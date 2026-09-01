from bs4 import BeautifulSoup
import requests

BASE_URL = 'https://junior.guru/jobs/praha/'

r = requests.get(BASE_URL)

with open("page.html", 'w', encoding="utf-8") as f:
    f.write(r.text)

with open("page.html", 'r', encoding="utf-8") as f:
    soup = BeautifulSoup(f, 'html.parser')

for job in soup.find_all("div", class_="jobs-body", limit=10):
    title = job.select_one("h3.jobs-title a.jobs-title-link").get_text(strip=True)
    company = job.select_one("p.jobs-info strong.jobs-info-item").get_text(strip=True)
    location = job.select_one("p.jobs-info span.jobs-info-item").get_text(strip=True)
    url = job.select_one("h3.jobs-title a.jobs-title-link")["href"]

    print(f"{title}")
    print(f"  Company:  {company}")
    print(f"  Location: {location}")
    print(f"  URL:      {url}")
    print()