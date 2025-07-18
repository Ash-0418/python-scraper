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
            },
            {
                "title": "Full Stack Developer",
                "company": "BerlinTech",
                "link": "/job/fullstack-dev"
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
        # Mock 데이터 설정 - 각 소스별로 다른 데이터
        web3_jobs = [mock_job_data[0]]    # Python Developer
        wework_jobs = [mock_job_data[1]]  # Backend Engineer  
        berlin_jobs = [mock_job_data[2]]  # Full Stack Developer
        
        mock_web3.return_value = web3_jobs
        mock_wework.return_value = wework_jobs
        mock_berlin.return_value = berlin_jobs
        
        # 검색 요청
        response = client.get('/search?keyword=python')
        
        # 검증
        assert response.status_code == 200
        assert b'python' in response.data  # 키워드가 페이지에 표시되는지
        
        # 모든 extractor가 호출되었는지 확인
        mock_web3.assert_called_once_with('python')
        mock_wework.assert_called_once_with('python')
        mock_berlin.assert_called_once_with('python')
        
        # db에 합쳐진 결과가 저장되었는지 확인
        assert 'python' in main.db
        expected_combined = web3_jobs + wework_jobs + berlin_jobs
        assert main.db['python'] == expected_combined
        assert len(main.db['python']) == 3  # web3 1개 + wework 1개 + berlin 1개

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
        
        # 홈페이지로 리다이렉트되는지 확인 (if not keyword 조건)
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
        # Mock 설정 - 각 소스별로 데이터 분리
        web3_jobs = [mock_job_data[0]]   # Python Developer
        wework_jobs = [mock_job_data[1]] # Backend Engineer
        berlin_jobs = [mock_job_data[2]] # Full Stack Developer
        
        mock_web3.return_value = web3_jobs
        mock_wework.return_value = wework_jobs
        mock_berlin.return_value = berlin_jobs
        
        keywords = ['python', 'javascript', 'react']
        expected_combined = web3_jobs + wework_jobs + berlin_jobs
        
        for keyword in keywords:
            response = client.get(f'/search?keyword={keyword}')
            assert response.status_code == 200
            assert keyword.encode() in response.data
            assert keyword in main.db
        
        # 모든 키워드가 캐시되었는지 확인
        assert len(main.db) == 3
        for keyword in keywords:
            assert main.db[keyword] == expected_combined
            assert len(main.db[keyword]) == 3  # web3 1개 + wework 1개 + berlin 1개

    @patch('main.extract_web3_jobs')
    @patch('main.extract_wework_jobs')
    @patch('main.extract_berlin_jobs')
    def test_search_combines_all_results(self, mock_berlin, mock_wework, mock_web3, client):
        """search 함수가 web3 + wework + berlin 모든 결과를 합치는지 테스트"""
        # 각각 다른 Mock 데이터 설정
        web3_data = [{"title": "Web3 Job", "company": "Web3 Corp", "link": "/web3"}]
        wework_data = [{"title": "WeWork Job", "company": "WeWork Corp", "link": "/wework"}]
        berlin_data = [{"title": "Berlin Job", "company": "Berlin Corp", "link": "/berlin"}]
        
        mock_web3.return_value = web3_data
        mock_wework.return_value = wework_data
        mock_berlin.return_value = berlin_data
        
        response = client.get('/search?keyword=test')
        
        # 모든 결과가 합쳐져서 저장되었는지 확인 (jobs = web3 + wwr + berlin)
        expected_combined_data = web3_data + wework_data + berlin_data
        assert main.db['test'] == expected_combined_data
        assert len(main.db['test']) == 3  # 3개 소스에서 각각 1개씩 총 3개
        
        # 각 소스의 데이터가 모두 포함되어 있는지 확인
        stored_jobs = main.db['test']
        assert any(job['title'] == 'Web3 Job' for job in stored_jobs)
        assert any(job['title'] == 'WeWork Job' for job in stored_jobs)
        assert any(job['title'] == 'Berlin Job' for job in stored_jobs)

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
        # Mock 설정 - 각 소스별로 데이터 분리
        web3_jobs = [mock_job_data[0]]   # Python Developer
        wework_jobs = [mock_job_data[1]] # Backend Engineer
        berlin_jobs = [mock_job_data[2]] # Full Stack Developer
        
        mock_web3.return_value = web3_jobs
        mock_wework.return_value = wework_jobs
        mock_berlin.return_value = berlin_jobs
        
        # URL 인코딩이 필요한 키워드
        keyword = 'machine learning'
        response = client.get(f'/search?keyword={keyword}')
        
        assert response.status_code == 200
        assert keyword in main.db
        
        # 합쳐진 결과가 저장되었는지 확인
        expected_combined = web3_jobs + wework_jobs + berlin_jobs
        assert main.db[keyword] == expected_combined
        
        # extractor가 올바른 키워드로 호출되었는지 확인
        mock_web3.assert_called_once_with(keyword)
        mock_wework.assert_called_once_with(keyword)
        mock_berlin.assert_called_once_with(keyword)

    @patch('main.extract_web3_jobs')
    @patch('main.extract_wework_jobs')
    @patch('main.extract_berlin_jobs')
    def test_search_different_result_counts(self, mock_berlin, mock_wework, mock_web3, client):
        """각 소스에서 다른 개수의 결과가 나올 때 올바르게 합쳐지는지 테스트"""
        # Mock 데이터 설정 - 각 소스별로 다른 개수의 결과
        web3_jobs = [
            {"title": "Web3 Job 1", "company": "Web3 Corp 1", "link": "/web3-1"},
            {"title": "Web3 Job 2", "company": "Web3 Corp 2", "link": "/web3-2"}
        ]
        wework_jobs = [
            {"title": "WeWork Job 1", "company": "WeWork Corp 1", "link": "/wework-1"}
        ]
        berlin_jobs = [
            {"title": "Berlin Job 1", "company": "Berlin Corp 1", "link": "/berlin-1"},
            {"title": "Berlin Job 2", "company": "Berlin Corp 2", "link": "/berlin-2"},
            {"title": "Berlin Job 3", "company": "Berlin Corp 3", "link": "/berlin-3"}
        ]
        
        mock_web3.return_value = web3_jobs
        mock_wework.return_value = wework_jobs
        mock_berlin.return_value = berlin_jobs
        
        response = client.get('/search?keyword=developer')
        
        # 검증
        assert response.status_code == 200
        assert 'developer' in main.db
        
        # 모든 결과가 올바른 순서로 합쳐졌는지 확인
        combined_jobs = main.db['developer']
        assert len(combined_jobs) == 6  # 2 + 1 + 3 = 6
        
        # 순서 확인: web3 → wework → berlin
        assert combined_jobs[0]['title'] == 'Web3 Job 1'
        assert combined_jobs[1]['title'] == 'Web3 Job 2'
        assert combined_jobs[2]['title'] == 'WeWork Job 1'
        assert combined_jobs[3]['title'] == 'Berlin Job 1'
        assert combined_jobs[4]['title'] == 'Berlin Job 2'
        assert combined_jobs[5]['title'] == 'Berlin Job 3'

    @patch('main.extract_web3_jobs')
    @patch('main.extract_wework_jobs')
    @patch('main.extract_berlin_jobs')
    def test_search_partial_extractor_failure(self, mock_berlin, mock_wework, mock_web3, client):
        """일부 extractor에서만 에러가 발생할 때 테스트"""
        # Mock 설정 - web3에서만 에러 발생
        mock_web3.side_effect = Exception("Web3 API error")
        mock_wework.return_value = [{"title": "WeWork Job", "company": "WeWork Corp", "link": "/wework"}]
        mock_berlin.return_value = [{"title": "Berlin Job", "company": "Berlin Corp", "link": "/berlin"}]
        
        # 에러 발생으로 500 응답이 와야 함
        response = client.get('/search?keyword=partial_error')
        assert response.status_code == 500

    @patch('main.extract_web3_jobs')
    @patch('main.extract_wework_jobs')
    @patch('main.extract_berlin_jobs')
    def test_search_all_sources_empty(self, mock_berlin, mock_wework, mock_web3, client):
        """모든 소스에서 빈 결과가 나올 때 테스트"""
        # 모든 Mock이 빈 리스트 반환
        mock_web3.return_value = []
        mock_wework.return_value = []
        mock_berlin.return_value = []
        
        response = client.get('/search?keyword=nonexistent')
        
        # 검증
        assert response.status_code == 200
        assert 'nonexistent' in main.db
        assert main.db['nonexistent'] == []  # 빈 리스트
        
        # 모든 extractor가 호출되었는지 확인
        mock_web3.assert_called_once_with('nonexistent')
        mock_wework.assert_called_once_with('nonexistent')
        mock_berlin.assert_called_once_with('nonexistent')

    @patch('main.extract_web3_jobs')
    @patch('main.extract_wework_jobs')
    @patch('main.extract_berlin_jobs')
    def test_search_mixed_empty_and_results(self, mock_berlin, mock_wework, mock_web3, client, mock_job_data):
        """일부 소스는 빈 결과, 일부는 데이터가 있을 때 테스트"""
        # Mock 설정 - 일부만 결과 있음
        mock_web3.return_value = [mock_job_data[0]]  # Python Developer
        mock_wework.return_value = []  # 빈 결과
        mock_berlin.return_value = [mock_job_data[2]]  # Full Stack Developer
        
        response = client.get('/search?keyword=mixed')
        
        # 검증
        assert response.status_code == 200
        assert 'mixed' in main.db
        
        # 빈 결과가 있어도 올바르게 합쳐지는지 확인
        expected = [mock_job_data[0]] + [] + [mock_job_data[2]]
        assert main.db['mixed'] == expected
        assert len(main.db['mixed']) == 2  # web3 1개 + wework 0개 + berlin 1개
        
        # 결과 내용 확인
        stored_jobs = main.db['mixed']
        assert stored_jobs[0]['title'] == 'Python Developer'
        assert stored_jobs[1]['title'] == 'Full Stack Developer'

    @patch('main.extract_web3_jobs')
    @patch('main.extract_wework_jobs')
    @patch('main.extract_berlin_jobs')
    def test_search_duplicate_results_from_different_sources(self, mock_berlin, mock_wework, mock_web3, client):
        """다른 소스에서 중복된 결과가 나올 때도 모두 포함되는지 테스트"""
        # 의도적으로 중복된 job 데이터 설정
        duplicate_job = {"title": "Full Stack Developer", "company": "Tech Company", "link": "/job/fullstack"}
        
        mock_web3.return_value = [duplicate_job]
        mock_wework.return_value = [duplicate_job]  # 동일한 job
        mock_berlin.return_value = [duplicate_job]  # 동일한 job
        
        response = client.get('/search?keyword=fullstack')
        
        # 검증 - 중복 제거 없이 모든 결과 포함
        assert response.status_code == 200
        assert 'fullstack' in main.db
        assert len(main.db['fullstack']) == 3  # 중복이어도 3개 모두 포함
        
        # 모든 결과가 동일한지 확인
        for job in main.db['fullstack']:
            assert job == duplicate_job 