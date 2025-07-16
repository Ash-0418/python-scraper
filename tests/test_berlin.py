import pytest
import requests
from unittest.mock import patch, MagicMock
from bs4 import BeautifulSoup
import sys
import os

# 프로젝트 루트 디렉토리를 Python path에 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from extractors.berlin import extract_berlin_jobs, BASE_URL


class TestBerlinJobs:
    
    @pytest.fixture
    def mock_html_response(self):
        """정상적인 HTML 응답을 시뮬레이션하는 fixture"""
        html_content = """
        <html>
            <body>
                <ul>
                    <li class="bjs-jlid">
                        <a href="/job/python-developer">Apply Now</a>
                        <h4>Python Developer</h4>
                        <a class="bjs-jlid__b" href="/company/test-company">Test Company</a>
                    </li>
                    <li class="bjs-jlid">
                        <a href="/job/software-engineer">Apply Now</a>
                        <h4>Software Engineer</h4>
                        <a class="bjs-jlid__b" href="/company/another-company">Another Company</a>
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
                    <li class="bjs-jlid">
                        <!-- h4 태그 누락 -->
                        <a class="bjs-jlid__b" href="/company/test-company">Test Company</a>
                        <a href="/job/python-developer">Apply Now</a>
                    </li>
                </ul>
            </body>
        </html>
        """
        return html_content

    @patch('extractors.berlin.requests.get')
    def test_extract_berlin_jobs_success(self, mock_get, mock_html_response):
        """정상적인 경우 테스트"""
        # Mock response 설정
        mock_response = MagicMock()
        mock_response.text = mock_html_response
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        # 함수 실행
        result = extract_berlin_jobs("python")
        
        # 검증
        assert isinstance(result, list)
        assert len(result) == 2
        
        # 첫 번째 job 검증
        first_job = result[0]
        assert first_job['title'] == 'Python Developer'
        assert first_job['company'] == 'Test Company'
        assert first_job['link'] == '/job/python-developer'
        
        # 두 번째 job 검증
        second_job = result[1]
        assert second_job['title'] == 'Software Engineer'
        assert second_job['company'] == 'Another Company'
        assert second_job['link'] == '/job/software-engineer'
        
        # API 호출 검증
        expected_url = f"{BASE_URL}/skill-areas/python/"
        mock_get.assert_called_once_with(expected_url, headers={
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36"
        })

    @patch('extractors.berlin.requests.get')
    def test_extract_berlin_jobs_empty_result(self, mock_get, mock_empty_response):
        """빈 결과인 경우 테스트"""
        # Mock response 설정
        mock_response = MagicMock()
        mock_response.text = mock_empty_response
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        # 함수 실행
        result = extract_berlin_jobs("nonexistent")
        
        # 검증
        assert isinstance(result, list)
        assert len(result) == 0

    @patch('extractors.berlin.requests.get')
    def test_extract_berlin_jobs_http_error(self, mock_get):
        """HTTP 에러 발생시 테스트"""
        # Mock response 설정 (에러 발생)
        mock_get.side_effect = requests.exceptions.RequestException("Connection error")
        
        # 함수 실행시 예외 발생 검증
        with pytest.raises(requests.exceptions.RequestException):
            extract_berlin_jobs("python")

    @patch('extractors.berlin.requests.get')
    def test_extract_berlin_jobs_invalid_html(self, mock_get, mock_invalid_html):
        """잘못된 HTML 구조인 경우 테스트"""
        # Mock response 설정
        mock_response = MagicMock()
        mock_response.text = mock_invalid_html
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        # 함수 실행시 AttributeError 발생 검증 (h4 태그가 없어서)
        with pytest.raises(AttributeError):
            extract_berlin_jobs("python")

    @patch('extractors.berlin.requests.get')
    def test_extract_berlin_jobs_different_keywords(self, mock_get, mock_html_response):
        """다른 키워드로 호출시 URL 변경 테스트"""
        # Mock response 설정
        mock_response = MagicMock()
        mock_response.text = mock_html_response
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        # 여러 키워드로 테스트
        keywords = ["java", "javascript", "react", "django"]
        
        for keyword in keywords:
            extract_berlin_jobs(keyword)
            expected_url = f"{BASE_URL}/skill-areas/{keyword}/"
            mock_get.assert_called_with(expected_url, headers={
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36"
            })

    @patch('extractors.berlin.requests.get')
    def test_extract_berlin_jobs_return_structure(self, mock_get, mock_html_response):
        """반환값 구조 검증 테스트"""
        # Mock response 설정
        mock_response = MagicMock()
        mock_response.text = mock_html_response
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        # 함수 실행
        result = extract_berlin_jobs("python")
        
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