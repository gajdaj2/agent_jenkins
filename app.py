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
    st.sidebar.subheader("Ollama")
    ollama_host = st.sidebar.text_input("Host Ollama", value="http://localhost:11434")
    model_name = st.sidebar.text_input("Model", value="gemma2:7b")
    
    # Konfiguracja GitLab
    st.sidebar.subheader("GitLab")
    gitlab_token = st.sidebar.text_input("GitLab Token", type="password")
    gitlab_url = st.sidebar.text_input("GitLab URL", value="https://gitlab.com")
    project_id = st.sidebar.text_input("Project ID (lub owner/repo)")
    
    # Konfiguracja Jenkins
    st.sidebar.subheader("Jenkins")
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
                                st.sidebar.info(f"Znaleziono {len(jobs)} job'ów")
                                job_names = [job['name'] for job in jobs[:5]]
                                st.sidebar.write("Przykładowe job'y:", ", ".join(job_names))
                        except Exception as e:
                            st.sidebar.warning(f"Nie udało się pobrać listy job'ów: {e}")
                    else:
                        st.sidebar.error(connection_test['message'])
                        
                except Exception as e:
                    st.sidebar.error(f"Błąd testowania połączenia: {e}")
    
    # Główna aplikacja
    if st.sidebar.button("🔧 Inicjalizuj Agenta"):
        if not all([gitlab_token, project_id, jenkins_url, jenkins_user, jenkins_token]):
            st.error("Wypełnij wszystkie pola konfiguracji!")
            return
            
        try:
            # Inicializacja klientów
            ollama_client = OllamaClient(ollama_host, model_name)
            gitlab_client = GitLabClient(gitlab_token, gitlab_url)
            jenkins_client = JenkinsClient(jenkins_url, jenkins_user, jenkins_token)
            
            # Test połączenia Jenkins
            connection_test = jenkins_client.test_connection()
            if not connection_test['connected']:
                st.error(f"Nie udało się połączyć z Jenkins: {connection_test['message']}")
                return
            
            # Inicializacja agenta
            agent = TestAgent(ollama_client, gitlab_client, jenkins_client)
            
            st.session_state.agent = agent
            st.session_state.project_id = project_id
            st.session_state.jenkins_client = jenkins_client
            st.success("Agent został pomyślnie zainicjalizowany!")
            st.info(connection_test['message'])
            
        except Exception as e:
            st.error(f"Błąd inicjalizacji: {str(e)}")
    
    if 'agent' in st.session_state:
        show_agent_interface()

def show_agent_interface():
    agent = st.session_state.agent
    jenkins_client = st.session_state.get('jenkins_client')
    
    # Tabs dla różnych funkcji
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📥 Pobierz Testy", 
        "🏃 Uruchom Testy", 
        "📊 Analiza Logów", 
        "🔧 Popraw Testy",
        "🔍 Jenkins Jobs"
    ])
    
    with tab5:
        st.header("Jenkins Jobs")
        
        if jenkins_client:
            if st.button("🔄 Odśwież listę job'ów"):
                try:
                    jobs = jenkins_client.get_all_jobs()
                    st.session_state.jenkins_jobs = jobs
                    st.success(f"Znaleziono {len(jobs)} job'ów")
                except Exception as e:
                    st.error(f"Błąd pobierania job'ów: {e}")
            
            if 'jenkins_jobs' in st.session_state:
                jobs = st.session_state.jenkins_jobs
                
                st.subheader(f"Dostępne job'y ({len(jobs)})")
                for job in jobs:
                    with st.expander(f"📋 {job['name']}"):
                        st.write(f"**URL:** {job.get('url', 'N/A')}")
                        st.write(f"**Kolor:** {job.get('color', 'N/A')}")
                        
                        if st.button(f"ℹ️ Szczegóły", key=f"info_{job['name']}"):
                            try:
                                job_info = jenkins_client.get_job_info(job['name'])
                                st.json(job_info)
                            except Exception as e:
                                st.error(f"Błąd pobierania szczegółów: {e}")
    
    with tab1:
        st.header("Pobieranie testów z GitLab")
        
        col1, col2 = st.columns(2)
        with col1:
            project_id = st.text_input("Project ID", value=st.session_state.get('project_id', ''))
            branch = st.text_input("Branch", value="main")
        with col2:
            test_path = st.text_input("Ścieżka do testów", value="tests/")
        
        if st.button("📥 Pobierz Testy"):
            with st.spinner("Pobieranie testów..."):
                try:
                    tests = agent.fetch_tests_from_gitlab(project_id, branch, test_path)
                    st.session_state.tests = tests
                    st.success(f"Pobrano {len(tests)} plików testowych!")
                    
                    for test_file in tests:
                        with st.expander(f"📄 {test_file['name']}"):
                            st.code(test_file['content'], language='python')
                            
                except Exception as e:
                    st.error(f"Błąd pobierania testów: {str(e)}")
    
    with tab2:
        st.header("Uruchamianie testów")
        
        if 'tests' not in st.session_state:
            st.warning("Najpierw pobierz testy z GitLab!")
            return
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("🏠 Uruchom lokalnie")
            if st.button("▶️ Uruchom lokalne testy"):
                with st.spinner("Uruchamianie testów lokalnie..."):
                    try:
                        result = agent.run_tests_locally(st.session_state.tests)
                        st.session_state.local_results = result
                        
                        if result['success']:
                            st.success("Testy przeszły pomyślnie!")
                        else:
                            st.error("Niektóre testy nie przeszły!")
                        
                        st.code(result['output'], language='bash')
                        
                    except Exception as e:
                        st.error(f"Błąd uruchamiania testów: {str(e)}")
        
        with col2:
            st.subheader("☁️ Uruchom na Jenkins")
            
            # Dropdown z dostępnymi job'ami
            if 'jenkins_jobs' in st.session_state:
                job_names = [job['name'] for job in st.session_state.jenkins_jobs]
                selected_job = st.selectbox("Wybierz job", options=job_names)
                job_name = selected_job
            else:
                job_name = st.text_input("Nazwa job'a Jenkins")
            
            if st.button("▶️ Uruchom testy na Jenkins"):
                if not job_name:
                    st.error("Podaj nazwę job'a!")
                    return
                    
                with st.spinner("Uruchamianie testów na Jenkins..."):
                    try:
                        result = agent.run_tests_on_jenkins(job_name, st.session_state.tests)
                        st.session_state.jenkins_results = result
                        
                        st.success(f"Job uruchomiony! Build #{result['build_number']}")
                        st.info(f"Status: {result['status']}")
                        
                        if result['logs']:
                            with st.expander("📄 Logi Jenkins"):
                                st.code(result['logs'], language='bash')
                        
                    except Exception as e:
                        st.error(f"Błąd uruchamiania na Jenkins: {str(e)}")
    
    with tab3:
        st.header("Analiza logów Jenkins")
        
        if 'jenkins_results' not in st.session_state:
            st.warning("Najpierw uruchom testy na Jenkins!")
            return
        
        if st.button("🔍 Analizuj logi"):
            with st.spinner("Analizowanie logów..."):
                try:
                    analysis = agent.analyze_jenkins_logs(st.session_state.jenkins_results)
                    st.session_state.log_analysis = analysis
                    
                    st.subheader("📋 Podsumowanie analizy")
                    st.info(analysis['summary'])
                    
                    if analysis['errors']:
                        st.subheader("❌ Znalezione błędy")
                        for error in analysis['errors']:
                            st.error(error)
                    
                    if analysis['suggestions']:
                        st.subheader("💡 Sugestie poprawek")
                        for suggestion in analysis['suggestions']:
                            st.warning(suggestion)
                    
                except Exception as e:
                    st.error(f"Błąd analizy logów: {str(e)}")
    
    with tab4:
        st.header("Automatyczne poprawki testów")
        
        if 'log_analysis' not in st.session_state:
            st.warning("Najpierw przeanalizuj logi!")
            return
        
        if st.button("🔧 Wygeneruj poprawki"):
            with st.spinner("Generowanie poprawek..."):
                try:
                    fixes = agent.generate_test_fixes(
                        st.session_state.tests, 
                        st.session_state.log_analysis
                    )
                    st.session_state.fixes = fixes
                    
                    st.subheader("📝 Proponowane poprawki")
                    
                    for fix in fixes:
                        with st.expander(f"🔧 {fix['file']}"):
                            st.markdown("**Opis problemu:**")
                            st.write(fix['problem'])
                            
                            st.markdown("**Poprawiony kod:**")
                            st.code(fix['fixed_code'], language='python')
                            
                            if st.button(f"✅ Zastosuj poprawkę dla {fix['file']}", key=fix['file']):
                                agent.apply_fix(fix)
                                st.success(f"Poprawka zastosowana dla {fix['file']}")
                    
                except Exception as e:
                    st.error(f"Błąd generowania poprawek: {str(e)}")

if __name__ == "__main__":
    main() 
