import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings
from langchain_community.retrievers import BM25Retriever
from sentence_transformers import CrossEncoder
from langchain_core.documents import Document

# Import des modules internes
from src.rag_engine import run_baseline, run_rag, run_rag_hybrid, run_rag_reranking
from src.config import DB_PATH, MODEL, EMBEDDING_MODEL, SERVER
from src.utils import query_ollama

# Configuration

st.set_page_config(
    page_title="RAG - Analyse et Chat",
    page_icon="🛰️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Configuration des bases de données disponibles
DATABASES = {
    "Main Dataset (ESA/Galileo)": {
        "db_path": "db_multi_docs",
        "collection": "multi_docs_collection",
        "csv_path": "data/main/processed/demo_results.csv"
    },
    "Test Dataset (Local)": {
        "db_path": "db_local",
        "collection": "pdf_rag_collection",
        "csv_path": "data/test/processed/demo_results.csv"
    }
}

# Fonctions utilitaires

@st.cache_resource
def load_vector_db(db_path, collection_name):
    """Charge la base vectorielle et le reranker avec cache"""
    try:
        if not Path(db_path).exists():
            return None, None, None
        
        embeddings = OllamaEmbeddings(model=EMBEDDING_MODEL, base_url=SERVER)
        vector_db = Chroma(
            persist_directory=db_path,
            embedding_function=embeddings,
            collection_name=collection_name
        )
        
        # Chargement du reranker
        reranker = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')
        
        # Récupération des chunks pour BM25
        try:
            data = vector_db.get()
            all_chunks = []
            if data and data.get('ids'):
                for i in range(len(data['ids'])):
                    doc = Document(
                        page_content=data['documents'][i],
                        metadata=data['metadatas'][i] if data.get('metadatas') else {}
                    )
                    all_chunks.append(doc)
        except Exception as e:
            st.warning(f"Impossible de charger les chunks pour BM25: {e}")
            all_chunks = []
        
        return vector_db, reranker, all_chunks
        
    except Exception as e:
        st.error(f"Erreur lors du chargement de la base: {e}")
        return None, None, None


def format_sources_display(sources_list):
    """Formate les sources pour l'affichage"""
    if not sources_list:
        return []
    return [f"[{i+1}] {s}" for i, s in enumerate(sources_list)]


def load_csv_results(file_path):
    """Charge les résultats CSV"""
    try:
        if Path(file_path).exists():
            return pd.read_csv(file_path)
        return None
    except Exception as e:
        st.error(f"Erreur de chargement CSV: {e}")
        return None


# Sidebar de navigation

with st.sidebar:
    st.title("Navigation")
    
    # Sélection de la base de données
    st.subheader("Base de Connaissances")
    selected_db_key = st.selectbox(
        "Corpus actif:",
        list(DATABASES.keys()),
        index=0,
        key="db_selector"
    )
    
    current_db = DATABASES[selected_db_key]
    
    st.markdown("---")
    
    # Navigation entre pages
    page = st.radio(
        "Pages:",
        ["Chat RAG", "Analyse des Résultats"],
        index=0
    )
    
    st.markdown("---")
    
    # Informations système
    st.caption(f"**Modèle LLM:** {MODEL}")
    st.caption(f"**Embeddings:** {EMBEDDING_MODEL}")
    st.caption(f"**Collection:** {current_db['collection']}")
    
    # Statut Ollama
    try:
        import requests
        response = requests.get(f"{SERVER}/api/tags", timeout=2)
        if response.status_code == 200:
            st.success("Ollama: Connecté")
        else:
            st.error("Ollama: Erreur")
    except:
        st.error("Ollama: Non disponible")


# Chargement de la base vectorielle

vector_db, reranker, all_chunks = load_vector_db(
    current_db['db_path'],
    current_db['collection']
)


# PAGE 1: Chat RAG

if page == "Chat RAG":
    st.title(f"Chat - {selected_db_key}")
    st.markdown("*Posez vos questions sur les documents indexés*")
    
    # Vérification de la base de données
    if vector_db is None:
        st.error(f"Base de données introuvable: {current_db['db_path']}")
        st.info("Lancez d'abord: `python main.py --mode database`")
        st.stop()
    
    # Configuration du mode RAG
    col1, col2 = st.columns([3, 1])
    
    with col1:
        mode = st.selectbox(
            "Stratégie de recherche:",
            [
                "Baseline (LLM seul)",
                "RAG Standard (Recherche vectorielle)",
                "RAG Hybrid (BM25 + Vectoriel)",
                "RAG Reranking (Expert)"
            ],
            index=3
        )
    
    with col2:
        if st.button("Effacer historique"):
            st.session_state.messages = []
            st.rerun()
    
    # Initialisation de l'historique
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    # Affichage de l'historique
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            
            if "sources" in msg and msg["sources"]:
                with st.expander(f"Sources ({len(msg['sources'])}) - {msg.get('mode', 'N/A')}"):
                    for s in msg["sources"]:
                        st.info(s)
            
            if "time" in msg:
                st.caption(f"Temps: {msg['time']:.2f}s")
    
    # Zone de saisie
    if question := st.chat_input("Votre question..."):
        
        # Affichage question utilisateur
        st.session_state.messages.append({"role": "user", "content": question})
        with st.chat_message("user"):
            st.markdown(question)
        
        # Traitement de la réponse
        with st.chat_message("assistant"):
            with st.spinner(f"Recherche en cours ({mode})..."):
                
                try:
                    # Sélection de la méthode RAG
                    if "Baseline" in mode:
                        response, duration = run_baseline(question)
                        sources = []
                        tag = "Baseline"
                    
                    elif "Standard" in mode:
                        response, duration, sources = run_rag(question, current_db['db_path'], current_db['collection'])
                        tag = "RAG Standard"
                    
                    elif "Hybrid" in mode:
                        if not all_chunks:
                            st.warning("Mode Hybrid non disponible (chunks non chargés)")
                            response, duration, sources = run_rag(question, current_db['db_path'], current_db['collection'])
                            tag = "RAG Standard (fallback)"
                        else:
                            response, duration, sources = run_rag_hybrid(question, current_db['db_path'], current_db['collection'])
                            tag = "RAG Hybrid"
                    
                    else:  # Reranking
                        response, duration, sources = run_rag_reranking(question, current_db['db_path'], current_db['collection'])
                        tag = "RAG Reranking"
                    
                    # Affichage de la réponse
                    st.markdown(response)
                    
                    # Affichage des sources
                    if sources:
                        sources_formatted = format_sources_display(sources)
                        with st.expander(f"Voir les {len(sources)} sources"):
                            for s in sources_formatted:
                                st.info(s)
                    
                    st.caption(f"Temps: {duration:.2f}s | Mode: {tag}")
                    
                    # Sauvegarde dans l'historique
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": response,
                        "sources": sources_formatted if sources else [],
                        "time": duration,
                        "mode": tag
                    })
                
                except Exception as e:
                    st.error(f"Erreur: {str(e)}")
                    st.info("Vérifiez que Ollama est lancé et la base vectorielle existe.")


# PAGE 2: Analyse des Résultats

elif page == "Analyse des Résultats":
    st.title("Analyse Comparative des Performances RAG")
    st.markdown("*Visualisation et comparaison des différentes méthodes*")
    
    # Chargement des résultats CSV
    csv_path = current_db['csv_path']
    df = load_csv_results(csv_path)
    
    if df is None:
        st.warning(f"Fichier de résultats introuvable: {csv_path}")
        st.info("Générez d'abord les résultats: `python main.py --mode eval`")
        st.stop()
    
    st.success(f"{len(df)} questions chargées")
    
    # Onglets d'analyse
    tab1, tab2, tab3 = st.tabs([
        "Performances Globales",
        "Exploration par Question",
        "Données Brutes"
    ])
    
    # TAB 1: Performances Globales
    
    with tab1:
        st.subheader("Métriques de Performance")
        
        # Métriques moyennes
        col1, col2, col3, col4 = st.columns(4)
        
        metrics = [
            ("Baseline", "baseline_time", "#FF6B6B"),
            ("RAG Standard", "rag_time", "#4ECDC4"),
            ("RAG Hybrid", "rag_hybrid_time", "#45B7D1"),
            ("RAG Reranking", "rerank_time", "#96CEB4")
        ]
        
        for col, (label, metric_col, color) in zip([col1, col2, col3, col4], metrics):
            if metric_col in df.columns:
                avg_time = df[metric_col].mean()
                delta = avg_time - df['baseline_time'].mean() if metric_col != 'baseline_time' else None
                col.metric(
                    label,
                    f"{avg_time:.2f}s",
                    delta=f"{delta:.2f}s" if delta else None
                )
        
        st.markdown("---")
        
        # Graphique: Distribution des temps
        st.subheader("Distribution des Temps de Réponse")
        
        time_cols = ['baseline_time', 'rag_time', 'rag_hybrid_time', 'rerank_time']
        available_time_cols = [col for col in time_cols if col in df.columns]
        
        if available_time_cols:
            times_df = df[available_time_cols].copy()
            times_df.columns = ['Baseline', 'RAG Standard', 'RAG Hybrid', 'RAG Reranking'][:len(available_time_cols)]
            
            fig_times = px.box(
                times_df,
                title="Distribution des Temps par Méthode",
                labels={'value': 'Temps (secondes)', 'variable': 'Méthode'},
                color_discrete_sequence=['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4']
            )
            st.plotly_chart(fig_times, width="stretch")
        
        st.markdown("---")
        
        # Graphique: Longueur des réponses
        st.subheader("Longueur Moyenne des Réponses")
        
        length_cols = ['baseline_length', 'rag_length', 'rag_hybrid_length', 'rerank_length']
        available_length_cols = [col for col in length_cols if col in df.columns]
        
        if available_length_cols:
            lengths_data = {
                col.replace('_length', '').replace('_', ' ').title(): df[col].mean()
                for col in available_length_cols
            }
            
            fig_lengths = px.bar(
                x=list(lengths_data.keys()),
                y=list(lengths_data.values()),
                title="Nombre Moyen de Caractères par Réponse",
                labels={'x': 'Méthode', 'y': 'Caractères'},
                color=list(lengths_data.keys()),
                color_discrete_sequence=['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4']
            )
            st.plotly_chart(fig_lengths, width="stretch")
    
    # TAB 2: Analyse Détaillée par Question
    
    with tab2:
        st.subheader("Analyse Détaillée par Question")
        
        # Sélecteur de question
        question_idx = st.selectbox(
            "Sélectionner une question:",
            range(len(df)),
            format_func=lambda i: f"Q{i+1}: {df.iloc[i]['question'][:80]}..."
        )
        
        row = df.iloc[question_idx]
        
        st.markdown(f"### Question {question_idx + 1}")
        st.info(row['question'])
        
        # Affichage des réponses en colonnes
        col1, col2 = st.columns(2)
        
        with col1:
            # Baseline
            st.markdown("#### Baseline")
            st.write(row['baseline_response'])
            st.caption(f"Temps: {row['baseline_time']:.2f}s | Longueur: {row['baseline_length']} caractères")
            
            st.markdown("---")
            
            # RAG Standard
            st.markdown("#### RAG Standard")
            st.write(row['rag_response'])
            st.caption(f"Temps: {row['rag_time']:.2f}s | Longueur: {row['rag_length']} caractères")
            if row['rag_sources'] != 'Aucune':
                with st.expander("Sources"):
                    for src in row['rag_sources'].split(' | '):
                        st.text(src)
        
        with col2:
            # RAG Hybrid
            st.markdown("#### RAG Hybrid")
            st.write(row['rag_hybrid_response'])
            st.caption(f"Temps: {row['rag_hybrid_time']:.2f}s | Longueur: {row['rag_hybrid_length']} caractères")
            if row['rag_hybrid_sources'] != 'Aucune':
                with st.expander("Sources"):
                    for src in row['rag_hybrid_sources'].split(' | '):
                        st.text(src)
            
            st.markdown("---")
            
            # RAG Reranking
            st.markdown("#### RAG Reranking")
            st.write(row['rerank_response'])
            st.caption(f"Temps: {row['rerank_time']:.2f}s | Longueur: {row['rerank_length']} caractères")
            if row['rerank_sources'] != 'Aucune':
                with st.expander("Sources"):
                    for src in row['rerank_sources'].split(' | '):
                        st.text(src)
    
    # TAB 3: Donnees Brutes
    
    with tab3:
        st.subheader("Tableau de Données Complet")
        
        # Options d'affichage
        col1, col2 = st.columns(2)
        
        with col1:
            columns_to_show = st.multiselect(
                "Colonnes à afficher:",
                df.columns.tolist(),
                default=['id', 'question', 'baseline_time', 'rag_time', 'rag_hybrid_time', 'rerank_time']
            )
        
        with col2:
            show_full = st.checkbox("Afficher texte complet", value=False)
        
        if columns_to_show:
            display_df = df[columns_to_show].copy()
            
            # Tronquer si nécessaire
            if not show_full:
                for col in display_df.columns:
                    if display_df[col].dtype == 'object':
                        display_df[col] = display_df[col].apply(
                            lambda x: str(x)[:150] + "..." if len(str(x)) > 150 else str(x)
                        )
            
            st.dataframe(display_df, width="stretch", height=400)
            
            # Export CSV
            csv_export = df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="Télécharger (CSV)",
                data=csv_export,
                file_name=f"rag_results_{selected_db_key.lower().replace(' ', '_')}.csv",
                mime="text/csv"
            )
