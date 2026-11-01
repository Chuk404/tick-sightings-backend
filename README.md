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
- MySQL 8 (https://dev.mysql.com/downloads/installer/)
**Connect MySQL Workbench to your MySQL server.**
**Go to MYSQL Workbench to your MYSQL server.** click the **+** next to "MYSQL Connections" and
fill in: connection name and press ok 


## Setup

1. **Create the database and tables.** Open `data_cleaner/sighting_species.sql`
   in MySQL Workbench and run it (the lightning-bolt button). It creates a
   database called `elanco` with the `species` and `sightings` tables. and refresh your schemas

2. 2. **Add your database settings.** Rename `.env.example` to `.env` and fill in
   your own MySQL details (the username and password you use in Workbench).
   Leave `DB_NAME` as `elanco`. Then copy this `.env` file into **both** the
   `data_cleaner` and `API query` folders.

3. 3. **Install the dependencies.** In File Explorer, right-click the project
   folder (the one that contains `README.md`) and choose **Copy as path**.
   In your terminal, type `cd ` and paste the path, then press Enter. Then run:
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


2. **Start the API** (from the main folder):
   ```
   cd "API query"
   py app.py
   ```
   The terminal will show the address, normally http://127.0.0.1:5000. Open
   it in your browser, using the example links below.


## Endpoints

| Endpoint | What it does | Options |
|---|---|---|
| `/sightings` | Search and filter sightings. Returns the matching sightings plus the total number of matches. | `from`, `to`, `location`, `species`, `limit` (default 100, max 1000), `offset` (default 0) |
| `/sightings/<id>` | One sighting by its ID. Returns an error message if the ID doesn't exist. | none |
| `/summary` | Number of sightings per location, per species, or per UK region. | `group_by=location` (default), `group_by=species` or `group_by=region`, plus the filters below |
| `/trends` | Number of sightings over time, by month or by week. | `period=month` (default) or `period=week`, plus the filters below |
| `/seasonal` | Average number of sightings in each calendar month (or week of the year) across all the years in the data. | `period=month` (default) or `period=week`, plus the filters below |

The filters `from`, `to`, `location` and `species` work on `/summary`,
`/trends` and `/seasonal` as well.

Examples:

- http://127.0.0.1:5000/summary?group_by=region
- http://127.0.0.1:5000/sightings?location=London&limit=5
- http://127.0.0.1:5000/sightings?from=2020-01-01&to=2020-12-31&limit=3
- http://127.0.0.1:5000/sightings/02WNholuSg6ndCk4c1dA
- http://127.0.0.1:5000/summary?group_by=species
- http://127.0.0.1:5000/trends?period=month&location=Liverpool
- http://127.0.0.1:5000/seasonal?period=month

The filters `from`, `to`, `location` and `species` work on `/summary`,
`/trends` and `/seasonal` as well.

## Notes
- Flask's built-in server is for development only. A production setup would use
  a proper web server.
- Credentials live in `.env`, which is not committed.

## Running the data_cleaner on a schedule

The data_cleaner is designed to run once a day. Sightings arrive in batches and
Elanco's API is rate-limited, so running it more often adds little. Running it
again is always safe: sightings are updated by ID, so nothing is duplicated.

It doesn't schedule itself. Use your computer's scheduler to run it:

- **Windows** (Task Scheduler). This creates a task that runs every day at 3am
  (replace the path with where you saved the project):
  ```
  schtasks /Create /SC DAILY /ST 03:00 /TN "TickDataCleaner" /TR "py \"C:\path\to\data_cleaner\Scanning.py\""
  ```
- **Mac or Linux** (cron). Add this line with `crontab -e`:
  ```
  0 3 * * * python3 /path/to/data_cleaner/Scanning.py
  ```

If a run fails (for example, Elanco's API is down), it logs the error and stops
without changing the database, and the API keeps serving the last good data.
The next scheduled run tries again.

## Project outline and design choices

**Outline.** Two applications share a MySQL database. The `data_cleaner`
fetches Elanco's tick sighting data, cleans it and loads it. A separate Flask
API reads from the database to search, filter and summarise the sightings.
The full write-up, with screenshots, is in `Tick Design.docx`.

**Choices**
- **Two apps, one database.** If Elanco's API goes down or rate-limits me, only
  the data_cleaner fails and the API keeps serving the last good data.
- **Python, Flask and MySQL.** The data is small and relational, and a
  lightweight framework left the time for data handling.
- **Schema in 3NF.** Sightings are keyed on the API's ID; species (with its
  Latin name) is its own table. Indexes on date and on location plus date
  support the filters.
- **Duplicates and missing data.** The ID is the identity of a sighting, so
  re-running never duplicates. Records missing a required field or with an
  invalid date are rejected and counted. I don't fill in default values,
  because a made-up location would distort the counts.
- **Failure handling.** Failed or malformed responses are retried with a
  growing delay, and a rate limit makes it wait a minute. After four attempts it
  stops cleanly.
- **Safe API.** Filters live in one class, user input only goes in as query
  parameters, and fixed choices (`group_by`, `period`) are Enums.
- **Regions.** The data only has cities, so a fixed lookup in the code groups
  them into UK regions.

**With more time:** run the data_cleaner on a scheduler and check the stats
endpoint first, move regions into a `locations` table, add a fallback duplicate
rule, validate cities against the database, and add the AI/ML insights.

## Use of AI

I used AI tools for code suggestions and debugging help. The design decisions, the data checks and the testing were mine.