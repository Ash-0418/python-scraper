from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time

# 1. 크롬 드라이버 자동 설치 및 실행
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))

# 2. 웹 페이지 열기
driver.get("https://web3.career/mobile-jobs")

# 3. 자바스크립트 로딩 대기 (너무 빨리 읽으면 아무것도 안 나올 수 있음)
time.sleep(3)

# 4. 채용 제목 가져오기 (data-jobid를 가진 h2)
titles = driver.find_elements(By.CSS_SELECTOR, "h2[data-jobid]")

# 5. 출력
for title in titles:
    print("제목:", title.text)

# 6. 브라우저 종료
driver.quit()
