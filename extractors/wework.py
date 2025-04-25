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


def scraper(word):
    # 1. URL 설정
    url_word = f"{BASE_URL}{word}"
    # 2. 웹페이지 요청
    response_word = requests.get(url_word, headers=HEADERS)

    # 3. BeautifulSoup으로 HTML 파싱
    soup_word = BeautifulSoup(response_word.text, "html.parser")

    # 4. 채용 공고 가져오기
    jobs_word = soup_word.find_all("li",
                                   class_=" new-listing-container feature")
    jobs_word += soup_word.find_all("li", class_="new-listing-container")

    # 5. 출력
    results = []
    upper_word = word.capitalize()
    print(f"\n🔹 {upper_word} Jobs 🔹")
    for job_word in jobs_word:
        title = job_word.find(
            "h4", class_="new-listing__header__title").text.strip()
        company = job_word.find(
            "p", class_="new-listing__company-name").text.strip()
        link = job_word.find("a")["href"]

        print("제목:", title)
        print("회사:", company)
        print("링크:", link)

        print("-" * 40)
        job_info = {
            "title": title,
            "company": company,
            "link": link,
        }
        results.append(job_info)
    return results

