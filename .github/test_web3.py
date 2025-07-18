import pytest
from unittest.mock import patch, MagicMock, call
from selenium.common.exceptions import WebDriverException, TimeoutException
from selenium.webdriver.common.by import By
import sys
import os
import time

# 프로젝트 루트 디렉토리를 Python path에 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from extractors.web3 import extract_web3_jobs, BASE_URL


class TestWeb3Jobs:
    
    @pytest.fixture
    def mock_web_elements(self):
        """mock WebElement 객체들을 생성하는 fixture"""
        # Title elements
        title1 = MagicMock()
        title1.text = "Senior Blockchain Developer"
        title2 = MagicMock()
        title2.text = "Smart Contract Engineer"
        
        # Company elements
        company1 = MagicMock()
        company1.text = "CryptoTech Corp"
        company2 = MagicMock()
        company2.text = "Web3 Solutions"
        
        # Link elements
        link1 = MagicMock()
        link1.get_attribute.return_value = "https://web3.career/job/blockchain-dev"
        link2 = MagicMock()
        link2.get_attribute.return_value = "https://web3.career/job/smart-contract"
        
        return {
            'titles': [title1, title2],
            'companies': [company1, company2],
            'links': [link1, link2]
        }
    
    @pytest.fixture
    def mock_empty_elements(self):
        """빈 결과를 위한 fixture"""
        return {
            'titles': [],
            'companies': [],
            'links': []
        }
    
    @patch('extractors.web3.time.sleep')
    @patch('extractors.web3.ChromeDriverManager')
    @patch('extractors.web3.webdriver.Chrome')
    def test_extract_web3_jobs_success(self, mock_chrome, mock_driver_manager, mock_sleep, mock_web_elements):
        """정상적인 경우 테스트"""
        # Mock ChromeDriverManager
        mock_driver_manager.return_value.install.return_value = "/path/to/chromedriver"
        
        # Mock WebDriver
        mock_driver = MagicMock()
        mock_chrome.return_value = mock_driver
        
        # Mock find_elements 반환값 설정
        mock_driver.find_elements.side_effect = [
            mock_web_elements['titles'],
            mock_web_elements['companies'],
            mock_web_elements['links']
        ]
        
        # 함수 실행
        result = extract_web3_jobs("blockchain")
        
        # 검증
        assert isinstance(result, list)
        assert len(result) == 2
        
        # 첫 번째 job 검증
        first_job = result[0]
        assert first_job['title'] == 'Senior Blockchain Developer'
        assert first_job['company'] == 'CryptoTech Corp'
        assert first_job['link'] == 'https://web3.career/job/blockchain-dev'
        
        # 두 번째 job 검증
        second_job = result[1]
        assert second_job['title'] == 'Smart Contract Engineer'
        assert second_job['company'] == 'Web3 Solutions'
        assert second_job['link'] == 'https://web3.career/job/smart-contract'
        
        # WebDriver 호출 검증
        expected_url = f"{BASE_URL}/blockchain-jobs"
        mock_driver.get.assert_called_once_with(expected_url)
        
        # sleep 호출 검증
        mock_sleep.assert_called_once_with(3)
        
        # find_elements 호출 검증 (By.CSS_SELECTOR 포함)
        expected_calls = [
            call(By.CSS_SELECTOR, "h2[data-jobid]"),
            call(By.CSS_SELECTOR, "h3[data-jobid]"),
            call(By.CSS_SELECTOR, "a[data-jobid]")
        ]
        mock_driver.find_elements.assert_has_calls(expected_calls)
        
        # 브라우저 종료 검증
        mock_driver.quit.assert_called_once()
    
    @patch('extractors.web3.time.sleep')
    @patch('extractors.web3.ChromeDriverManager')
    @patch('extractors.web3.webdriver.Chrome')
    def test_extract_web3_jobs_empty_result(self, mock_chrome, mock_driver_manager, mock_sleep, mock_empty_elements):
        """빈 결과인 경우 테스트"""
        # Mock ChromeDriverManager
        mock_driver_manager.return_value.install.return_value = "/path/to/chromedriver"
        
        # Mock WebDriver
        mock_driver = MagicMock()
        mock_chrome.return_value = mock_driver
        
        # Mock find_elements 반환값 설정 (빈 리스트)
        mock_driver.find_elements.side_effect = [
            mock_empty_elements['titles'],
            mock_empty_elements['companies'],
            mock_empty_elements['links']
        ]
        
        # 함수 실행
        result = extract_web3_jobs("nonexistent")
        
        # 검증
        assert isinstance(result, list)
        assert len(result) == 0
        
        # 브라우저 종료 검증
        mock_driver.quit.assert_called_once()
    
    @patch('extractors.web3.time.sleep')
    @patch('extractors.web3.ChromeDriverManager')
    @patch('extractors.web3.webdriver.Chrome')
    def test_extract_web3_jobs_webdriver_error(self, mock_chrome, mock_driver_manager, mock_sleep):
        """WebDriver 생성 에러 테스트"""
        # Mock ChromeDriverManager
        mock_driver_manager.return_value.install.return_value = "/path/to/chromedriver"
        
        # Mock WebDriver 생성 에러
        mock_chrome.side_effect = WebDriverException("Chrome driver not found")
        
        # 함수 실행시 예외 발생 검증
        with pytest.raises(WebDriverException):
            extract_web3_jobs("blockchain")
    
    @patch('extractors.web3.time.sleep')
    @patch('extractors.web3.ChromeDriverManager')
    @patch('extractors.web3.webdriver.Chrome')
    def test_extract_web3_jobs_page_load_error(self, mock_chrome, mock_driver_manager, mock_sleep):
        """페이지 로딩 에러 테스트"""
        # Mock ChromeDriverManager
        mock_driver_manager.return_value.install.return_value = "/path/to/chromedriver"
        
        # Mock WebDriver
        mock_driver = MagicMock()
        mock_chrome.return_value = mock_driver
        
        # Mock 페이지 로딩 에러
        mock_driver.get.side_effect = TimeoutException("Page load timeout")
        
        # 함수 실행시 예외 발생 검증
        with pytest.raises(TimeoutException):
            extract_web3_jobs("blockchain")
        
        # 실제 코드에서는 에러 발생 시 quit이 호출되지 않음 (try-except 블록 없음)
        mock_driver.quit.assert_not_called()
    
    @patch('extractors.web3.time.sleep')
    @patch('extractors.web3.ChromeDriverManager')
    @patch('extractors.web3.webdriver.Chrome')
    def test_extract_web3_jobs_different_keywords(self, mock_chrome, mock_driver_manager, mock_sleep, mock_web_elements):
        """다른 키워드로 호출시 URL 변경 테스트"""
        # Mock ChromeDriverManager
        mock_driver_manager.return_value.install.return_value = "/path/to/chromedriver"
        
        # Mock WebDriver
        mock_driver = MagicMock()
        mock_chrome.return_value = mock_driver
        
        # Mock find_elements 반환값 설정
        mock_driver.find_elements.side_effect = [
            mock_web_elements['titles'],
            mock_web_elements['companies'],
            mock_web_elements['links']
        ]
        
        # 여러 키워드로 테스트
        keywords = ["defi", "nft", "dao", "solidity"]
        
        for keyword in keywords:
            # 각 테스트마다 새로운 driver mock 생성
            mock_driver.reset_mock()
            mock_driver.find_elements.side_effect = [
                mock_web_elements['titles'],
                mock_web_elements['companies'],
                mock_web_elements['links']
            ]
            
            extract_web3_jobs(keyword)
            expected_url = f"{BASE_URL}/{keyword}-jobs"
            mock_driver.get.assert_called_with(expected_url)
    
    @patch('extractors.web3.time.sleep')
    @patch('extractors.web3.ChromeDriverManager')
    @patch('extractors.web3.webdriver.Chrome')
    def test_extract_web3_jobs_return_structure(self, mock_chrome, mock_driver_manager, mock_sleep, mock_web_elements):
        """반환값 구조 검증 테스트"""
        # Mock ChromeDriverManager
        mock_driver_manager.return_value.install.return_value = "/path/to/chromedriver"
        
        # Mock WebDriver
        mock_driver = MagicMock()
        mock_chrome.return_value = mock_driver
        
        # Mock find_elements 반환값 설정
        mock_driver.find_elements.side_effect = [
            mock_web_elements['titles'],
            mock_web_elements['companies'],
            mock_web_elements['links']
        ]
        
        # 함수 실행
        result = extract_web3_jobs("blockchain")
        
        # 반환값 구조 검증
        assert isinstance(result, list)
        
        for job in result:
            assert isinstance(job, dict)
            assert 'title' in job
            assert 'company' in job
            assert 'link' in job
            assert isinstance(job['title'], str)
            assert isinstance(job['company'], str)
            assert isinstance(job['link'], str)
            # 빈 문자열이 아닌지 검증
            assert job['title'].strip() != ''
            assert job['company'].strip() != ''
            assert job['link'].strip() != ''
    
    @patch('extractors.web3.time.sleep')
    @patch('extractors.web3.ChromeDriverManager')
    @patch('extractors.web3.webdriver.Chrome')
    def test_extract_web3_jobs_driver_quit_not_called_on_error(self, mock_chrome, mock_driver_manager, mock_sleep):
        """에러 발생 시 driver.quit()이 호출되지 않는지 테스트 (try-except 블록 없음)"""
        # Mock ChromeDriverManager
        mock_driver_manager.return_value.install.return_value = "/path/to/chromedriver"
        
        # Mock WebDriver
        mock_driver = MagicMock()
        mock_chrome.return_value = mock_driver
        
        # Mock find_elements에서 에러 발생
        mock_driver.find_elements.side_effect = Exception("Element not found")
        
        # 함수 실행시 예외 발생 검증
        with pytest.raises(Exception):
            extract_web3_jobs("blockchain")
        
        # 실제 코드에서는 에러 발생 시 quit이 호출되지 않음 (try-except 블록 없음)
        mock_driver.quit.assert_not_called()
    
    @patch('extractors.web3.time.sleep')
    @patch('extractors.web3.ChromeDriverManager')
    @patch('extractors.web3.webdriver.Chrome')
    def test_extract_web3_jobs_chrome_options(self, mock_chrome, mock_driver_manager, mock_sleep, mock_web_elements):
        """Chrome 옵션 설정 테스트"""
        # Mock ChromeDriverManager
        mock_driver_manager.return_value.install.return_value = "/path/to/chromedriver"
        
        # Mock WebDriver
        mock_driver = MagicMock()
        mock_chrome.return_value = mock_driver
        
        # Mock find_elements 반환값 설정
        mock_driver.find_elements.side_effect = [
            mock_web_elements['titles'],
            mock_web_elements['companies'],
            mock_web_elements['links']
        ]
        
        # 함수 실행
        extract_web3_jobs("blockchain")
        
        # Chrome 생성 시 옵션이 전달되었는지 검증
        mock_chrome.assert_called_once()
        call_args = mock_chrome.call_args
        
        # service 인자 검증
        assert 'service' in call_args.kwargs
        
        # options 인자 검증
        assert 'options' in call_args.kwargs
        options = call_args.kwargs['options']
        
        # 옵션 내용은 실제 Options 객체이므로 직접 검증하기 어려움
        # 대신 webdriver.Chrome이 올바른 인자로 호출되었는지만 확인 