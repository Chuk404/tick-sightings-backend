# Tick Sightings Backend

A backend MVP for Elanco's tick sighting task. It has two applications that
share a MySQL database:

- **data_cleaner**: fetches sightings from Elanco's API, cleans them and loads
  them into MySQL. Safe to run more than once.
- **API query**: a small Flask API that reads from MySQL to search, filter and
  summarise the sightings.

The design write-up is in `docs/Tick Design.docx`.

## Requirements

- Python 3.10 or newer
- MySQL 8


## Setup

1. **Create the database and tables.** Open `data_cleaner/sighting_species.sql`
   in MySQL Workbench and run it (the lightning-bolt button). It creates a
   database called `elanco` with the `species` and `sightings` tables.

2. **Add your database settings.** Copy `.env.example` to a file named `.env`
   inside **both** the `data_cleaner` and `API query` folders, then fill in your
   own MySQL details. Set `DB_NAME` to `elanco`.

3. **Install the dependencies** (one per app), from the project's main folder:
   ```
   py -m pip install -r data_cleaner/requirements.txt
   py -m pip install -r "API query/requirements.txt"
   ```

## Run 

1. **Load the data** (run first):
   ```
   py data_cleaner/Scanning.py
   ```
   You should see `Fetched 1000 records`, `1000 kept, 0 rejected` and
   `Loaded 1000 sightings`. Running it again leaves the count at 1000. If
   Elanco's API replies "rate limit exceeded", the script waits and retries.


2. **Start the API:**
      ```
   cd "API query"
   py app.py
   ```
   It runs at http://127.0.0.1:5000


## Endpoints

| Endpoint | What it does | Options |
|---|---|---|
| `/sightings` | Search and filter sightings. Returns the matching sightings plus the total number of matches. | `from`, `to`, `location`, `species`, `limit` (default 100, max 1000), `offset` (default 0) |
| `/sightings/<id>` | One sighting by its ID. Returns an error message if the ID doesn't exist. | none |
| `/summary` | Number of sightings per location, or per species. | `group_by=location` (default) or `group_by=species`, plus the filters below |
| `/trends` | Number of sightings over time, by month or by week. | `period=month` (default) or `period=week`, plus the filters below |
| `/seasonal` | Average number of sightings in each calendar month (or week of the year) across all the years in the data. | `period=month` (default) or `period=week`, plus the filters below |


Examples:

- http://127.0.0.1:5000/sightings?location=London&limit=5
- http://127.0.0.1:5000/sightings?from=2020-01-01&to=2020-12-31&limit=3
- http://127.0.0.1:5000/sightings/02WNholuSg6ndCk4c1dA
- http://127.0.0.1:5000/summary?group_by=species
- http://127.0.0.1:5000/trends?period=month&location=Liverpool
- http://127.0.0.1:5000/seasonal?period=month

The filters `from`, `to`, `location` and `species` work on `/summary`,
`/trends` and `/seasonal` as well.

The filters `from`, `to`, `location` and `species` work on `/summary`, `/trends` and `/seasonal` as well.

## Notes
- Flask's built-in server is for development only. A production setup would use
  a proper web server.
- Credentials live in `.env`, which is not committed.