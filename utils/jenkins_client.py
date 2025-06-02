import jenkins
import time
from typing import Dict, Any, Optional

class JenkinsClient:
    def __init__(self, url: str, username: str, password: str):
        self.server = jenkins.Jenkins(url, username=username, password=password)
        
    def trigger_build(self, job_name: str, parameters: Optional[Dict] = None) -> int:
        """Uruchamia build Jenkins job'a"""
        try:
            if parameters:
                next_build_number = self.server.get_job_info(job_name)['nextBuildNumber']
                self.server.build_job(job_name, parameters)
            else:
                next_build_number = self.server.get_job_info(job_name)['nextBuildNumber']
                self.server.build_job(job_name)
            
            return next_build_number
            
        except Exception as e:
            raise Exception(f"Błąd uruchamiania job'a Jenkins: {str(e)}")
    
    def wait_for_build(self, job_name: str, build_number: int, timeout: int = 300) -> str:
        """Oczekuje na zakończenie buildu"""
        try:
            start_time = time.time()
            
            while time.time() - start_time < timeout:
                try:
                    build_info = self.server.get_build_info(job_name, build_number)
                    
                    if not build_info['building']:
                        return build_info['result']
                    
                    time.sleep(10)  # Czeka 10 sekund przed kolejnym sprawdzeniem
                    
                except jenkins.NotFoundException:
                    # Build jeszcze nie istnieje
                    time.sleep(5)
                    continue
            
            raise Exception(f"Timeout oczekiwania na build {build_number}")
            
        except Exception as e:
            raise Exception(f"Błąd oczekiwania na build: {str(e)}")
    
    def get_build_logs(self, job_name: str, build_number: int) -> str:
        """Pobiera logi z buildu"""
        try:
            return self.server.get_build_console_output(job_name, build_number)
            
        except Exception as e:
            raise Exception(f"Błąd pobierania logów: {str(e)}")
    
    def get_job_info(self, job_name: str) -> Dict[str, Any]:
        """Pobiera informacje o job'ie"""
        try:
            return self.server.get_job_info(job_name)
            
        except Exception as e:
            raise Exception(f"Błąd pobierania informacji o job'ie: {str(e)}")
    
    def create_job(self, job_name: str, config_xml: str) -> bool:
        """Tworzy nowy job w Jenkins"""
        try:
            self.server.create_job(job_name, config_xml)
            return True
            
        except Exception as e:
            raise Exception(f"Błąd tworzenia job'a: {str(e)}")
    
    def get_all_jobs(self) -> list:
        """Pobiera listę wszystkich job'ów"""
        try:
            return self.server.get_all_jobs()
            
        except Exception as e:
            raise Exception(f"Błąd pobierania listy job'ów: {str(e)}") 