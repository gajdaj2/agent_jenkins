import streamlit as st
import os
from dotenv import load_dotenv
from agents.test_agent import TestAgent
from utils.gitlab_client import GitLabClient
from utils.jenkins_client import JenkinsClient
from utils.ollama_client import OllamaClient

# Ładowanie zmiennych środowiskowych
load_dotenv()

def main():
    st.set_page_config(
        page_title="Jenkins Test Agent",
        page_icon="🤖",
        layout="wide"
    )
    
    st.title("🤖 Jenkins Test Agent z Gemma3:7b")
    st.markdown("Agent AI do zarządzania testami na GitLabie i Jenkinsie")
    
    # Sidebar z konfiguracją
    st.sidebar.header("⚙️ Konfiguracja")
    
    # Konfiguracja Ollama
    st.sidebar.subheader("🧠 Ollama")
    ollama_host = st.sidebar.text_input("Host Ollama", value="http://localhost:11434")
    model_name = st.sidebar.text_input("Model", value="gemma2:7b")
    
    # Test połączenia Ollama
    if st.sidebar.button("🔍 Testuj Ollama"):
        with st.sidebar.spinner("Testowanie Ollama..."):
            try:
                ollama_client = OllamaClient(ollama_host, model_name)
                if ollama_client.check_model_availability():
                    st.sidebar.success(f"✅ Model {model_name} jest dostępny!")
                else:
                    st.sidebar.warning(f"⚠️ Model {model_name} nie jest dostępny")
                    if st.sidebar.button("⬇️ Pobierz model"):
                        ollama_client.pull_model()
                        st.sidebar.success("Model pobrany!")
            except Exception as e:
                st.sidebar.error(f"❌ Błąd Ollama: {e}")
    
    # Konfiguracja GitLab
    st.sidebar.subheader("🦊 GitLab")
    gitlab_token = st.sidebar.text_input("GitLab Token", type="password")
    gitlab_url = st.sidebar.text_input("GitLab URL", value="https://gitlab.com")
    project_id = st.sidebar.text_input("Project ID (lub owner/repo)")
    
    # Test połączenia GitLab
    if gitlab_token and st.sidebar.button("🔍 Testuj GitLab"):
        with st.sidebar.spinner("Testowanie GitLab..."):
            try:
                gitlab_client = GitLabClient(gitlab_token, gitlab_url)
                projects = gitlab_client.list_projects()
                st.sidebar.success(f"✅ Połączono! Znaleziono {len(projects)} projektów")
                if projects:
                    project_names = [p['path'] for p in projects[:3]]
                    st.sidebar.info(f"Przykłady: {', '.join(project_names)}")
            except Exception as e:
                st.sidebar.error(f"❌ Błąd GitLab: {e}")
    
    # Konfiguracja Jenkins
    st.sidebar.subheader("🏗️ Jenkins")
    jenkins_url = st.sidebar.text_input("Jenkins URL")
    jenkins_user = st.sidebar.text_input("Jenkins User")
    jenkins_token = st.sidebar.text_input("Jenkins Token", type="password")
    
    # Test połączenia Jenkins
    if jenkins_url and jenkins_user and jenkins_token:
        if st.sidebar.button("🔍 Testuj połączenie Jenkins"):
            with st.sidebar.spinner("Testowanie połączenia..."):
                try:
                    jenkins_client = JenkinsClient(jenkins_url, jenkins_user, jenkins_token)
                    connection_test = jenkins_client.test_connection()
                    
                    if connection_test['connected']:
                        st.sidebar.success(connection_test['message'])
                        
                        # Pokaż dostępne job'y
                        try:
                            jobs = jenkins_client.get_all_jobs()
                            if jobs:
                                st.sidebar.info(f"📋 Znaleziono {len(jobs)} job'ów")
                                job_names = [job['name'] for job in jobs[:5]]
                                st.sidebar.write("Przykładowe job'y:", ", ".join(job_names))
                        except Exception as e:
                            st.sidebar.warning(f"Nie udało się pobrać listy job'ów: {e}")
                    else:
                        st.sidebar.error(connection_test['message'])
                        
                except Exception as e:
                    st.sidebar.error(f"Błąd testowania połączenia: {e}")
    
    st.sidebar.markdown("---")
    
    # Główna aplikacja
    if st.sidebar.button("🚀 Inicjalizuj Agenta", type="primary"):
        if not all([gitlab_token, project_id, jenkins_url, jenkins_user, jenkins_token]):
            st.error("❌ Wypełnij wszystkie pola konfiguracji!")
            return
            
        try:
            with st.spinner("Inicjalizacja agenta..."):
                # Inicializacja klientów
                ollama_client = OllamaClient(ollama_host, model_name)
                gitlab_client = GitLabClient(gitlab_token, gitlab_url)
                jenkins_client = JenkinsClient(jenkins_url, jenkins_user, jenkins_token)
                
                # Test połączenia Jenkins
                connection_test = jenkins_client.test_connection()
                if not connection_test['connected']:
                    st.error(f"❌ Nie udało się połączyć z Jenkins: {connection_test['message']}")
                    return
                
                # Inicializacja agenta
                agent = TestAgent(ollama_client, gitlab_client, jenkins_client)
                
                st.session_state.agent = agent
                st.session_state.project_id = project_id
                st.session_state.jenkins_client = jenkins_client
                st.session_state.gitlab_client = gitlab_client
                st.session_state.ollama_client = ollama_client
                
                st.success("✅ Agent został pomyślnie zainicjalizowany!")
                st.info(f"🔗 {connection_test['message']}")
                
        except Exception as e:
            st.error(f"❌ Błąd inicjalizacji: {str(e)}")
    
    if 'agent' in st.session_state:
        show_agent_interface()
    else:
        show_welcome_screen()

def show_welcome_screen():
    """Ekran powitalny z instrukcjami"""
    st.markdown("## 👋 Witaj w Jenkins Test Agent!")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        ### 🧠 Ollama
        - Zainstaluj Ollama
        - Pobierz model gemma2:7b
        - Sprawdź czy działa
        """)
        
    with col2:
        st.markdown("""
        ### 🦊 GitLab
        - Utwórz Access Token
        - Uprawnienia: api, read_repository
        - Znajdź Project ID
        """)
        
    with col3:
        st.markdown("""
        ### 🏗️ Jenkins
        - Utwórz API Token
        - Upewnij się że masz uprawnienia
        - Przygotuj job do testów
        """)
    
    st.markdown("---")
    st.info("💡 **Wskazówka:** Użyj przycisków 'Testuj' w sidebarze aby sprawdzić połączenia przed inicjalizacją agenta.")

def show_agent_interface():
    """Główny interfejs agenta"""
    agent = st.session_state.agent
    jenkins_client = st.session_state.get('jenkins_client')
    
    # Tabs dla różnych funkcji
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "📥 Pobierz Testy", 
        "🏃 Uruchom Testy", 
        "📊 Analiza Logów", 
        "🔧 Popraw Testy",
        "🔍 Jenkins Jobs",
        "📈 Dashboard"
    ])
    
    with tab6:
        show_dashboard()
    
    with tab5:
        show_jenkins_jobs()
    
    with tab1:
        show_fetch_tests()
    
    with tab2:
        show_run_tests()
    
    with tab3:
        show_analyze_logs()
    
    with tab4:
        show_fix_tests()

def show_dashboard():
    """Dashboard z podsumowaniem"""
    st.header("📈 Dashboard")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        tests_count = len(st.session_state.get('tests', []))
        st.metric("📄 Testy", tests_count)
    
    with col2:
        jenkins_jobs = len(st.session_state.get('jenkins_jobs', []))
        st.metric("🏗️ Jenkins Jobs", jenkins_jobs)
    
    with col3:
        local_results = st.session_state.get('local_results', {})
        local_status = "✅" if local_results.get('success') else "❌" if local_results else "⏳"
        st.metric("🏠 Testy lokalne", local_status)
    
    with col4:
        jenkins_results = st.session_state.get('jenkins_results', {})
        jenkins_status = "✅" if jenkins_results.get('success') else "❌" if jenkins_results else "⏳"
        st.metric("☁️ Testy Jenkins", jenkins_status)
    
    # Historia działań
    if 'activity_log' not in st.session_state:
        st.session_state.activity_log = []
    
    if st.session_state.activity_log:
        st.subheader("📋 Historia działań")
        for activity in reversed(st.session_state.activity_log[-10:]):
            st.write(f"• {activity}")

def show_jenkins_jobs():
    """Tab z Jenkins jobs"""
    st.header("🔍 Jenkins Jobs")
    
    jenkins_client = st.session_state.get('jenkins_client')
    
    if jenkins_client:
        col1, col2 = st.columns([1, 3])
        
        with col1:
            if st.button("🔄 Odśwież listę job'ów"):
                try:
                    with st.spinner("Pobieranie job'ów..."):
                        jobs = jenkins_client.get_all_jobs()
                        st.session_state.jenkins_jobs = jobs
                        st.success(f"✅ Znaleziono {len(jobs)} job'ów")
                        add_activity(f"Pobrano {len(jobs)} job'ów z Jenkins")
                except Exception as e:
                    st.error(f"❌ Błąd pobierania job'ów: {e}")
        
        with col2:
            if st.button("➕ Utwórz przykładowy job"):
                create_sample_job()
        
        if 'jenkins_jobs' in st.session_state:
            jobs = st.session_state.jenkins_jobs
            
            if jobs:
                st.subheader(f"📋 Dostępne job'y ({len(jobs)})")
                
                # Filtrowanie job'ów
                search_term = st.text_input("🔍 Szukaj job'a:", "")
                filtered_jobs = [job for job in jobs if search_term.lower() in job['name'].lower()] if search_term else jobs
                
                for job in filtered_jobs:
                    with st.expander(f"📋 {job['name']} - {job.get('color', 'unknown')}"):
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.write(f"**URL:** {job.get('url', 'N/A')}")
                            st.write(f"**Status:** {job.get('color', 'N/A')}")
                        
                        with col2:
                            if st.button(f"ℹ️ Szczegóły", key=f"info_{job['name']}"):
                                try:
                                    job_info = jenkins_client.get_job_info(job['name'])
                                    st.json(job_info)
                                except Exception as e:
                                    st.error(f"Błąd pobierania szczegółów: {e}")
            else:
                st.info("🔍 Brak job'ów w Jenkins lub brak uprawnień do ich przeglądania")
    else:
        st.warning("⚠️ Brak połączenia z Jenkins")

def show_fetch_tests():
    """Tab pobierania testów"""
    st.header("📥 Pobieranie testów z GitLab")
    
    col1, col2 = st.columns(2)
    with col1:
        project_id = st.text_input("Project ID", value=st.session_state.get('project_id', ''))
        branch = st.text_input("Branch", value="main")
    with col2:
        test_path = st.text_input("Ścieżka do testów", value="tests/")
        
    if st.button("📥 Pobierz Testy", type="primary"):
        if not project_id:
            st.error("❌ Podaj Project ID!")
            return
            
        with st.spinner("Pobieranie testów z GitLab..."):
            try:
                agent = st.session_state.agent
                tests = agent.fetch_tests_from_gitlab(project_id, branch, test_path)
                st.session_state.tests = tests
                st.success(f"✅ Pobrano {len(tests)} plików testowych!")
                add_activity(f"Pobrano {len(tests)} testów z GitLab ({project_id})")
                
                if tests:
                    st.subheader("📄 Pobrane pliki testowe:")
                    for test_file in tests:
                        with st.expander(f"📄 {test_file['name']} ({test_file.get('size', 0)} bytes)"):
                            st.code(test_file['content'], language='python')
                else:
                    st.warning("⚠️ Nie znaleziono plików testowych w podanej ścieżce")
                    
            except Exception as e:
                st.error(f"❌ Błąd pobierania testów: {str(e)}")

def show_run_tests():
    """Tab uruchamiania testów"""
    st.header("🏃 Uruchamianie testów")
    
    if 'tests' not in st.session_state or not st.session_state.tests:
        st.warning("⚠️ Najpierw pobierz testy z GitLab!")
        return
    
    tests_count = len(st.session_state.tests)
    st.info(f"📄 Gotowe do uruchomienia: {tests_count} plików testowych")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🏠 Uruchom lokalnie")
        if st.button("▶️ Uruchom lokalne testy", type="primary"):
            with st.spinner("Uruchamianie testów lokalnie..."):
                try:
                    agent = st.session_state.agent
                    result = agent.run_tests_locally(st.session_state.tests)
                    st.session_state.local_results = result
                    
                    if result['success']:
                        st.success("✅ Testy przeszły pomyślnie!")
                    else:
                        st.error("❌ Niektóre testy nie przeszły!")
                    
                    add_activity(f"Uruchomiono testy lokalnie - {'sukces' if result['success'] else 'błąd'}")
                    
                    with st.expander("📄 Logi testów lokalnych"):
                        st.code(result['output'], language='bash')
                        
                except Exception as e:
                    st.error(f"❌ Błąd uruchamiania testów: {str(e)}")
    
    with col2:
        st.subheader("☁️ Uruchom na Jenkins")
        
        # Dropdown z dostępnymi job'ami
        if 'jenkins_jobs' in st.session_state and st.session_state.jenkins_jobs:
            job_names = [job['name'] for job in st.session_state.jenkins_jobs]
            selected_job = st.selectbox("Wybierz job", options=job_names)
            job_name = selected_job
        else:
            job_name = st.text_input("Nazwa job'a Jenkins")
            st.info("💡 Przejdź do tabu 'Jenkins Jobs' aby odświeżyć listę dostępnych job'ów")
        
        if st.button("▶️ Uruchom testy na Jenkins", type="primary"):
            if not job_name:
                st.error("❌ Podaj nazwę job'a!")
                return
                
            with st.spinner(f"Uruchamianie testów na Jenkins ({job_name})..."):
                try:
                    agent = st.session_state.agent
                    result = agent.run_tests_on_jenkins(job_name, st.session_state.tests)
                    st.session_state.jenkins_results = result
                    
                    st.success(f"✅ Job uruchomiony! Build #{result['build_number']}")
                    st.info(f"📊 Status: {result['status']}")
                    
                    add_activity(f"Uruchomiono job '{job_name}' - build #{result['build_number']}")
                    
                    if result.get('logs'):
                        with st.expander("📄 Logi Jenkins"):
                            st.code(result['logs'], language='bash')
                    
                except Exception as e:
                    st.error(f"❌ Błąd uruchamiania na Jenkins: {str(e)}")

def show_analyze_logs():
    """Tab analizy logów"""
    st.header("📊 Analiza logów Jenkins")
    
    if 'jenkins_results' not in st.session_state:
        st.warning("⚠️ Najpierw uruchom testy na Jenkins!")
        return
    
    jenkins_results = st.session_state.jenkins_results
    st.info(f"📋 Analiza buildu #{jenkins_results['build_number']} - Status: {jenkins_results['status']}")
    
    if st.button("🔍 Analizuj logi AI", type="primary"):
        with st.spinner("🧠 AI analizuje logi Jenkins..."):
            try:
                agent = st.session_state.agent
                analysis = agent.analyze_jenkins_logs(jenkins_results)
                st.session_state.log_analysis = analysis
                
                add_activity("AI przeanalizował logi Jenkins")
                
                # Wyświetl wyniki analizy
                col1, col2 = st.columns(2)
                
                with col1:
                    st.subheader("📋 Podsumowanie analizy")
                    st.info(analysis['summary'])
                
                with col2:
                    if analysis.get('errors'):
                        st.subheader("❌ Znalezione błędy")
                        for i, error in enumerate(analysis['errors'], 1):
                            st.error(f"{i}. {error}")
                
                if analysis.get('suggestions'):
                    st.subheader("💡 Sugestie poprawek")
                    for i, suggestion in enumerate(analysis['suggestions'], 1):
                        st.warning(f"{i}. {suggestion}")
                
            except Exception as e:
                st.error(f"❌ Błąd analizy logów: {str(e)}")

def show_fix_tests():
    """Tab poprawek testów"""
    st.header("🔧 Automatyczne poprawki testów")
    
    if 'log_analysis' not in st.session_state:
        st.warning("⚠️ Najpierw przeanalizuj logi!")
        return
    
    analysis = st.session_state.log_analysis
    st.info(f"🎯 Na podstawie analizy: {len(analysis.get('errors', []))} błędów, {len(analysis.get('suggestions', []))} sugestii")
    
    if st.button("🔧 Wygeneruj poprawki AI", type="primary"):
        with st.spinner("🧠 AI generuje poprawki testów..."):
            try:
                agent = st.session_state.agent
                fixes = agent.generate_test_fixes(
                    st.session_state.tests, 
                    analysis
                )
                st.session_state.fixes = fixes
                
                add_activity(f"AI wygenerował {len(fixes)} poprawek")
                
                if fixes:
                    st.success(f"✅ Wygenerowano {len(fixes)} poprawek!")
                    
                    st.subheader("📝 Proponowane poprawki")
                    
                    for i, fix in enumerate(fixes, 1):
                        with st.expander(f"🔧 Poprawka {i}: {fix['file']}"):
                            st.markdown("**🔍 Opis problemu:**")
                            st.write(fix['problem'])
                            
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                st.markdown("**📄 Oryginalny kod:**")
                                st.code(fix['original_code'], language='python')
                            
                            with col2:
                                st.markdown("**✅ Poprawiony kod:**")
                                st.code(fix['fixed_code'], language='python')
                            
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                if st.button(f"✅ Zastosuj", key=f"apply_{i}"):
                                    apply_fix(fix)
                            with col2:
                                if st.button(f"💾 Zapisz do GitLab", key=f"save_{i}"):
                                    save_fix_to_gitlab(fix)
                            with col3:
                                if st.button(f"📋 Kopiuj", key=f"copy_{i}"):
                                    st.code(fix['fixed_code'], language='python')
                else:
                    st.info("ℹ️ Nie znaleziono problemów wymagających poprawek")
                    
            except Exception as e:
                st.error(f"❌ Błąd generowania poprawek: {str(e)}")

def apply_fix(fix):
    """Aplikuje poprawkę lokalnie"""
    try:
        agent = st.session_state.agent
        agent.apply_fix(fix)
        st.success(f"✅ Poprawka zastosowana dla {fix['file']}")
        add_activity(f"Zastosowano poprawkę dla {fix['file']}")
    except Exception as e:
        st.error(f"❌ Błąd aplikowania poprawki: {e}")

def save_fix_to_gitlab(fix):
    """Zapisuje poprawkę do GitLab"""
    try:
        gitlab_client = st.session_state.get('gitlab_client')
        project_id = st.session_state.get('project_id')
        
        if not gitlab_client or not project_id:
            st.error("❌ Brak konfiguracji GitLab")
            return
        
        commit_message = f"AI fix: {fix['problem'][:50]}..."
        gitlab_client.update_file(
            project_id, 
            fix['file'], 
            fix['fixed_code'], 
            commit_message
        )
        
        st.success(f"✅ Poprawka zapisana do GitLab: {fix['file']}")
        add_activity(f"Zapisano poprawkę do GitLab: {fix['file']}")
        
    except Exception as e:
        st.error(f"❌ Błąd zapisu do GitLab: {e}")

def create_sample_job():
    """Tworzy przykładowy job w Jenkins"""
    try:
        jenkins_client = st.session_state.get('jenkins_client')
        
        # Wczytaj przykładowy XML
        with open('example_jenkins_job.xml', 'r') as f:
            job_xml = f.read()
        
        job_name = "test-agent-sample-job"
        jenkins_client.create_job(job_name, job_xml)
        
        st.success(f"✅ Utworzono przykładowy job: {job_name}")
        add_activity(f"Utworzono job: {job_name}")
        
    except Exception as e:
        st.error(f"❌ Błąd tworzenia job'a: {e}")

def add_activity(message):
    """Dodaje wpis do historii działań"""
    if 'activity_log' not in st.session_state:
        st.session_state.activity_log = []
    
    import datetime
    timestamp = datetime.datetime.now().strftime("%H:%M:%S")
    st.session_state.activity_log.append(f"{timestamp} - {message}")

if __name__ == "__main__":
    main() 
