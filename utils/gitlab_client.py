import gitlab
from typing import List, Dict
import base64

class GitLabClient:
    def __init__(self, token: str, url: str = "https://gitlab.com"):
        self.gl = gitlab.Gitlab(url, private_token=token)
        
    def get_test_files(self, project_id: str, branch: str = "main", test_path: str = "tests/") -> List[Dict]:
        """Pobiera pliki testowe z GitLab repository"""
        try:
            project = self.gl.projects.get(project_id)
            
            # Pobieranie zawartości katalogu testów
            test_files = []
            
            # Rekurencyjne przeszukiwanie katalogów
            def process_directory(path: str = test_path):
                try:
                    items = project.repository_tree(path=path, ref=branch, recursive=True)
                    
                    for item in items:
                        if item['type'] == 'blob' and item['path'].endswith(('.py', '_test.py', 'test_.py')):
                            # Pobieranie zawartości pliku
                            try:
                                file_content = project.files.get(file_path=item['path'], ref=branch)
                                content = base64.b64decode(file_content.content).decode('utf-8')
                                
                                test_files.append({
                                    'name': item['path'],
                                    'content': content,
                                    'id': item['id'],
                                    'size': file_content.size
                                })
                            except Exception as e:
                                print(f"Błąd pobierania pliku {item['path']}: {e}")
                                
                except Exception as e:
                    print(f"Błąd przeglądania katalogu {path}: {e}")
            
            process_directory()
            return test_files
            
        except Exception as e:
            raise Exception(f"Błąd pobierania plików z GitLab: {str(e)}")
    
    def update_file(self, project_id: str, file_path: str, content: str, 
                   commit_message: str, branch: str = "main") -> bool:
        """Aktualizuje plik w repository"""
        try:
            project = self.gl.projects.get(project_id)
            
            # Sprawdzenie czy plik istnieje
            try:
                file_obj = project.files.get(file_path=file_path, ref=branch)
                # Aktualizacja istniejącego pliku
                file_obj.content = base64.b64encode(content.encode('utf-8')).decode('utf-8')
                file_obj.save(branch=branch, commit_message=commit_message)
            except gitlab.exceptions.GitlabGetError:
                # Utworzenie nowego pliku
                file_data = {
                    'file_path': file_path,
                    'branch': branch,
                    'content': content,
                    'commit_message': commit_message
                }
                project.files.create(file_data)
            
            return True
            
        except Exception as e:
            raise Exception(f"Błąd aktualizacji pliku na GitLab: {str(e)}")
    
    def create_merge_request(self, project_id: str, title: str, description: str, 
                           source_branch: str, target_branch: str = "main") -> str:
        """Tworzy merge request"""
        try:
            project = self.gl.projects.get(project_id)
            
            mr_data = {
                'source_branch': source_branch,
                'target_branch': target_branch,
                'title': title,
                'description': description
            }
            
            mr = project.mergerequests.create(mr_data)
            
            return mr.web_url
            
        except Exception as e:
            raise Exception(f"Błąd tworzenia merge request: {str(e)}")
    
    def get_project_info(self, project_id: str) -> Dict:
        """Pobiera informacje o projekcie"""
        try:
            project = self.gl.projects.get(project_id)
            return {
                'id': project.id,
                'name': project.name,
                'path': project.path,
                'web_url': project.web_url,
                'default_branch': project.default_branch
            }
            
        except Exception as e:
            raise Exception(f"Błąd pobierania informacji o projekcie: {str(e)}")
    
    def list_projects(self) -> List[Dict]:
        """Pobiera listę dostępnych projektów"""
        try:
            projects = self.gl.projects.list(owned=True)
            return [{
                'id': p.id,
                'name': p.name,
                'path': p.path_with_namespace,
                'web_url': p.web_url
            } for p in projects]
            
        except Exception as e:
            raise Exception(f"Błąd pobierania listy projektów: {str(e)}") 