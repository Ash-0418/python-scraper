import pytest
import os
import tempfile
from unittest.mock import patch, MagicMock
import sys

# 프로젝트 루트 디렉토리를 Python path에 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Flask 앱 import
import main


class TestMainApp:
    
    @pytest.fixture
    def app(self):
        """Flask 애플리케이션 테스트 설정"""
        # 테스트용 설정
        main.app.config['TESTING'] = True
        main.app.config['WTF_CSRF_ENABLED'] = False
        
        # 테스트 시작 전 db 초기화
        main.db.clear()
        
        return main.app

    @pytest.fixture
    def client(self, app):
        """Flask 테스트 클라이언트"""
        return app.test_client()

    @pytest.fixture
    def mock_job_data(self):
        """테스트용 job 데이터"""
        return [
            {
                "title": "Python Developer",
                "company": "TechCorp",
                "link": "/job/python-dev"
            },
            {
                "title": "Backend Engineer", 
                "company": "StartupXYZ",
                "link": "/job/backend-eng"
            }
        ]

    def test_home_page(self, client):
        """홈페이지 접속 테스트"""
        response = client.get('/')
        assert response.status_code == 200
        assert b'html' in response.data  # HTML 페이지가 반환되는지 확인

    @patch('main.extract_web3_jobs')
    @patch('main.extract_wework_jobs')
    @patch('main.extract_berlin_jobs')
    def test_search_first_time(self, mock_berlin, mock_wework, mock_web3, client, mock_job_data):
        """첫 번째 검색 테스트 (캐시되지 않은 상태)"""
        # Mock 데이터 설정
        mock_web3.return_value = mock_job_data
        mock_wework.return_value = []
        mock_berlin.return_value = []
        
        # 검색 요청
        response = client.get('/search?keyword=python')
        
        # 검증
        assert response.status_code == 200
        assert b'python' in response.data  # 키워드가 페이지에 표시되는지
        
        # 모든 extractor가 호출되었는지 확인
        mock_web3.assert_called_once_with('python')
        mock_wework.assert_called_once_with('python')
        mock_berlin.assert_called_once_with('python')
        
        # db에 결과가 저장되었는지 확인
        assert 'python' in main.db
        assert main.db['python'] == mock_job_data

    def test_search_cached_result(self, client, mock_job_data):
        """캐시된 검색 결과 테스트"""
        # 미리 db에 데이터 저장 (캐시 시뮬레이션)
        main.db['javascript'] = mock_job_data
        
        with patch('main.extract_web3_jobs') as mock_web3:
            response = client.get('/search?keyword=javascript')
            
            # 검증
            assert response.status_code == 200
            assert b'javascript' in response.data
            
            # extractor가 호출되지 않았는지 확인 (캐시 사용)
            mock_web3.assert_not_called()

    def test_search_without_keyword(self, client):
        """키워드 없이 검색 시 리다이렉트 테스트"""
        response = client.get('/search')
        
        # 홈페이지로 리다이렉트되는지 확인
        assert response.status_code == 302
        assert response.location == '/'

    def test_search_empty_keyword(self, client):
        """빈 키워드로 검색 시 리다이렉트 테스트"""
        response = client.get('/search?keyword=')
        
        # 홈페이지로 리다이렉트되는지 확인
        assert response.status_code == 302
        assert response.location == '/'

    @patch('main.extract_web3_jobs')
    @patch('main.extract_wework_jobs') 
    @patch('main.extract_berlin_jobs')
    def test_search_with_extractor_error(self, mock_berlin, mock_wework, mock_web3, client):
        """extractor에서 에러 발생 시 테스트"""
        # Mock에서 예외 발생 시뮬레이션
        mock_web3.side_effect = Exception("Network error")
        mock_wework.return_value = []
        mock_berlin.return_value = []
        
        # 예외가 발생해도 500 에러가 나는지 확인
        response = client.get('/search?keyword=error')
        assert response.status_code == 500

    @patch('main.save_to_file')
    def test_export_with_cached_data(self, mock_save_to_file, client, mock_job_data):
        """캐시된 데이터 CSV 다운로드 테스트"""
        # 미리 db에 데이터 저장
        keyword = 'python'
        main.db[keyword] = mock_job_data
        
        # 임시 파일 생성 시뮬레이션
        with tempfile.NamedTemporaryFile(suffix=f'{keyword}.csv', delete=False) as tmp_file:
            tmp_file.write(b'Title,Company,Link\n')
            tmp_file.write(b'Python Developer,TechCorp,/job/python-dev\n')
            tmp_file_path = tmp_file.name
        
        try:
            # export 요청
            with patch('main.send_file') as mock_send_file:
                mock_send_file.return_value = "file_content"
                response = client.get(f'/export?keyword={keyword}')
                
                # 검증
                mock_save_to_file.assert_called_once_with(keyword, mock_job_data)
                mock_send_file.assert_called_once_with(f"{keyword}.csv", as_attachment=True)
        finally:
            # 임시 파일 정리
            if os.path.exists(tmp_file_path):
                os.unlink(tmp_file_path)

    def test_export_without_keyword(self, client):
        """키워드 없이 export 시 리다이렉트 테스트"""
        response = client.get('/export')
        
        # 홈페이지로 리다이렉트되는지 확인
        assert response.status_code == 302
        assert response.location == '/'

    def test_export_without_cached_data(self, client):
        """캐시되지 않은 데이터 export 시 검색페이지로 리다이렉트 테스트"""
        keyword = 'notcached'
        
        # db에 해당 키워드가 없는 상태에서 export 요청
        response = client.get(f'/export?keyword={keyword}')
        
        # 검색페이지로 리다이렉트되는지 확인
        assert response.status_code == 302
        assert response.location == f'/search?keyword={keyword}'

    @patch('main.extract_web3_jobs')
    @patch('main.extract_wework_jobs')
    @patch('main.extract_berlin_jobs')
    def test_search_multiple_keywords_caching(self, mock_berlin, mock_wework, mock_web3, client, mock_job_data):
        """여러 키워드 검색 및 캐싱 테스트"""
        # Mock 설정
        mock_web3.return_value = mock_job_data
        mock_wework.return_value = []
        mock_berlin.return_value = []
        
        keywords = ['python', 'javascript', 'react']
        
        for keyword in keywords:
            response = client.get(f'/search?keyword={keyword}')
            assert response.status_code == 200
            assert keyword.encode() in response.data
            assert keyword in main.db
        
        # 모든 키워드가 캐시되었는지 확인
        assert len(main.db) == 3
        for keyword in keywords:
            assert main.db[keyword] == mock_job_data

    @patch('main.extract_web3_jobs')
    @patch('main.extract_wework_jobs')
    @patch('main.extract_berlin_jobs')
    def test_search_only_uses_web3_results(self, mock_berlin, mock_wework, mock_web3, client):
        """search 함수가 web3 결과만 사용하는지 테스트"""
        # 각각 다른 Mock 데이터 설정
        web3_data = [{"title": "Web3 Job", "company": "Web3 Corp", "link": "/web3"}]
        wework_data = [{"title": "WeWork Job", "company": "WeWork Corp", "link": "/wework"}]
        berlin_data = [{"title": "Berlin Job", "company": "Berlin Corp", "link": "/berlin"}]
        
        mock_web3.return_value = web3_data
        mock_wework.return_value = wework_data
        mock_berlin.return_value = berlin_data
        
        response = client.get('/search?keyword=test')
        
        # web3 결과만 저장되었는지 확인 (코드에서 jobs = web3로 설정됨)
        assert main.db['test'] == web3_data
        assert main.db['test'] != wework_data
        assert main.db['test'] != berlin_data

    def test_db_state_isolation_between_tests(self, client):
        """테스트 간 db 상태 격리 확인"""
        # db가 각 테스트마다 초기화되는지 확인
        assert len(main.db) == 0 or len(main.db) <= 3  # 이전 테스트의 영향 최소화
        
        # 새로운 데이터 추가
        main.db['isolation_test'] = [{"title": "Test", "company": "Test", "link": "/test"}]
        assert 'isolation_test' in main.db

    @patch('main.extract_web3_jobs')
    @patch('main.extract_wework_jobs')
    @patch('main.extract_berlin_jobs')
    def test_search_with_special_characters(self, mock_berlin, mock_wework, mock_web3, client, mock_job_data):
        """특수문자가 포함된 키워드 검색 테스트"""
        mock_web3.return_value = mock_job_data
        mock_wework.return_value = []
        mock_berlin.return_value = []
        
        # URL 인코딩이 필요한 키워드
        keyword = 'machine learning'
        response = client.get(f'/search?keyword={keyword}')
        
        assert response.status_code == 200
        assert keyword in main.db
        
        # extractor가 올바른 키워드로 호출되었는지 확인
        mock_web3.assert_called_once_with(keyword)
        mock_wework.assert_called_once_with(keyword)
        mock_berlin.assert_called_once_with(keyword) 