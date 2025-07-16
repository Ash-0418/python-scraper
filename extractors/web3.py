from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import cloudscraper
import time

HEADERS = {
    "User-Agent":
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36"
}
BASE_URL = "https://web3.career"

scraper = cloudscraper.create_scraper()  # returns a requests.Session object


def extract_web3_jobs(keyword):
    job_list = []
    #selennium 옵션
    options = Options()
    options.add_argument("--headless=new")  # 👈 이 옵션이 핵심
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    # 1. 크롬 드라이버 자동 설치 및 실행
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    # 2. 웹 페이지 열기
    driver.get(f"{BASE_URL}/{keyword}-jobs")

    # 3. 자바스크립트 로딩 대기 (너무 빨리 읽으면 아무것도 안 나올 수 있음)
    time.sleep(3)

    # 4. 채용 제목 가져오기 (data-jobid를 가진 h2)
    titles = driver.find_elements(By.CSS_SELECTOR, "h2[data-jobid]")
    compayies = driver.find_elements(By.CSS_SELECTOR, "h3[data-jobid]")
    links = driver.find_elements(By.CSS_SELECTOR, "a[data-jobid]")

    for title, company, link in zip(titles, compayies, links):
        title_text = title.text.strip()
        company_text = company.text.strip()
        link_text = link.get_attribute("href").strip() # type: ignore

        # 💡 딕셔너리로 정리
        job_info = {
            "title": title_text,
            "company": company_text,
            "link": link_text,
        }
        job_list.append(job_info)
    # 5. 출력
    for job in job_list:
        print("제목:", job["title"])
        print("회사:", job["company"])
        print("링크:", job["link"])
        print("-" * 20)
    
    # 6. 브라우저 종료
    driver.quit()
    return job_list


