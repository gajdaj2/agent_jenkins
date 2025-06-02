from github import Github
from typing import List, Dict
import base64

class GitHubClient:
    def __init__(self, token: str):
        self.github = Github(token)
        
    def get_test_files(self, owner: str, repo_name: str, branch: str = "main", test_path: str = "tests/") -> List[Dict]:
        """Pobiera pliki testowe z repository"""
        try:
            repo = self.github.get_repo(f"{owner}/{repo_name}")
            
            # Pobieranie zawartości katalogu testów
            contents = repo.get_contents(test_path, ref=branch)
            
            test_files = []
            
            # Rekurencyjne przeszukiwanie katalogów
            def process_contents(contents_list, current_path=""):
                for content in contents_list:
                    if content.type == "file" and content.name.endswith(('.py', '_test.py', 'test_.py')):
                        # Dekodowanie zawartości pliku
                        file_content = base64.b64decode(content.content).decode('utf-8')
                        
                        test_files.append({
                            'name': content.path,
                            'content': file_content,
                            'sha': content.sha,
                            'size': content.size
                        })
                    
                    elif content.type == "dir":
                        # Rekurencyjne przeszukiwanie podkatalogów
                        sub_contents = repo.get_contents(content.path, ref=branch)
                        process_contents(sub_contents, content.path)
            
            if isinstance(contents, list):
                process_contents(contents)
            else:
                process_contents([contents])
            
            return test_files
            
        except Exception as e:
            raise Exception(f"Błąd pobierania plików z GitHub: {str(e)}")
    
    def update_file(self, owner: str, repo_name: str, file_path: str, content: str, 
                   commit_message: str, branch: str = "main") -> bool:
        """Aktualizuje plik w repository"""
        try:
            repo = self.github.get_repo(f"{owner}/{repo_name}")
            
            # Sprawdzenie czy plik istnieje
            try:
                file = repo.get_contents(file_path, ref=branch)
                # Aktualizacja istniejącego pliku
                repo.update_file(
                    path=file_path,
                    message=commit_message,
                    content=content,
                    sha=file.sha,
                    branch=branch
                )
            except:
                # Utworzenie nowego pliku
                repo.create_file(
                    path=file_path,
                    message=commit_message,
                    content=content,
                    branch=branch
                )
            
            return True
            
        except Exception as e:
            raise Exception(f"Błąd aktualizacji pliku na GitHub: {str(e)}")
    
    def create_pull_request(self, owner: str, repo_name: str, title: str, 
                          body: str, head_branch: str, base_branch: str = "main") -> str:
        """Tworzy pull request"""
        try:
            repo = self.github.get_repo(f"{owner}/{repo_name}")
            
            pr = repo.create_pull(
                title=title,
                body=body,
                head=head_branch,
                base=base_branch
            )
            
            return pr.html_url
            
        except Exception as e:
            raise Exception(f"Błąd tworzenia pull request: {str(e)}") 