import os 
from dataclasses import dataclass
from enum import Enum
from typing import Optional
from pathlib import Path
import mysql.connector
from dotenv import load_dotenv

env_path = Path(__file__).parent / ".env"
load_dotenv(env_path)
class GroupBy(Enum):
    LOCATION = "location"
    SPECIES = "species"

class Period(Enum):
    WEEK = "week"
    MONTH = "month"

PERIOD_FORMAT = {Period.WEEK: "%x-W%v", Period.MONTH: "%Y-%m"}
SEASON_EXPR = {Period.WEEK: "WEEK(sighted_at, 3)", Period.MONTH: "MONTH(sighted_at)"}

def get_seasonal_average(f, period):
    where, params = build_where(f)
    span = run_query(
        f"SELECT MIN(YEAR(sighted_at)) AS first_year, MAX(YEAR(sighted_at)) AS last_year "
        f"FROM sightings{where}",
        params,
    )[0]
    if span["first_year"] is None:
        return {"years_covered": 0, "result": []}
    years = span["last_year"] - span["first_year"] + 1

    expr = SEASON_EXPR[period]
    rows = run_query(
        f"SELECT {expr} AS period_number, COUNT(*) AS total "
        f"FROM sightings{where} GROUP BY period_number ORDER BY period_number",
        params,
    )
    for r in rows:
        r["average"] = round(r["total"]/ years,1)
    return {"years_covered": years, "results":rows}
@dataclass
class SightingFilter:
    location: Optional[str] = None
    species: Optional[str] = None
    start: Optional[datetime] = None
    end: Optional[datetime] = None
    limit: int = 100
    offset: int = 0

def get_conn():
    return mysql.connector.connect(
        host=os.environ["DB_HOST"],
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
        database=os.environ["DB_NAME"],
    )

def run_query(sql, params):
    conn = get_conn()
    cur = conn.cursor(dictionary=True)
    cur.execute(sql, params)
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows

def build_where(f):
    clauses, params = [], []
    if f.location:
        clauses.append("location = %s")
        params.append(f.location)
    if f.species:
        clauses.append("species = %s")
        params.append(f.species)
    if f.start:
        clauses.append("sighted_at >= %s")
        params.append(f.start)
    if f.end: 
        clauses.append("sighted_at <= %s")
        params.append(f.end)
    where = " WHERE " + " AND ".join(clauses) if clauses else ""
    return where,params

def get_sightings(f):
    where, params = build_where(f)
    total = run_query(f"SELECT COUNT(*) AS n FROM sightings{where}", params)[0]["n"]
    rows = run_query(
        f"SELECT id, sighted_at, location, species FROM sightings{where} "
        "ORDER BY sighted_at LIMIT %s OFFSET %s",
        params + [f.limit, f.offset],
    )
    for r in rows:
        r["sighted_at"] = r["sighted_at"].isoformat()
    return {"total": total, "results": rows}

def get_sighting_by_id(sighting_id):
    rows = run_query(
        "SELECT id, sighted_at, location, species FROM sightings WHERE id = %s",
        [sighting_id]
    )
    if not rows:
        return None
    rows[0]["sighted_at"] = rows[0]["sighted_at"].isoformat()
    return rows[0]

def get_summary(f, group_by):
    where, params = build_where(f)
    col = group_by.value
    return run_query(
        f"SELECT {col} AS name, COUNT(*) AS sightings FROM sightings {where}"
        f"GROUP BY {col} ORDER BY sightings DESC",
        params,
    )

def get_trends(f, period):
    where, params = build_where(f)
    return run_query(
        f"SELECT DATE_FORMAT(sighted_at, %s) AS period, COUNT(*) AS sightings "
        f"FROM sightings{where} GROUP BY period ORDER BY period",
        [PERIOD_FORMAT[period]] + params,
    )
    average = sum(r["sightings"] for r in rows) / len(rows) if rows else 0
    return {"average_per_period": round(average, 1), "results": rows}