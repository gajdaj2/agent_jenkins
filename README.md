# Jenkins Test Agent z Gemma3:7b

🤖 Inteligentny agent AI wykorzystujący model Gemma3:7b na Ollama do automatycznego zarządzania testami między GitHubem a Jenkinsem.

## ✨ Funkcje

- 📥 **Pobieranie testów z GitHub** - Automatyczne pobieranie plików testowych z repozytoriów
- 🏃 **Uruchamianie testów** - Lokalne i zdalne wykonanie testów na Jenkins
- 📊 **Analiza logów** - Inteligentna analiza wyników testów używając AI
- 🔧 **Automatyczne poprawki** - Generowanie i aplikowanie poprawek na podstawie błędów

## 🚀 Instalacja

### Wymagania wstępne

1. **Python 3.8+**
2. **Ollama z modelem Gemma3:7b**
   ```bash
   # Instalacja Ollama
   curl -fsSL https://ollama.ai/install.sh | sh
   
   # Pobranie modelu Gemma3:7b
   ollama pull gemma2:7b
   ```
3. **Dostęp do Jenkins** z API token
4. **GitHub token** z odpowiednimi uprawnieniami

### Instalacja aplikacji

1. **Klonowanie i instalacja zależności:**
   ```bash
   git clone <repository-url>
   cd jenkins_agent
   pip install -r requirements.txt
   ```

2. **Konfiguracja zmiennych środowiskowych:**
   ```bash
   cp .env.example .env
   # Edytuj plik .env z własnymi danymi
   ```

3. **Uruchomienie aplikacji:**
   ```bash
   streamlit run app.py
   ```

## 📋 Konfiguracja

### GitHub Token

1. Przejdź do GitHub Settings → Developer settings → Personal access tokens
2. Utwórz nowy token z uprawnieniami:
   - `repo` (pełny dostęp do repozytoriów)
   - `workflow` (dostęp do GitHub Actions)

### Jenkins API Token

1. Zaloguj się do Jenkins
2. Przejdź do User → Configure → API Token
3. Wygeneruj nowy token

### Ollama

Upewnij się, że Ollama działa lokalnie:
```bash
ollama serve
ollama list  # Sprawdź dostępne modele
```

## 🎯 Użytkowanie

### 1. Konfiguracja agenta

W panelu bocznym wprowadź:
- URL i dane dostępowe do Ollama
- GitHub token i URL repozytorium
- Dane dostępowe do Jenkins

### 2. Pobieranie testów

- Wprowadź szczegóły repozytorium (właściciel, nazwa, branch)
- Kliknij "Pobierz Testy"
- Przejrzyj pobrane pliki testowe

### 3. Uruchamianie testów

**Lokalnie:**
- Testy są uruchamiane w izolowanym środowisku
- Wyniki wyświetlane w czasie rzeczywistym

**Na Jenkins:**
- Wprowadź nazwę job'a Jenkins
- Agent automatycznie śledzi status buildu

### 4. Analiza i poprawki

- AI analizuje logi z niepowodzeń
- Generuje konkretne sugestie poprawek
- Oferuje zautomatyzowane aplikowanie zmian

## 🏗️ Architektura

```
jenkins_agent/
├── app.py                 # Główna aplikacja Streamlit
├── agents/
│   └── test_agent.py     # Główna logika agenta
├── utils/
│   ├── ollama_client.py  # Klient Ollama
│   ├── github_client.py  # Klient GitHub API
│   └── jenkins_client.py # Klient Jenkins API
├── requirements.txt      # Zależności Python
├── .env.example         # Przykład konfiguracji
└── README.md           # Dokumentacja
```

## 🔧 Konfiguracja Jenkins Job

Przykładowy Jenkinsfile dla job'a testowego:

```groovy
pipeline {
    agent any
    
    parameters {
        text(name: 'TESTS_DATA', defaultValue: '[]', description: 'JSON with test files')
        booleanParam(name: 'RUN_TESTS', defaultValue: false, description: 'Run tests')
    }
    
    stages {
        stage('Setup') {
            steps {
                script {
                    if (params.RUN_TESTS) {
                        // Rozpakowanie testów z parametru TESTS_DATA
                        def tests = readJSON text: params.TESTS_DATA
                        
                        tests.each { test ->
                            writeFile file: test.name, text: test.content
                        }
                    }
                }
            }
        }
        
        stage('Install Dependencies') {
            steps {
                sh 'pip install pytest'
            }
        }
        
        stage('Run Tests') {
            steps {
                sh 'python -m pytest -v --tb=short'
            }
        }
    }
    
    post {
        always {
            archiveArtifacts artifacts: '**/*.py', allowEmptyArchive: true
            publishTestResults testResultsPattern: 'test-results.xml'
        }
    }
}
```

## 🚨 Rozwiązywanie problemów

### Ollama nie odpowiada
```bash
# Sprawdź status Ollama
ollama list
ollama ps

# Restart Ollama
pkill ollama
ollama serve
```

### Błędy autoryzacji Jenkins
- Sprawdź poprawność URL, nazwy użytkownika i API token
- Upewnij się, że użytkownik ma uprawnienia do uruchamiania job'ów

### Błędy GitHub API
- Sprawdź ważność token'a
- Upewnij się, że token ma odpowiednie uprawnienia

## 🤝 Wkład w rozwój

1. Fork repozytorium
2. Utwórz branch dla nowej funkcji
3. Wprowadź zmiany i dodaj testy
4. Utwórz Pull Request

## 📄 Licencja

MIT License - zobacz plik LICENSE dla szczegółów.

## 🙋‍♀️ Wsparcie

W razie problemów:
1. Sprawdź sekcję rozwiązywania problemów
2. Otwórz issue na GitHub
3. Dołącz logi z błędami i konfigurację (bez tokenów!) 