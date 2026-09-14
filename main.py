from bs4 import BeautifulSoup
import requests
import sys
import json
import os.path
from load import load_jobs_to_db


BASE_URL = "https://junior.guru/jobs/praha/"
CACHE_FILE = "data/page.html"
JOBS_FILE = "data/jobs.json"
TOP_TAGS = 10


def download_page(url, path):
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
    except requests.exceptions.HTTPError as e:
        print("HTTP error occurred:", e)
        sys.exit(1)
    except requests.exceptions.RequestException as e:
        print("A request error occurred:", e)
        sys.exit(1)

    with open(path, "w", encoding="utf-8") as f:
        f.write(response.text)


def load_soup(path):
    with open(path, "r", encoding="utf-8") as f:
        return BeautifulSoup(f, "html.parser")


def parse_text(job, selector):
    element = job.select_one(selector)
    if element is None:
        return None
    return element.get_text(strip=True)


def parse_url(job, selector):
    element = job.select_one(selector)
    if element is None:
        return None
    return element.get("href")


def parse_tags(job, selector):
    elements = job.select(selector)
    return [element.get("data-jobs-tag") for element in elements]


def parse_jobs(soup):
    jobs = []

    for job in soup.find_all("div", class_="jobs-body"):
        jobs.append({
            "title": parse_text(job, "h3.jobs-title a.jobs-title-link"),
            "company": parse_text(job, "p.jobs-info strong.jobs-info-item"),
            "location": parse_text(job, "p.jobs-info span.jobs-info-item"),
            "url": parse_url(job, "h3.jobs-title a.jobs-title-link"),
            "tags": parse_tags(job, "p.jobs-tags span.jobs-tag"),
        })

    return jobs


def save_jobs(jobs, path):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(jobs, f, indent=4, ensure_ascii=False)


def read_jobs(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError as e:
        print("File was not found:", e)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print("Not JSON file type:", e)
        sys.exit(1)


def count_tags(jobs):
    tag_counts = {}

    for job in jobs:
        for tag in job["tags"]:
            tag_counts[tag] = tag_counts.get(tag, 0) + 1

    return sorted(tag_counts.items(), key=lambda item: item[1], reverse=True)


if __name__ == "__main__":
    if os.path.isfile(CACHE_FILE):
        print(f"File {CACHE_FILE} already exists. Skipping download.")
    else:
        download_page(BASE_URL, CACHE_FILE)

    soup = load_soup(CACHE_FILE)
    jobs = parse_jobs(soup)
    save_jobs(jobs, JOBS_FILE)
    
    load_jobs_to_db(read_jobs(JOBS_FILE))
    print(f"Saved {len(jobs)} jobs to {JOBS_FILE}.")

    #tag_counts = count_tags(jobs)

    #print(f"\nTop {TOP_TAGS} tags:")
    #for tag, count in tag_counts[:TOP_TAGS]:
    #    print(f"{tag}: {count}")
