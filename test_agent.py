import os
import tempfile
import subprocess
import json
from typing import List, Dict, Any

class TestAgent:
    def __init__(self, ollama_client, gitlab_client, jenkins_client):
        self.ollama = ollama_client
        self.gitlab = gitlab_client
        self.jenkins = jenkins_client
        
    def fetch_tests_from_gitlab(self, project_id: str, branch: str = "main", test_path: str = "tests/") -> List[Dict]:
        """Pobiera pliki testowe z GitLab repository"""
        try:
            tests = self.gitlab.get_test_files(project_id, branch, test_path)
            return tests
        except Exception as e:
            raise Exception(f"Błąd pobierania testów z GitLab: {str(e)}")
    
    def run_tests_locally(self, tests: List[Dict]) -> Dict[str, Any]:
        """Uruchamia testy lokalnie"""
        try:
            # Utworzenie tymczasowego katalogu
            with tempfile.TemporaryDirectory() as temp_dir:
                # Zapisanie plików testowych
                for test in tests:
                    file_path = os.path.join(temp_dir, test['name'])
                    os.makedirs(os.path.dirname(file_path), exist_ok=True)
                    with open(file_path, 'w') as f:
                        f.write(test['content'])
                
                # Uruchomienie pytest
                result = subprocess.run(
                    ['python', '-m', 'pytest', temp_dir, '-v'],
                    capture_output=True,
                    text=True,
                    cwd=temp_dir
                )
                
                return {
                    'success': result.returncode == 0,
                    'output': result.stdout + result.stderr,
                    'return_code': result.returncode
                }
                
        except Exception as e:
            raise Exception(f"Błąd uruchamiania testów lokalnie: {str(e)}")
    
    def run_tests_on_jenkins(self, job_name: str, tests: List[Dict]) -> Dict[str, Any]:
        """Uruchamia testy na Jenkins"""
        try:
            # Przygotowanie parametrów dla job'a
            params = {
                'TESTS_DATA': json.dumps(tests),
                'RUN_TESTS': 'true'
            }
            
            # Uruchomienie job'a
            build_number = self.jenkins.trigger_build(job_name, params)
            
            # Oczekiwanie na zakończenie
            status = self.jenkins.wait_for_build(job_name, build_number)
            
            # Pobranie logów
            logs = self.jenkins.get_build_logs(job_name, build_number)
            
            return {
                'build_number': build_number,
                'status': status,
                'logs': logs,
                'success': status == 'SUCCESS'
            }
            
        except Exception as e:
            raise Exception(f"Błąd uruchamiania testów na Jenkins: {str(e)}")
    
    def analyze_jenkins_logs(self, jenkins_result: Dict[str, Any]) -> Dict[str, Any]:
        """Analizuje logi Jenkins przy użyciu AI"""
        try:
            logs = jenkins_result['logs']
            
            prompt = f"""
            Przeanalizuj logi z wykonania testów na Jenkins i zidentyfikuj problemy:
            
            Status buildu: {jenkins_result['status']}
            
            Logi:
            {logs}
            
            Proszę o:
            1. Krótkie podsumowanie co się stało
            2. Lista konkretnych błędów (jeśli są)
            3. Sugestie jak naprawić problemy
            
            Odpowiedz w formacie JSON:
            {{
                "summary": "krótkie podsumowanie",
                "errors": ["lista", "błędów"],
                "suggestions": ["lista", "sugestii"]
            }}
            """
            
            response = self.ollama.generate(prompt)
            
            try:
                analysis = json.loads(response)
            except json.JSONDecodeError:
                # Fallback jeśli AI nie zwróci poprawnego JSON
                analysis = {
                    "summary": "Analiza AI nie zwróciła poprawnego formatu JSON",
                    "errors": ["Nie udało się sparsować odpowiedzi AI"],
                    "suggestions": ["Sprawdź logi ręcznie"]
                }
            
            return analysis
            
        except Exception as e:
            raise Exception(f"Błąd analizy logów: {str(e)}")
    
    def generate_test_fixes(self, tests: List[Dict], analysis: Dict[str, Any]) -> List[Dict]:
        """Generuje poprawki dla testów na podstawie analizy"""
        try:
            fixes = []
            
            for test in tests:
                if any(error for error in analysis['errors'] if test['name'] in error):
                    prompt = f"""
                    Na podstawie analizy błędów:
                    Błędy: {analysis['errors']}
                    Sugestie: {analysis['suggestions']}
                    
                    Popraw następujący test:
                    
                    Nazwa pliku: {test['name']}
                    Kod:
                    {test['content']}
                    
                    Zwróć poprawiony kod wraz z opisem problemu.
                    Format odpowiedzi:
                    PROBLEM: opis problemu
                    FIXED_CODE:
                    [poprawiony kod]
                    """
                    
                    response = self.ollama.generate(prompt)
                    
                    # Parsowanie odpowiedzi
                    if "PROBLEM:" in response and "FIXED_CODE:" in response:
                        parts = response.split("FIXED_CODE:")
                        problem = parts[0].replace("PROBLEM:", "").strip()
                        fixed_code = parts[1].strip()
                        
                        fixes.append({
                            'file': test['name'],
                            'problem': problem,
                            'original_code': test['content'],
                            'fixed_code': fixed_code
                        })
            
            return fixes
            
        except Exception as e:
            raise Exception(f"Błąd generowania poprawek: {str(e)}")
    
    def apply_fix(self, fix: Dict[str, Any]) -> bool:
        """Aplikuje poprawkę do pliku"""
        try:
            # W rzeczywistej implementacji można by tu zaktualizować pliki w repo GitLab
            # Na razie tylko logujemy
            print(f"Zastosowano poprawkę dla {fix['file']}")
            return True
            
        except Exception as e:
            raise Exception(f"Błąd aplikowania poprawki: {str(e)}")
    
    def update_gitlab_file(self, project_id: str, file_path: str, content: str, commit_message: str) -> bool:
        """Aktualizuje plik w GitLab repository"""
        try:
            return self.gitlab.update_file(project_id, file_path, content, commit_message)
        except Exception as e:
            raise Exception(f"Błąd aktualizacji pliku w GitLab: {str(e)}")
    
    def create_merge_request(self, project_id: str, title: str, description: str, source_branch: str) -> str:
        """Tworzy merge request w GitLab"""
        try:
            return self.gitlab.create_merge_request(project_id, title, description, source_branch)
        except Exception as e:
            raise Exception(f"Błąd tworzenia merge request: {str(e)}") 