# Dev log

## What this is

A scraper for [junior.guru](https://junior.guru/jobs/praha/) job listings. It downloads
the listings page, pulls out the jobs, saves them to a json file, loads them into
Postgres, and prints the most common tags.

## The pipeline

```
junior.guru
    |
    v
page.html      cached copy, so debugging doesn't hit the site every run
    |
    v
parse_jobs()   title, company, location, url, tags
    |
    +---> jobs.json          full result, easy to eyeball
    |         |
    |         v
    |     load_jobs_to_db()  insert into Postgres, skip what's already there
    |
    +---> count_tags()  ---> top 10 printed to the console
```

## Files

| File | What's in it |
|---|---|
| `main.py` | download, parse, save json, count tags, print |
| `load.py` | insert rows into Postgres |
| `README.md` | docker and psql commands for the database |
| `page.html` | cached page, gitignored |
| `jobs.json` | parse result, gitignored |
| `.env` | `DB_PASSWORD`, gitignored |

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
| `count_tags(jobs)` | counts tags, returns pairs sorted by count |

`load.py` has one function, `load_jobs_to_db(jobs)`.

## The database

Postgres 18 in Docker, container `jobdb`, port 5433. Table `job`:

| Column | Type | Note |
|---|---|---|
| `id` | integer | primary key, auto |
| `title` | text | |
| `company` | text | |
| `url` | text | |
| `location` | text | |
| `source_id` | text | not null, unique — dedup key, holds the url |

Tags aren't in the table yet, they only exist in the json.

## Why it's built this way

| Decision | Reason |
|---|---|
| Cache the page in `page.html` | Debugging shouldn't hammer someone else's site. Downside: the cache never expires, so fresh data needs the file deleted. |
| Parsers return `None` instead of crashing | The markup isn't uniform — a missing field shouldn't kill the whole run. |
| `jobs.json` sits between parsing and the database | The data is readable in one glance, and the db load can be rerun without scraping again. |
| `source_id` is the url, with a `UNIQUE` constraint | Reruns must not duplicate rows, and the url is the only stable id the site gives me. |
| `ON CONFLICT (source_id) DO NOTHING` | The database rejects the duplicate itself, so Python doesn't have to check first. |
| Password in `.env`, not in the code | `.env` is gitignored, so nothing secret goes into the repo. |
| Container on port 5433 | Port 5432 is taken by a Postgres installed in Windows. |
| `count_tags` returns a list, not a dict | What's needed is the order, and a list can be sliced for the top 10. |
| Counting with `dict.get(tag, 0) + 1` | The first time a tag shows up stops being a special case. |

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

## TODO

- `python-dotenv` is missing from `requirements.txt` — a fresh clone would fail on the
  import. And the file is UTF-16 again.
- No tags in the database, they live only in the json.
- Cache never refreshes — needs a max age or a `--refresh` flag.
- Mixed link formats: some relative (`/jobs/...`), some absolute. `urllib.parse.urljoin`.
- If the site's markup changes, the parser returns 0 jobs and reports success.
- `read_jobs` is called on a file that was just written from memory a line earlier.
- Connection settings are hardcoded in `load.py` — only the password comes from `.env`.
- No tests. `count_tags` is the easy first one — no files, no network.
