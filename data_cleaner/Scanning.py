import requests
from collections import Counter
import json
import time 
import logging
from datetime import datetime
import os
import mysql.connector
from dotenv import load_dotenv
load_dotenv()

URL = "https://dev-task.elancoapps.com/data/tick-sightings"
MAX_RETRIES = 4

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("ingest")


def fetch_sightings():
    delay = 5 
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            resp = requests.get(URL, headers = {"accept":"application/json"}, timeout=10)

            if resp.status_code == 200:
                data = resp.json()
                log.info("Fetched %d records", len(data))
                return data

            if resp.status_code == 429:
                wait = 60
            elif resp.status_code >= 500:
                wait = delay
            else:
                log.error("Status %s, not retrying", resp.status_code)
                return None
            log.warning("Attempt %d: status %s, retrying in %ds", attempt, resp.status_code, wait)

        except (requests.RequestException, ValueError) as exc:
            wait = delay
            log.warning("Attempt %d failed: %s, retrying in %ds",attempt,exc,wait)

        if attempt < MAX_RETRIES:
            time.sleep(wait)
            delay *= 2

    log.error("Giving up after %d attempts", MAX_RETRIES)
    return None

def parse_date(text):
    try:
        return datetime.fromisoformat(text)
    except ValueError:
        return None

REQUIRED = ["id","date","location","species","latinName"]
 
def clean_record(rec):

    for field in REQUIRED:
        value = rec.get(field)
        if value is None or str(value).strip() == "":
            return None
    
    sighted_at = parse_date(rec["date"].strip())
    if sighted_at is None:
        return None 

    return {
        "id": rec["id"].strip(),
        "sighted_at": sighted_at,
        "location": rec["location"].strip(),
        "species": rec["species"].strip(),
        "latin_name": rec["latinName"].strip()
    }

data = fetch_sightings()
if data is None:
    raise SystemExit("Fetch failed")
    

kept, rejected = [], 0
for rec in data:
    cleaned = clean_record(rec)
    if cleaned is None:
        rejected += 1
    else:
        kept.append(cleaned)

print(len(kept), "kept,", rejected, "rejected")

            
conn = mysql.connector.connect(
    host=os.environ["DB_HOST"],
    user=os.environ["DB_USER"],
    password=os.environ["DB_PASSWORD"],
    database=os.environ["DB_NAME"],
)

cur = conn.cursor()

# loading in species first
species = {(r["species"], r["latin_name"]) for r in kept}
cur.executemany(
    "INSERT IGNORE INTO species (name, latin_name) VALUES (%s, %s)",
    list(species),
)

# sighted inserted second 
cur.executemany(
    """INSERT INTO sightings (id, sighted_at, location, species)
       VALUES (%s, %s, %s, %s)
       ON DUPLICATE KEY UPDATE
         sighted_at = VALUES(sighted_at),
         location = VALUES(location),
         species = VALUES(species)""",
       [(r["id"], r["sighted_at"], r["location"], r["species"]) for r in kept],
)

conn.commit()
cur.close()
conn.close()
print("Loaded", len(kept), "sightings")


