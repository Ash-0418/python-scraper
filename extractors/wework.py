import re
import requests
import cloudscraper
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent":
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36"
}
BASE_URL = "https://weworkremotely.com/remote-jobs/search?utf8=%E2%9C%93&term="

scraper = cloudscraper.create_scraper()  # returns a requests.Session object


def extract_wework_jobs(keyword):
    # 1. URL 설정
    url = f"{BASE_URL}{keyword}"
    # 2. 웹페이지 요청
    response = requests.get(url, headers=HEADERS)

    # 3. BeautifulSoup으로 HTML 파싱
    soup = BeautifulSoup(response.text, "html.parser")

    # 4. 채용 공고 가져오기
    jobs_keyword = soup.find_all("li", class_=" new-listing-container feature")
    jobs_keyword += soup.find_all("li", class_="new-listing-container")

    # 5. 출력
    results = []
    upper_keyword = keyword.capitalize()
    jobs = soup.find_all("li", class_=" new-listing-container feature")
    jobs += soup.find_all("li", class_="new-listing-container")

    for job in jobs:
        title = job.find("h4", class_="new-listing__header__title").text.strip()
        company = job.find("p", class_="new-listing__company-name").text.strip()
        link = job.find("a")["href"]

        job_info = {
            "title": title,
            "company": company,
            "link": link,
        }
        results.append(job_info)
    return results

