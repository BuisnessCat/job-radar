# Dev log

My notes on building job-radar. The top part is how things are right now. Below that is
what happened day by day, the dumb stuff included. How to run the project is in
[README.md](README.md).

## What this is

A scraper for [junior.guru](https://junior.guru/jobs/praha/) job listings. It downloads
the listings page, pulls out the jobs with their tags, saves them to a json file and
loads them into Postgres. A small FastAPI app serves what's in the database: jobs with
paging and filters by city and tag, plus counts per tag.

## The pipeline

```
junior.guru
    |
    v
data/page.html      cached copy, so debugging doesn't hit the site every run
    |
    v
parse_jobs()        title, company, location, url, tags
    |
    v
data/jobs.json      full result, easy to eyeball
    |
    +---> load_jobs_to_db()    job table, skips urls that are already there
    +---> load_tags_to_db()    tag and job_tag tables
                 |
                 v
             Postgres    tables created by alembic, not by hand
                 |
                 v
             FastAPI     /jobs, /jobs/{id}, /stats/tags, /health
```

## Files

| File | What's in it |
|---|---|
| `main.py` | download, parse, save json, load into the database |
| `load.py` | everything that touches the database, all through the ORM now |
| `db.py` | SQLAlchemy engine and the `Session` factory |
| `models.py` | `Job`, `Tag`, `JobTag`, the tables described in Python |
| `schemas.py` | `JobOut`, what the api is allowed to send back |
| `app.py` | the FastAPI app |
| `alembic/` | migrations. `env.py` builds the connection string from `.env` itself |
| `README.md` | what the project is and how to run it, plus my docker/psql cheat sheet |
| `data/page.html`, `data/jobs.json` | generated, gitignored |
| `.env` | `DB_PASSWORD`, gitignored. `.env.example` is the template for it |

## Functions in main.py

| Function | What it does |
|---|---|
| `download_page(url, path)` | fetches the page, exits on a network error |
| `load_soup(path)` | reads the cached file into BeautifulSoup |
| `parse_text(job, selector)` | text of one element, `None` if it isn't there |
| `parse_url(job, selector)` | `href` of one element, `None` if it isn't there |
| `parse_tags(job, selector)` | list of tags from `data-jobs-tag` attributes |
| `parse_jobs(soup)` | walks the listings, returns a list of job dicts |
| `save_jobs(jobs, path)` | writes json |
| `read_jobs(path)` | reads json back, exits if the file is missing or broken |
| `count_tags(jobs)` | counts tags from the json. Nothing calls it anymore, see Sep 28 |

## Functions in load.py

| Function | What it does |
|---|---|
| `read_jobs_from_db(offset, limit, location, tag)` | one page of jobs, filters are optional |
| `read_job_from_db(job_id)` | one job, or `None` if there's no such id |
| `load_jobs_to_db(jobs)` | inserts jobs, skips the ones whose url is already in the table |
| `load_tags_to_db(jobs)` | creates tags that don't exist yet and links them to their jobs |
| `count_tags()` | tag name and number of jobs, counted and sorted by Postgres |

## Endpoints in app.py

| Route | Returns |
|---|---|
| `GET /health` | `{"status": "ok"}` |
| `GET /jobs` | 20 jobs by default. `offset`, `limit`, `location`, `tag` |
| `GET /jobs/{job_id}` | one job, 404 if it doesn't exist |
| `GET /stats/tags` | `[{"tag": ..., "count": ...}]` |

## The database

Postgres 18 in Docker, container `jobdb`, port 5433. Three tables:

- `job`: `id`, `title`, `company`, `url`, `location`, `created_at`, and `source_id`.
  `source_id` is the url again, with a unique constraint. It's how reruns know a job is
  already there.
- `tag`: `id` and a unique `name`.
- `job_tag`: `job_id` and `tag_id`, both foreign keys, together the primary key. One row
  means "this job has this tag".

Alembic also keeps its own little table, `alembic_version`, with the id of the last
migration that was applied.

## Why it's built this way

- **The page is cached in `data/page.html`.** Debugging shouldn't hammer someone else's
  site. The price is that the cache never expires and I have to delete it by hand.
- **Parsers return `None` instead of crashing.** The markup isn't the same on every card,
  and one weird card shouldn't kill the whole run. The Discord jobs (Oct 8) proved that
  right, even if the data they produce is still wrong.
- **`jobs.json` sits between parsing and the database.** I can look at what got parsed
  in one glance, and reload the database without scraping again.
- **The url is the dedup key.** It's the only stable id the site gives me. Back in the
  raw SQL days the database rejected duplicates itself with `ON CONFLICT DO NOTHING`.
  With the ORM, Python looks the url up first, and the unique constraint is the safety
  net.
- **Tags have their own table plus a link table**, not a text column with commas in it.
  A job has many tags and a tag has many jobs. This way "jobs with tag X" and "how many
  jobs per tag" are plain joins.
- **The schema lives in `models.py`, Alembic turns changes into migrations.** At first I
  wrote the table in psql and copied it into the model. Keeping two descriptions in sync
  by hand didn't last long.
- **`JobOut` decides what leaves the api.** Otherwise whatever the ORM object has goes
  out, `source_id` included.
- **`Session.begin()` for writing, plain `Session()` for reading.** `begin()` commits at
  the end of the block, or rolls back if something raises, so there's no commit to
  forget.
- **404s live in `app.py`, not in `load.py`.** The database functions return `None`, and
  the endpoint decides what that means over http.
- **The password is in `.env`.** It's gitignored, so nothing secret goes into the repo.
- **The container is on port 5433**, because a Postgres installed in Windows already
  holds 5432.
- **Generated files go in `data/`, code stays at the root.** No package layout, six
  modules don't need one.

---

# Log

## Aug 31

venv, `.gitignore`, deps.

- `requirements.txt` came out as UTF-16, because that's what PowerShell does with
  `pip freeze >`. `pip install -r` chokes on it. Took me a while to spot, the file looks
  completely normal in the editor. Rewrote it as UTF-8.

## Sep 1

Parser for title, company, location and link.

- `data["href"]` could blow up with a KeyError, even though there's a None check right
  above it. Switched to `.get("href")`.
- 8-space indents in `parse_jobs`. Keeps happening, it's a habit and not a typo.
  Should just install a formatter.

## Sep 4

Page caching, saving to json, reading it back, counting tags.

- `if __name__` had grown to 25 lines doing everything at once: download, catch errors,
  parse, write. Split it into `download_page`, `load_soup`, `save_jobs`.
- `"page.html"` was typed out in three places. Moved to constants.
- `main` saved the list to json and then read it straight back, while the same list was
  sitting in memory. Dropped that.
- `count_tech` wasn't counting tech. The tags mix languages, cities (`praha`, `brno`),
  contract type (`fulltime`) and job boards (`jobscz`, `linkedin`) — three of the top
  five aren't technologies. Renamed to `count_tags`.
- `if/else` counter became `tag_counts.get(tag, 0) + 1`.
- Returned a dict when what I needed was an order.

## Sep 8

Printing the top 10 tags.

- Because of the dict, slicing didn't work, so the printing came out clunky:
  `list(tag_counts.items())[:limit]`. The problem wasn't the printing, it was the
  useless `dict(...)` one level up. Dropped it and got `tag_counts[:TOP_TAGS]`.
- Also: trailing whitespace, blank lines between functions, quotes, `occured` typo.

## Sep 10

Postgres in Docker. Container `jobdb`, first version of the `job` table.

- Created the container without `-v name:path`, so the volume got a random name.

## Sep 11

Two Postgres servers on one port, then the loader.

- Couldn't connect. The error came back as mojibake, which decoded to a Russian
  "password authentication failed for user postgres". Two things followed from that:
  the connection was getting through, so Docker and the network were fine, and the
  server answering wasn't mine — the Docker image speaks English, so this was a Postgres
  installed straight into Windows, sitting on 5432 with a Russian locale.
- Confirmed it with `docker ps` and `services.msc` — the `postgresql-x64` service was
  running.
- Didn't uninstall anything, just moved the container to a free host port:
  `-p 5433:5432`. Left number is the port on my machine, right one is inside the
  container.
- Recreating the container wiped the volume, so the `job` table had to be created again.
  Added `source_id text not null unique` this time.
- Wrote `load.py`: `psycopg`, connection string with the password from `.env`,
  `INSERT ... ON CONFLICT (source_id) DO NOTHING`. 80 jobs in the table, and a second
  run adds nothing.
- Generated `requirements.txt` with `pip freeze >` again and got UTF-16 again. Same
  trap as Aug 31.

## Sep 13

FastAPI on top of the database: `/health` and `/jobs`.

- `/jobs` came back as arrays of values instead of objects. psycopg returns tuples by
  default; `cursor(row_factory=dict_row)` makes each row a dict keyed by column name, and
  then FastAPI serializes them as proper json objects.
- Kept `psycopg.connect` inside the function instead of opening one connection at module
  level. `with` closes the connection when the function returns, so a global one would be
  dead after the first request anyway — and a connection holds transaction state, so one
  failed query would poison every request after it.
- `uvicorn app:app` — the first `app` is the module (`app.py`), the second is the
  `app = FastAPI()` object inside it. Nothing magic, just `module:variable`.
- Pulled the connection string out into a `DSN` constant, both functions use it now.
- Checked it end to end: `/health` returns ok, `/jobs` returns the 81 rows in the table.

## Sep 14

SQLAlchemy for the writing side: `db.py` (engine + `sessionmaker`), `models.py` (the
`Job` model), `load_jobs_to_db` rewritten on the ORM.

- `Session()` vs `Session.begin()`. `Session()` just hands me a session — nothing is
  saved unless I call `session.commit()` myself, and leaving the `with` block only closes
  it. `Session.begin()` opens a transaction and commits it when the block exits cleanly,
  rolls back if something raises. Writing goes through `begin()` so there's no forgotten
  commit; plain `Session()` is enough for reading.
- `select(Job).where(...)` doesn't touch the database. It builds a `Select` object, which
  is a description of a query and nothing else. The database only sees it when a session
  runs it — `session.scalars(stmt)` or `session.execute(stmt)`. That's why a statement can
  sit in a variable and be reused.
- Who owns `scalar_one_or_none`: the result, not the session and not the statement.
  `session.execute(stmt)` returns a `Result`, and `Result` has `.scalar_one_or_none()`.
  `session.scalars(stmt)` returns a `ScalarResult`, already unwrapped to single values,
  and that one only has `.one_or_none()` — no `scalar_` prefix, because the unwrapping
  already happened. I'm using the second pair.
- `echo=True` on the engine prints every statement it sends. Handy while learning what
  the ORM actually does, noise once it works.
- Commented out the tag printing so the SQL log was readable.
- Moved `page.html` and `jobs.json` into `data/`. Two constants in `main.py`, nothing else
  refers to those paths. `.gitignore` didn't need touching — patterns without a slash
  match at any depth.

## Sep 19

Reading went through the ORM too. Added paging to `/jobs` and a new endpoint,
`/jobs/{id}`.

- `load.py` doesn't talk to the database in two different ways anymore, everything goes
  through the `Session`. Except I forgot the `DSN` constant and `load_dotenv()` at the
  top of the file. Nothing used them, and they sat there for another week.
- The question from Sep 13, a connection per request or a pool, more or less solved
  itself. The SQLAlchemy engine keeps a pool of connections on its own. No
  `psycopg_pool` needed.
- Paging is two query parameters, `offset` and `limit`, declared as `Query(ge=0)` and
  `Query(ge=1)`. I didn't write a single `if` for validation. `?limit=0` or `?offset=-5`
  gets a 422 from FastAPI, with an explanation of what's wrong. Default limit is 20.
- I was sure that returning ORM objects after the `with Session()` block is closed would
  blow up. It doesn't. The columns are already loaded and nothing is lazy, so the objects
  are fine without a session. It would break on a relationship, but I don't have any.
- The 404 for a missing job: in the first version `read_job_from_db` raised
  `HTTPException` itself. It worked, but now my database code knew about http. Didn't
  like it, moved it out on Sep 27.

## Sep 21

Alembic.

Until today the table was something I typed into psql by hand, and `models.py` copied
it. Every change had to be done twice, and I just hoped the two matched. Now it's the
other way around. I change the model, `alembic revision --autogenerate` writes the
migration, `alembic upgrade head` runs it.

- `alembic init alembic`, and the first problem right away: `alembic.ini` wants the
  database url as plain text, password included, and that file goes into git. Left the
  placeholder in there and built the url in `env.py` from `.env` instead. Which means the
  connection string now lives in two places, `db.py` and `env.py`. Not great, but it
  works.
- My first autogenerate came out empty. I hadn't set `target_metadata = Base.metadata` in
  `env.py`, so Alembic had nothing to compare the database against.
- Dropped the hand-made table so that the first migration ("initial") could create it
  from scratch. That lost the 80 rows, but after both migrations `main.py` put them back
  in a second, from the cached page. First time the cache paid off for real.
- Added `created_at`. It's `default=lambda: datetime.now(timezone.utc)`, and the lambda
  matters. Without it `datetime.now()` runs once, when the module is imported, and every
  row gets that same time.
- The migration for it says `nullable=False` and has no default on the database side. It
  only went through because the table was empty at that moment. With rows already in it,
  Postgres would refuse, because it has nothing to put into the new column for them. The
  `default=` in the model is Python-only, the database knows nothing about it.

## Sep 22

`schemas.py` with `JobOut`, a Pydantic model for what the api sends back, and
`response_model=` on both job endpoints.

- Before this, FastAPI turned `Job` objects into json however it could, and `source_id`
  went out with everything else. Now only the fields in `JobOut` leave, and `/docs` shows
  what the response looks like.
- Short day.

## Sep 25

Location filter, `/jobs?location=praha`.

- `.title()` on the input, so `praha`, `PRAHA` and `Praha` all work. The site writes
  cities with a capital letter.
- First version had a whitelist, `ALLOWED_LOCATIONS = {"Praha", "Brno"}`, and a 400 for
  anything else. Seemed like good validation at the time.
- Committed it with a bug. I built the filtered query in one line and threw it away on
  the next if there was no location. But `location.title()` ran in that first line no
  matter what, so a plain `/jobs` without a filter did `None.title()` and fell over with
  a 500. Didn't notice, because I was only testing the filter.

## Sep 27

Tags in the database. Two new tables, `tag` and `job_tag`.

- It's many-to-many: a job has many tags, a tag belongs to many jobs. `job_tag` is just
  two columns, and the pair of them is the primary key, so the same link can't be added
  twice.
- There are two migrations called "add tag tables" now, four minutes apart. I generated
  the first one before I'd put `ForeignKey(...)` in the model, so it made the tables with
  no links between them. Added the foreign keys, ran autogenerate again, got a second
  migration with just those. The first one was already applied, so I left both. Lesson:
  read the generated file before running `upgrade`.
- The second migration creates the foreign keys without names (`None`), and Alembic left
  a warning right in the file: its `downgrade` won't work. Haven't fixed that.
- `load_tags_to_db` goes through `jobs.json` again, finds each job by its url, and for
  every tag: find it or create it, then link it to the job if it isn't linked yet.
- `session.flush()` after adding a new tag. It sends the INSERT to the database without
  committing, just so `tag.id` gets a value that I can use for the link right away.
- With `echo=True` you can watch how many queries that is. A few hundred for 80 jobs.
  Fine for now, not fine for 10 000 jobs.
- Found the Sep 25 bug while I was in `read_jobs_from_db` anyway. Rewrote it as a normal
  `if location is not None:`.
- And dropped the whitelist. I finally looked at what locations are actually in the
  data, and there are about twenty: Ostrava, Plzeň, "Vimperk (České Budějovice)"... A
  set of two cities was just wrong. The set itself is still sitting in `load.py`, unused.
- Moved the 404 out of `load.py` into the endpoint, like I wanted on Sep 19.
  `read_job_from_db` returns `None`, and `app.py` decides that's a 404.
- Cleaned the leftovers from the psycopg days out of `load.py`. And somehow picked up a
  new one: `from ast import stmt` at the very top. VS Code auto-imported it while I was
  typing `stmt`.

## Sep 28

Filter by tag and tag stats.

- `/jobs?tag=python` is a join from `job` through `job_tag` to `tag`, then a `where` on
  the tag name. Tags on the site are all lowercase, so I lowercase the input and that's
  it.
- I wrote `.offset().limit()` first and the joins after it, then got worried the limit
  would be applied before the filter. It isn't. Same thing as Sep 14: `select()` only
  describes the query, and SQLAlchemy puts `LIMIT` and `OFFSET` at the end of the SQL no
  matter what order I call the methods in. Checked it in the `echo` output to be sure.
- `/stats/tags` is `func.count` with `group_by` on the tag name. Postgres does the
  counting now. This used to be `count_tags` in `main.py`, counting the json in Python.
  So now there are two functions called `count_tags`, and the old one isn't called by
  anything.
- The stats come back unsorted. Forgot `order_by`.

## Oct 8

README day. The old README was really just my docker and psql notes. Rewrote it for
someone who has never seen the project: what it is, why, how to run it from zero, and an
example request with the response. My notes stayed at the bottom as a cheat sheet.

- Added `description=` to every endpoint and to the query parameters. `/docs` actually
  explains things now, instead of just listing names.
- Walked through the README as if I'd just cloned the repo, and it broke on step 6.
  `data/` is gitignored, so it doesn't exist in a fresh clone, and `main.py` can't write
  `data/page.html` into a folder that isn't there. One line,
  `os.makedirs(..., exist_ok=True)`.
- Added `.env.example`. Without it a new person has no way to know `.env` should exist,
  or what goes in it.
- Pinned `docker run` to `postgres:18`. Plain `postgres` is whatever the latest version
  is, and the volume path in my command is the one that works for 18.
- Funny thing: after all the fuss on Aug 31, the current pip (26) reads the UTF-16
  `requirements.txt` without complaining. Still want it in UTF-8, other tools aren't that
  forgiving.
- While writing the "what doesn't work" part of the README, I went through the data and
  found the Discord jobs. People share jobs on the junior.guru Discord, and the site shows
  those with a different card. Where the company and the city would be, there's
  "Děkujeme H.J. za sdílení!", "thanks H.J. for sharing". My parser takes the first
  `span` as the location, so that's what the location becomes (`DěkujemeH.J.za
  sdílení!`, without the spaces even), and the company is `None`. Five jobs like that,
  plus one LinkedIn job with no location at all.
- And that breaks the api. `JobOut` says `company: str`, so FastAPI refuses to send a job
  without a company and the whole request ends in a 500. The default first page happens
  to be fine, `/jobs?limit=100` isn't.

## Oct 10

Sick, so just something small: `/stats/tags` is sorted now, most common tag first.

- `order_by(job_count.desc(), Tag.name)`. Postgres sorts by the count, biggest first, and
  tags with the same count go alphabetically. Without the second part their order could
  change from one request to the next.
- Put `func.count(JobTag.job_id)` into a variable, `job_count`, because it's needed twice
  now, in `select` and in `order_by`. It doesn't run anything, it's just a piece of the
  query, same as `select()` itself (Sep 14).
- The sorted list made the Sep 4 thing obvious again: the top three are `fulltime`,
  `jobscz` and `database`. `python` is sixth.

## TODO

- `/jobs` 500s on jobs with no company or location. Either `str | None` in `JobOut`, or
  teach the parser about the Discord cards, or both.
- The Discord cards in general. The parser should at least not put "thanks for sharing"
  into the location.
- `model_config` in `schemas.py` sits outside the class, so it does nothing. It only works
  because FastAPI reads the attributes by itself.
- No `order_by` in `/jobs`. Paging without an order isn't guaranteed to be stable.
- The connection string is in two places, `db.py` and `alembic/env.py`, and everything
  except the password is hardcoded.
- The last migration can't be downgraded, the foreign keys have no names.
- `created_at` is `DateTime` without a timezone, but I write UTC into it. Should be
  `DateTime(timezone=True)`.
- `load_tags_to_db` does a query per tag.
- `jobs.json` gets read twice, right after being written, while the same list is in
  memory.
- Dead code: `ALLOWED_LOCATIONS`, `from ast import stmt`, the old `count_tags` and the
  commented-out printing in `main.py`.
- `echo=True` is still on.
- `requirements.txt` is still UTF-16.
- The cache never refreshes. Needs a max age or a `--refresh` flag.
- Mixed link formats: some relative (`/jobs/...`), some absolute. `urllib.parse.urljoin`.
- If the site's markup changes, the parser returns 0 jobs and reports success.
- No tests. The parser is a good place to start: give it a saved page, check what comes
  out. The Discord cards would be the first test case.
