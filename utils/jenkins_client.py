import jenkins
import time
import requests
from typing import Dict, Any, Optional

class JenkinsClient:
    def __init__(self, url: str, username: str, password: str):
        self.url = url.rstrip('/')
        self.username = username
        self.password = password
        self.server = jenkins.Jenkins(url, username=username, password=password)
        
    def test_connection(self) -> Dict[str, Any]:
        """Testuje połączenie z Jenkins"""
        try:
            user_info = self.server.get_whoami()
            version = self.server.get_version()
            return {
                'connected': True,
                'user': user_info,
                'version': version,
                'message': f"Połączono jako {user_info.get('fullName', username)} (Jenkins {version})"
            }
        except Exception as e:
            return {
                'connected': False,
                'error': str(e),
                'message': f"Błąd połączenia z Jenkins: {str(e)}"
            }
    
    def job_exists(self, job_name: str) -> bool:
        """Sprawdza czy job istnieje"""
        try:
            self.server.get_job_info(job_name)
            return True
        except jenkins.NotFoundException:
            return False
        except Exception:
            return False
        
    def trigger_build(self, job_name: str, parameters: Optional[Dict] = None) -> int:
        """Uruchamia build Jenkins job'a"""
        try:
            # Sprawdzenie czy job istnieje
            if not self.job_exists(job_name):
                available_jobs = [job['name'] for job in self.get_all_jobs()]
                raise Exception(f"Job '{job_name}' nie istnieje. Dostępne job'y: {available_jobs[:10]}")
            
            # Pobranie informacji o job'ie
            job_info = self.server.get_job_info(job_name)
            next_build_number = job_info.get('nextBuildNumber', 1)
            
            # Uruchomienie buildu
            if parameters:
                self.server.build_job(job_name, parameters)
            else:
                self.server.build_job(job_name)
            
            return next_build_number
            
        except jenkins.JenkinsException as e:
            raise Exception(f"Błąd Jenkins API: {str(e)}")
        except Exception as e:
            raise Exception(f"Błąd uruchamiania job'a '{job_name}': {str(e)}")
    
    def wait_for_build(self, job_name: str, build_number: int, timeout: int = 300) -> str:
        """Oczekuje na zakończenie buildu"""
        try:
            start_time = time.time()
            
            print(f"Oczekiwanie na build #{build_number} job'a '{job_name}'...")
            
            while time.time() - start_time < timeout:
                try:
                    build_info = self.server.get_build_info(job_name, build_number)
                    
                    if not build_info.get('building', False):
                        result = build_info.get('result', 'UNKNOWN')
                        print(f"Build #{build_number} zakończony ze statusem: {result}")
                        return result
                    
                    print(f"Build #{build_number} nadal trwa...")
                    time.sleep(10)  # Czeka 10 sekund przed kolejnym sprawdzeniem
                    
                except jenkins.NotFoundException:
                    # Build jeszcze nie istnieje - czeka krócej
                    print(f"Build #{build_number} jeszcze nie rozpoczęty...")
                    time.sleep(5)
                    continue
                except Exception as e:
                    print(f"Błąd sprawdzania statusu buildu: {e}")
                    time.sleep(5)
                    continue
            
            raise Exception(f"Timeout ({timeout}s) oczekiwania na build #{build_number}")
            
        except Exception as e:
            raise Exception(f"Błąd oczekiwania na build: {str(e)}")
    
    def get_build_logs(self, job_name: str, build_number: int) -> str:
        """Pobiera logi z buildu"""
        try:
            if not self.job_exists(job_name):
                raise Exception(f"Job '{job_name}' nie istnieje")
            
            logs = self.server.get_build_console_output(job_name, build_number)
            return logs
            
        except jenkins.NotFoundException:
            raise Exception(f"Build #{build_number} dla job'a '{job_name}' nie istnieje")
        except Exception as e:
            raise Exception(f"Błąd pobierania logów build #{build_number}: {str(e)}")
    
    def get_job_info(self, job_name: str) -> Dict[str, Any]:
        """Pobiera informacje o job'ie"""
        try:
            return self.server.get_job_info(job_name)
            
        except jenkins.NotFoundException:
            raise Exception(f"Job '{job_name}' nie został znaleziony")
        except jenkins.JenkinsException as e:
            raise Exception(f"Błąd Jenkins API dla job'a '{job_name}': {str(e)}")
        except Exception as e:
            raise Exception(f"Błąd pobierania informacji o job'ie '{job_name}': {str(e)}")
    
    def create_job(self, job_name: str, config_xml: str) -> bool:
        """Tworzy nowy job w Jenkins"""
        try:
            if self.job_exists(job_name):
                raise Exception(f"Job '{job_name}' już istnieje")
                
            self.server.create_job(job_name, config_xml)
            return True
            
        except jenkins.JenkinsException as e:
            raise Exception(f"Błąd Jenkins API podczas tworzenia job'a: {str(e)}")
        except Exception as e:
            raise Exception(f"Błąd tworzenia job'a '{job_name}': {str(e)}")
    
    def get_all_jobs(self) -> list:
        """Pobiera listę wszystkich job'ów"""
        try:
            jobs = self.server.get_all_jobs()
            return jobs
            
        except jenkins.JenkinsException as e:
            raise Exception(f"Błąd Jenkins API: {str(e)}")
        except Exception as e:
            raise Exception(f"Błąd pobierania listy job'ów: {str(e)}")
    
    def get_build_info(self, job_name: str, build_number: int) -> Dict[str, Any]:
        """Pobiera informacje o konkretnym buildzie"""
        try:
            return self.server.get_build_info(job_name, build_number)
            
        except jenkins.NotFoundException:
            raise Exception(f"Build #{build_number} dla job'a '{job_name}' nie istnieje")
        except Exception as e:
            raise Exception(f"Błąd pobierania informacji o buildzie: {str(e)}") 
