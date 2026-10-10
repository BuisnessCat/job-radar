# job-radar

A practice project of mine. It scrapes junior IT job listings from
[junior.guru](https://junior.guru/jobs/praha/), puts them into Postgres and serves them
through a small FastAPI app. So you can ask things like "Python jobs in Prague" or "which
tags show up the most" and get an answer in one request.

## Why

junior.guru is a great site, but it's one long page you scroll through. I wanted the same
jobs in a database where I can filter them and count things.

The other reason is that I'm learning backend development, and I wanted one project that
touches everything at once: scraping, SQL, migrations, an API. I wrote down every step as
I went, mistakes included, in [dev_log.md](dev_log.md).

## How it works

```
junior.guru  --->  main.py  --->  Postgres  --->  app.py (FastAPI)
                      |
                      +--> data/page.html    the downloaded page
                      +--> data/jobs.json    what the parser found
```

`main.py` downloads the listings page once and keeps it in `data/page.html`, so I'm not
hitting the site every time I run it. Then it pulls out the jobs (title, company,
location, link, tags), saves them to `data/jobs.json` and loads them into the database.

`app.py` only reads from the database. It doesn't know the scraper exists.

The rest of the files: `load.py` is everything that talks to the database, `models.py`
describes the tables, `schemas.py` is what the API sends back, and `alembic/` has the
migrations.

## Running it locally

You'll need Python 3.10 or newer (I use 3.11), Docker and git. I work on Windows, but
apart from activating the venv everything is the same on macOS and Linux.

**1. Clone the repo**

```bash
git clone https://github.com/BuisnessCat/job-radar.git
cd job-radar
```

**2. Make a virtual environment and install the dependencies**

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

On macOS or Linux the second line is `source .venv/bin/activate`.

**3. Start Postgres in Docker**

```bash
docker run -d --name jobdb -e POSTGRES_PASSWORD=secret -p 5433:5432 -v jobdb-data:/var/lib/postgresql postgres:18
```

Note the port, it's 5433 and not the usual 5432. I have another Postgres installed
straight into Windows that sits on 5432, and the two kept getting mixed up (that story is
in the dev log, Sep 11).

It needs a few seconds to start. If you're not sure it's up, `docker logs jobdb` should
end with "database system is ready to accept connections".

**4. Create `.env`**

```bash
cp .env.example .env
```

There's only the database password in it, and it already matches the one from
`docker run`. If you changed it there, change it here too. Host, port and user are
hardcoded in `db.py` and `alembic/env.py` (yes, I know).

**5. Create the tables**

```bash
alembic upgrade head
```

**6. Run the scraper**

```bash
python main.py
```

It prints a wall of SQL (I left `echo=True` on in `db.py` while learning SQLAlchemy) and
ends with something like `Saved 80 jobs to data/jobs.json.`

You can run it as many times as you want, nothing gets duplicated. But it reuses the
saved page, so for fresh jobs delete `data/page.html` first.

**7. Start the API**

```bash
uvicorn app:app --reload
```

Now open <http://127.0.0.1:8000/docs>. It lists every endpoint and lets you call them
right from the browser, which is the easiest way to poke around. If port 8000 is busy,
add `--port 8001`.

## The API

| Endpoint | What you get |
|---|---|
| `GET /health` | `{"status": "ok"}` if the server is running |
| `GET /jobs` | jobs, 20 at a time |
| `GET /jobs/{id}` | one job, or a 404 |
| `GET /stats/tags` | how many jobs have each tag |

`/jobs` takes a few optional parameters, and you can combine them:

- `offset` and `limit` for paging. `?offset=20&limit=20` is the second page.
- `location` is a city: `praha`, `brno`. Case doesn't matter, but it has to match the
  whole location, so `brno` won't find "Brno, Prostějov (Olomouc)".
- `tag` is `python`, `react`, `testing` and so on. The full list is in `/stats/tags`.

For example, the first two Python jobs in Prague:

```bash
curl "http://127.0.0.1:8000/jobs?location=praha&tag=python&limit=2"
```

```json
[
  {
    "id": 2,
    "title": "Specialista/ka v oblasti datové infrastruktury a služeb (Life Sciences)",
    "company": "Ústav molekulární genetiky AV ČR, v.v.i.",
    "url": "https://www.jobs.cz/rpd/2001345737/?utm_source=juniorguru",
    "location": "Praha",
    "created_at": "2026-09-28T16:35:12.418903"
  },
  {
    "id": 8,
    "title": "Data Scientist",
    "company": "PŘEDVÝBĚR.CZ a.s.",
    "url": "https://www.jobs.cz/rpd/2001371969/?utm_source=juniorguru",
    "location": "Praha",
    "created_at": "2026-09-28T16:35:12.421337"
  }
]
```

And the tag stats, most common first, cut short:

```json
[
  {"tag": "fulltime", "count": 73},
  {"tag": "jobscz", "count": 49},
  {"tag": "database", "count": 46},
  ...
]
```

Yes, the top ones aren't technologies. The site's tags mix skills with cities, contract
types and job boards. `python` is in sixth place with 32.

Your ids, dates and numbers will be different, it depends on when you ran the scraper.

On Windows, `curl` in PowerShell isn't the real curl, it's an alias for
`Invoke-WebRequest`. Type `curl.exe` instead, or just open the link in a browser.

## What doesn't work yet

- Only one page gets scraped, `/jobs/praha/`. It does have jobs from other cities too.
- Jobs that people share on the junior.guru Discord have a different card layout, and the
  parser gets them wrong. The company comes out empty, and the location turns into
  `DěkujemeH.J.za sdílení!` ("thanks H.J. for sharing", with the spaces lost on top).
  Worse, `/jobs` returns a 500 for any page that contains one of them.
- The saved page never expires, you have to delete it by hand.
- Some job links are relative (`/jobs/...` on junior.guru), others go to other sites.
- No tests yet.

---

# Postgres cheat sheet

My own notes, mostly so I don't have to google the same docker and psql commands every
time. All of it is about the `jobdb` container from step 3.

## The container

```bash
docker ps                  # what's running
docker ps -a               # everything, including stopped
docker start jobdb         # after a reboot it's stopped, start it again
docker stop jobdb
docker logs jobdb          # look here first when it won't connect
```

What the `docker run` flags mean: `-d` runs it in the background, `-p 5433:5432` maps
port 5432 inside the container to 5433 on my machine, and `-v jobdb-data:...` keeps the
data in a named volume, so it survives deleting the container.

Starting over with an empty database (careful, `docker volume rm` deletes the data for
good):

```bash
docker stop jobdb
docker rm jobdb
docker volume rm jobdb-data
```

Then steps 3, 5 and 6 again.

## Getting into psql

```bash
docker exec -it jobdb psql -U postgres
```

Or a single query without opening the console:

```bash
docker exec jobdb psql -U postgres -c "select count(*) from job;"
```

## psql commands

```
\l            list databases
\c dbname     switch to another database
\dt           list tables
\d job        structure of the job table
\di           indexes
\du           users
\x            print rows as columns — handy for wide tables
\timing       show how long queries take
\copy job to 'jobs.csv' csv header    export a table to csv
\?            all psql commands
\h SELECT     help on a SQL command
\q            quit
```

If the output doesn't fit the screen, scroll with the arrow keys and press `q` to leave
the pager.

## Tables

There are three. `job` holds the jobs: `id`, `title`, `company`, `url`, `location`,
`created_at`, and `source_id`, which is the job's url again with a unique constraint, so
the same job can't get in twice. `tag` is just `id` and `name`. `job_tag` connects the
two, one row per "this job has this tag".

I don't create or change tables by hand anymore. I change `models.py`, then:

```bash
alembic revision --autogenerate -m "what changed"
alembic upgrade head
```

Queries I keep coming back to:

```sql
select * from job limit 5;
select count(*) from job;
select * from job where location = 'Praha';
select company, count(*) from job group by company order by count(*) desc;

-- top 10 tags
select t.name, count(*) from tag t
join job_tag jt on jt.tag_id = t.id
group by t.name order by count(*) desc limit 10;

-- jobs with a given tag
select j.title, j.company from job j
join job_tag jt on jt.job_id = j.id
join tag t on t.id = jt.tag_id
where t.name = 'python';

-- empty all three tables and reset the ids
truncate job, tag, job_tag restart identity;
```

## When something breaks

- `Cannot connect to the Docker daemon`: Docker Desktop isn't running.
- `No such container: jobdb`: the container doesn't exist yet, see step 3.
- `port is already allocated`: something else took 5433. You can publish a different
  port, but then change it in `db.py` and `alembic/env.py` as well.
- `connection refused` from `alembic` or `/jobs`: the container is stopped,
  `docker start jobdb`.
- `password authentication failed`: the password in `.env` doesn't match the one the
  container was created with.
- `relation "job" does not exist`: the tables were never created, run
  `alembic upgrade head`.
- The error message comes back as mojibake: that's the Windows Postgres answering, not
  the container. Check the port.
- `the input device is not a TTY`: you forgot `-it` on `docker exec`.
- psql hangs and the prompt says `postgres-#`: it's waiting for a `;`.
