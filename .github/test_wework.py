import pytest
import requests
from unittest.mock import patch, MagicMock
from bs4 import BeautifulSoup
import sys
import os

# 프로젝트 루트 디렉토리를 Python path에 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from extractors.wework import extract_wework_jobs, BASE_URL


class TestWeworkJobs:
    
    @pytest.fixture
    def mock_html_response(self):
        """정상적인 HTML 응답을 시뮬레이션하는 fixture"""
        html_content = """
        <html>
            <body>
                <ul>
                    <li class=" new-listing-container feature">
                        <a href="/job/remote-python-developer">
                            <h4 class="new-listing__header__title">Senior Python Developer</h4>
                        </a>
                        <p class="new-listing__company-name">TechCorp Inc</p>
                    </li>
                    <li class="new-listing-container">
                        <a href="/job/remote-fullstack-engineer">
                            <h4 class="new-listing__header__title">Full Stack Engineer</h4>
                        </a>
                        <p class="new-listing__company-name">StartupXYZ</p>
                    </li>
                    <li class=" new-listing-container feature">
                        <a href="/job/remote-devops-engineer">
                            <h4 class="new-listing__header__title">DevOps Engineer</h4>
                        </a>
                        <p class="new-listing__company-name">CloudSolutions</p>
                    </li>
                </ul>
            </body>
        </html>
        """
        return html_content

    @pytest.fixture
    def mock_empty_response(self):
        """빈 결과를 시뮬레이션하는 fixture"""
        html_content = """
        <html>
            <body>
                <ul>
                    <!-- 매칭되는 li 요소가 없음 -->
                    <li class="other-class">Other content</li>
                </ul>
            </body>
        </html>
        """
        return html_content

    @pytest.fixture
    def mock_invalid_html(self):
        """잘못된 HTML 구조를 시뮬레이션하는 fixture"""
        html_content = """
        <html>
            <body>
                <ul>
                    <li class="new-listing-container">
                        <a href="/job/incomplete-job">
                            <!-- h4 태그 누락 -->
                        </a>
                        <!-- p 태그 누락 -->
                    </li>
                </ul>
            </body>
        </html>
        """
        return html_content

    @patch('extractors.wework.requests.get')
    def test_extract_wework_jobs_success(self, mock_get, mock_html_response):
        """정상적인 경우 테스트"""
        # Mock response 설정
        mock_response = MagicMock()
        mock_response.text = mock_html_response
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        # 함수 실행
        result = extract_wework_jobs("python")
        
        # 검증
        assert isinstance(result, list)
        assert len(result) == 3  # feature 2개 + normal 1개
        
        # 첫 번째 job 검증 (feature)
        first_job = result[0]
        assert first_job['title'] == 'Senior Python Developer'
        assert first_job['company'] == 'TechCorp Inc'
        assert first_job['link'] == '/job/remote-python-developer'
        
        # 두 번째 job 검증 (normal)
        second_job = result[1]
        assert second_job['title'] == 'Full Stack Engineer'
        assert second_job['company'] == 'StartupXYZ'
        assert second_job['link'] == '/job/remote-fullstack-engineer'
        
        # 세 번째 job 검증 (feature)
        third_job = result[2]
        assert third_job['title'] == 'DevOps Engineer'
        assert third_job['company'] == 'CloudSolutions'
        assert third_job['link'] == '/job/remote-devops-engineer'
        
        # API 호출 검증
        expected_url = f"{BASE_URL}python"
        mock_get.assert_called_once_with(expected_url, headers={
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36"
        })

    @patch('extractors.wework.requests.get')
    def test_extract_wework_jobs_empty_result(self, mock_get, mock_empty_response):
        """빈 결과인 경우 테스트"""
        # Mock response 설정
        mock_response = MagicMock()
        mock_response.text = mock_empty_response
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        # 함수 실행
        result = extract_wework_jobs("nonexistent")
        
        # 검증
        assert isinstance(result, list)
        assert len(result) == 0

    @patch('extractors.wework.requests.get')
    def test_extract_wework_jobs_http_error(self, mock_get):
        """HTTP 에러 발생시 테스트"""
        # Mock response 설정 (에러 발생)
        mock_get.side_effect = requests.exceptions.RequestException("Connection error")
        
        # 함수 실행시 예외 발생 검증
        with pytest.raises(requests.exceptions.RequestException):
            extract_wework_jobs("python")

    @patch('extractors.wework.requests.get')
    def test_extract_wework_jobs_invalid_html(self, mock_get, mock_invalid_html):
        """잘못된 HTML 구조인 경우 테스트"""
        # Mock response 설정
        mock_response = MagicMock()
        mock_response.text = mock_invalid_html
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        # 함수 실행시 AttributeError 발생 검증 (h4 또는 p 태그가 없어서)
        with pytest.raises(AttributeError):
            extract_wework_jobs("python")

    @patch('extractors.wework.requests.get')
    def test_extract_wework_jobs_different_keywords(self, mock_get, mock_html_response):
        """다른 키워드로 호출시 URL 변경 테스트"""
        # Mock response 설정
        mock_response = MagicMock()
        mock_response.text = mock_html_response
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        # 여러 키워드로 테스트
        keywords = ["javascript", "react", "node", "golang"]
        
        for keyword in keywords:
            extract_wework_jobs(keyword)
            expected_url = f"{BASE_URL}{keyword}"
            mock_get.assert_called_with(expected_url, headers={
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36"
            })

    @patch('extractors.wework.requests.get')
    def test_extract_wework_jobs_return_structure(self, mock_get, mock_html_response):
        """반환값 구조 검증 테스트"""
        # Mock response 설정
        mock_response = MagicMock()
        mock_response.text = mock_html_response
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        # 함수 실행
        result = extract_wework_jobs("python")
        
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

    @patch('extractors.wework.requests.get')
    def test_extract_wework_jobs_both_listing_types(self, mock_get):
        """feature와 normal 두 가지 listing 타입 모두 처리하는지 테스트"""
        # 각각 다른 타입의 listing만 있는 HTML
        html_with_feature_only = """
        <html>
            <body>
                <li class=" new-listing-container feature">
                    <a href="/job/feature-job">
                        <h4 class="new-listing__header__title">Feature Job</h4>
                    </a>
                    <p class="new-listing__company-name">Feature Company</p>
                </li>
            </body>
        </html>
        """
        
        html_with_normal_only = """
        <html>
            <body>
                <li class="new-listing-container">
                    <a href="/job/normal-job">
                        <h4 class="new-listing__header__title">Normal Job</h4>
                    </a>
                    <p class="new-listing__company-name">Normal Company</p>
                </li>
            </body>
        </html>
        """
        
        # Feature 타입만 있는 경우 테스트
        mock_response_feature = MagicMock()
        mock_response_feature.text = html_with_feature_only
        mock_get.return_value = mock_response_feature
        
        result_feature = extract_wework_jobs("test")
        assert len(result_feature) == 1
        assert result_feature[0]['title'] == 'Feature Job'
        
        # Normal 타입만 있는 경우 테스트
        mock_response_normal = MagicMock()
        mock_response_normal.text = html_with_normal_only
        mock_get.return_value = mock_response_normal
        
        result_normal = extract_wework_jobs("test")
        assert len(result_normal) == 1
        assert result_normal[0]['title'] == 'Normal Job'

    @patch('extractors.wework.requests.get')
    def test_extract_wework_jobs_url_encoding(self, mock_get, mock_html_response):
        """키워드에 공백이나 특수문자가 있을 때 URL 처리 테스트"""
        # Mock response 설정
        mock_response = MagicMock()
        mock_response.text = mock_html_response
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        # 공백이 포함된 키워드 테스트
        keyword_with_space = "machine learning"
        extract_wework_jobs(keyword_with_space)
        
        expected_url = f"{BASE_URL}{keyword_with_space}"
        mock_get.assert_called_with(expected_url, headers={
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36"
        })

    @pytest.fixture
    def mock_partial_data_html(self):
        """일부 데이터만 있는 HTML"""
        html_content = """
        <html>
            <body>
                <ul>
                    <li class="new-listing-container">
                        <a href="/job/partial-job">
                            <h4 class="new-listing__header__title">Partial Job Title</h4>
                        </a>
                        <p class="new-listing__company-name">Partial Company</p>
                    </li>
                </ul>
            </body>
        </html>
        """
        return html_content

    @patch('extractors.wework.requests.get')
    def test_extract_wework_jobs_with_partial_data(self, mock_get, mock_partial_data_html):
        """일부 데이터만 있는 경우에도 정상 처리되는지 테스트"""
        # Mock response 설정
        mock_response = MagicMock()
        mock_response.text = mock_partial_data_html
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        # 함수 실행
        result = extract_wework_jobs("test")
        
        # 검증
        assert isinstance(result, list)
        assert len(result) == 1
        
        job = result[0]
        assert job['title'] == 'Partial Job Title'
        assert job['company'] == 'Partial Company'
        assert job['link'] == '/job/partial-job' 