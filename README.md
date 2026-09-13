# job-radar

Job scraper for [junior.guru](https://junior.guru/jobs/praha/). Collects title, company,
location, link and tags, saves them to `jobs.json` and to Postgres, prints the top 10
tags. A small FastAPI app serves what's in the database.

## Running it

```bash
pip install -r requirements.txt
python main.py
```

The page is cached in `page.html`, and while that file is there the script won't hit the
network. To get fresh data, delete the cache: `rm page.html`.

## Running the API

```bash
uvicorn app:app --reload
```

Then open <http://127.0.0.1:8000>.

`app:app` is `module:variable` — the file `app.py`, and the `app = FastAPI()` object
inside it. uvicorn imports the module and serves that object. `--reload` restarts the
server whenever a file changes, which is for development only.

| Endpoint | Returns |
|---|---|
| `/health` | `{"status": "ok"}` — just checks the server is up |
| `/jobs` | every job in the database as json |
| `/docs` | generated, clickable API docs |

`/jobs` reads from Postgres, so the container has to be running. If it isn't, the
request fails with a connection error.

Another port, if 8000 is busy:

```bash
uvicorn app:app --reload --port 8001
```

---

# Postgres in Docker

Current setup: container `jobdb`, postgres 18, port `5433`, user `postgres`,
password `secret`, database `postgres`.

Port 5433 and not 5432, because a Postgres installed in Windows already holds 5432.

## Container

```bash
docker ps                  # what's running
docker ps -a               # everything, including stopped
docker start jobdb
docker stop jobdb
docker logs jobdb          # check this when it won't connect
```

Create from scratch (once, if the container doesn't exist yet):

```bash
docker run -d --name jobdb -e POSTGRES_PASSWORD=secret -p 5433:5432 -v jobdb-data:/var/lib/postgresql postgres
```

`-d` runs it in the background, `-p 5433:5432` publishes port 5433 on this machine, `-v jobdb-data:...`
is the data volume so it survives the container being deleted.

Deleting (careful, `docker volume rm` wipes the database for good):

```bash
docker stop jobdb
docker rm jobdb
docker volume ls
docker volume rm jobdb-data
```

## Getting into psql

```bash
docker exec -it jobdb psql -U postgres
```

Running a single query without opening the console:

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

## The job table

```
 id       | integer | not null | nextval('job_id_seq'::regclass)
 title    | text
 company  | text
 url      | text
 location | text
```

```sql
select * from job limit 5;
select count(*) from job;
select * from job where location = 'Praha';
select company, count(*) from job group by company order by count(*) desc;

insert into job (title, company, url, location)
values ('Python Developer', 'Red Hat', 'https://example.com', 'Brno');

delete from job where id = 1;
truncate job restart identity;   -- empty the table and reset the id counter
```

Recreating the table:

```sql
create table job (
    id serial primary key,
    title text,
    company text,
    url text,
    location text
);
```

## When it doesn't work

- `Cannot connect to the Docker daemon` — Docker Desktop isn't running.
- `No such container: jobdb` — the container doesn't exist, see `docker run` above.
- `port is already allocated` — something else is on that port, publish another one.
- Error text comes back as mojibake — that's the Windows Postgres answering, not the
  container. Check the port.
- `the input device is not a TTY` — missing `-it` on `docker exec`.
- psql not responding, prompt shows `postgres-#` — it's waiting for a `;`.
