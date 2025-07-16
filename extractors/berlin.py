import requests
import cloudscraper
from bs4 import BeautifulSoup
from bs4.element import Tag


HEADERS = {
    "User-Agent":
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36"
}
BASE_URL = "https://berlinstartupjobs.com"

scraper = cloudscraper.create_scraper()  # returns a requests.Session object


def extract_berlin_jobs(keyword):
    url = f"{BASE_URL}/skill-areas/{keyword}/"
    response = requests.get(url, headers=HEADERS)
    soup = BeautifulSoup(response.text, "html.parser")
    jobs = soup.find_all("li", class_="bjs-jlid")

    results = []

    for job in jobs:
        title = job.find("h4").text.strip()  # type: ignore
        company = job.find("a", class_="bjs-jlid__b").text.strip()  # type: ignore
        link = job.find("a")["href"]  # type: ignore
        #description = job.find("div", class_="bjs-jlid__description").text.strip()

        # 💡 딕셔너리로 정리
        job_info = {
            "title": title,
            "company": company,
            "link": link,
        }

        results.append(job_info)
    return results
