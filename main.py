from bs4 import BeautifulSoup
import requests
import sys
import json
import os.path

BASE_URL = 'https://junior.guru/jobs/praha/'

def parse_text(job, select):
    data = job.select_one(select)
    if data is None:
        return None
    return data.get_text(strip=True)

def parse_url(job, select):
    data = job.select_one(select)
    if data is None:
        return None
    return data["href"]
    
def parse_jobs(soup):
        jobs = []
        
        for job in soup.find_all("div", class_="jobs-body"):
            title = parse_text(job, "h3.jobs-title a.jobs-title-link")
            company = parse_text(job, "p.jobs-info strong.jobs-info-item")
            location = parse_text(job, "p.jobs-info span.jobs-info-item")
            url = parse_url(job, "h3.jobs-title a.jobs-title-link")
            
            current_job = {"title": title, "company": company, "location": location, "url": url}
            jobs.append(current_job)
            
        return jobs


if __name__ == "__main__":
    
    if os.path.isfile("page.html"):
        print("File page.html already exists. Skipping download.")
                 
    else:    
        try:
            r = requests.get(BASE_URL, timeout=30)
            r.raise_for_status()
        except requests.exceptions.HTTPError as e:
            print("HTTP error occured", e)
            sys.exit(1)
        except requests.exceptions.RequestException as e:
            print("A request error occurred:", e)
            sys.exit(1)

        with open("page.html", 'w', encoding="utf-8") as f:
            f.write(r.text)

    with open("page.html", 'r', encoding="utf-8") as f:
        soup = BeautifulSoup(f, 'html.parser')

    jobs = parse_jobs(soup)
    
    with open("jobs.json", "w", encoding="utf-8") as file:
        json.dump(jobs, file, indent=4, ensure_ascii=False)
        