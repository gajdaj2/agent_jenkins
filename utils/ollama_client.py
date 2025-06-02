import requests
import json
from typing import Optional

class OllamaClient:
    def __init__(self, host: str = "http://localhost:11434", model: str = "gemma2:7b"):
        self.host = host.rstrip('/')
        self.model = model
        
    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Generuje odpowiedź używając modelu Ollama"""
        try:
            url = f"{self.host}/api/generate"
            
            data = {
                "model": self.model,
                "prompt": prompt,
                "stream": False
            }
            
            if system_prompt:
                data["system"] = system_prompt
            
            response = requests.post(url, json=data, timeout=300)
            response.raise_for_status()
            
            result = response.json()
            return result.get('response', '')
            
        except requests.exceptions.RequestException as e:
            raise Exception(f"Błąd komunikacji z Ollama: {str(e)}")
        except json.JSONDecodeError as e:
            raise Exception(f"Błąd parsowania odpowiedzi Ollama: {str(e)}")
    
    def check_model_availability(self) -> bool:
        """Sprawdza czy model jest dostępny"""
        try:
            url = f"{self.host}/api/tags"
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            models = response.json().get('models', [])
            return any(model['name'] == self.model for model in models)
            
        except Exception:
            return False
    
    def pull_model(self) -> bool:
        """Pobiera model jeśli nie jest dostępny"""
        try:
            url = f"{self.host}/api/pull"
            data = {"name": self.model}
            
            response = requests.post(url, json=data, timeout=600)
            response.raise_for_status()
            
            return True
            
        except Exception as e:
            raise Exception(f"Błąd pobierania modelu: {str(e)}") 