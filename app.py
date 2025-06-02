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
            
            # Inicializacja agenta
            agent = TestAgent(ollama_client, gitlab_client, jenkins_client)
            
            st.session_state.agent = agent
            st.session_state.project_id = project_id
            st.success("Agent został pomyślnie zainicjalizowany!")
            
        except Exception as e:
            st.error(f"Błąd inicjalizacji: {str(e)}")
    
    if 'agent' in st.session_state:
        show_agent_interface()

def show_agent_interface():
    agent = st.session_state.agent
    
    # Tabs dla różnych funkcji
    tab1, tab2, tab3, tab4 = st.tabs([
        "📥 Pobierz Testy", 
        "🏃 Uruchom Testy", 
        "📊 Analiza Logów", 
        "🔧 Popraw Testy"
    ])
    
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