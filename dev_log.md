# Dev log

Notes on what broke and why.

## Aug 31

venv, `.gitignore`, deps.

- `requirements.txt` came out as UTF-16, because that's what PowerShell does with
  `pip freeze >`. `pip install -r` chokes on it. Took me a while to spot, the file looks
  completely normal in the editor. Rewrote it as UTF-8 and cut it down to the two deps
  I actually import.

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
- The cache never expires. As long as `page.html` is there, the script never fetches a
  new page. Not great for a job radar. Still broken.
- `main` saved the list to json and then read it straight back, while the same list was
  sitting in memory. Dropped that, so now `read_jobs` isn't called anywhere. Keeping it
  for running the stats off an existing file.
- `count_tech` wasn't counting tech. The tags mix languages, cities (`praha`, `brno`),
  contract type (`fulltime`) and job boards (`jobscz`, `linkedin`) — three of the top
  five aren't technologies. Renamed to `count_tags`.
- `if/else` counter became `tag_counts.get(tag, 0) + 1`.
- The dict comprehension around `sorted` did nothing except push the line to 110 chars.
- Returned a dict when what I needed was an order.

## Sep 8

Printing the top 10 tags.

- Because of the dict, slicing didn't work, so the printing came out clunky:
  `list(tag_counts.items())[:limit]`. The problem wasn't the printing, it was the
  useless `dict(...)` one level up. Dropped it and got `tag_counts[:TOP_TAGS]`.
- Also: trailing whitespace, blank lines between functions, quotes, `occured` typo.

## Sep 10

Postgres in Docker. Container `jobdb`, table `job` (`id`, `title`, `company`, `url`,
`location`). Commands are in [README.md](README.md).

- No column for tags, even though the parser collects them and all the stats are based
  on them.
- `main.py` doesn't know about the database yet, still writes json. The one row in there
  I typed by hand.
- Created the container without `-v name:path`, so the volume has a random name. Fine
  for now, annoying if I ever `docker rm` it.

## TODO

- Cache never refreshes — needs a max age or a `--refresh` flag.
- Mixed link formats: some relative (`/jobs/...`), some absolute. `urllib.parse.urljoin`.
- If the site's markup changes, the parser returns 0 jobs and reports success.
- No dedup — same job gets written twice. `url` is the natural key.
- `read_jobs` is unused.
- `jobs.json` is caught by `*.json` in `.gitignore`. Decide if that's what I want.
- No tests. `count_tags` is the easy first one — no files, no network.
