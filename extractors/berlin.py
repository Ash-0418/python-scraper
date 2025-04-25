import requests
import cloudscraper
from bs4 import BeautifulSoup

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
        job: Tag  #에러 삭제 - job이 Tag 타입임을 명시
        title = job.find("h4").text.strip()
        company = job.find("a", class_="bjs-jlid__b").text.strip()
        link = job.find("a")["href"]
        #description = job.find("div", class_="bjs-jlid__description").text.strip()

        # 💡 딕셔너리로 정리
        job_info = {
            "title": title,
            "company": company,
            "link": link,
        }
        print("제목:", title)
        print("회사:", company)
        print("링크:", link)
        #print("설명:", description)

        results.append(job_info)
    return results
