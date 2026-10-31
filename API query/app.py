from datetime import datetime

from flask import Flask, jsonify, request

import db
from db import GroupBy, Period, SightingFilter

app = Flask(__name__)


@app.errorhandler(ValueError)
def bad_request(err):
    return jsonify({"error": str(err)}), 400

def parse_date(text, is_end=False):
    try:
        d = datetime.fromisoformat(text)
    except ValueError:
        raise ValueError(f"invalid data 'text', use YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS")
    if is_end and len(text) == 10:
        d = d.replace(hour=23, minute=59, second=59)
    return d

def parse_enum(enum_cls, text, default):
    try:
        return enum_cls(text or default)
    except ValueError:
        allowed = ", ".join(e.value for e in enum_cls)
        raise ValueError(f"invalid value '{text}', allowed: {allowed}")


def build_filter():
    args = request.args
    try:
        limit = int(args.get("limit", 100))
        offset = int(args.get("offset",0))
    except ValueError:
        raise ValueError("limit and offset must be whole numbers")
    return SightingFilter(
        location=args.get("location"),
        species=args.get("species"),
        start=parse_date(args["from"]) if args.get("from") else None,
        end=parse_date(args["to"], is_end=True) if args.get("to") else None,
        limit=max(1, min(limit, 1000)),
        offset=max(0, offset),
    )

@app.route("/sightings")
def list_sightings():
    return jsonify(db.get_sightings(build_filter()))

@app.route("/sightings/<sighting_id>")
def one_sighting(sighting_id):
    row = db.get_sighting_by_id(sighting_id)
    if row  is None:
        return jsonify({"error": "Sighting not found"}), 404
    return jsonify(row)

@app.route("/summary")
def summary():
    group_by = parse_enum(GroupBy, request.args.get("group_by"), "location")
    return jsonify(db.get_summary(build_filter(), group_by))

@app.route("/trends")
def trends():
    period = parse_enum(Period, request.args.get("period"), "month")
    return jsonify(db.get_trends(build_filter(), period))
@app.route("/seasonal")
def seasonal():
    period = parse_enum(Period, request.args.get("period"), "month")
    return jsonify(db.get_seasonal_average(build_filter(), period))
if __name__ == "__main__":
    app.run(debug=True)