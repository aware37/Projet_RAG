import os
import glob
import json
import time
import shutil
import requests
from tqdm import tqdm
import pandas as pd
import nest_asyncio
nest_asyncio.apply()

from llama_parse import LlamaParse
from langchain_text_splitters import Language, MarkdownHeaderTextSplitter, RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_community.retrievers import BM25Retriever
from langchain_ollama import OllamaEmbeddings
from langchain_core.documents import Document
from sentence_transformers import CrossEncoder
from dotenv import load_dotenv
load_dotenv()

# ============================================================================
# CONFIGURATION
# ============================================================================

INPUT_DIR = "data/main/raw"
MD_DIR = "data/main/intermediate"
CHUNKS_JSON = "data/main/processed/all_chunks.json"
DB_PATH = "./db_multi_docs"

os.makedirs(INPUT_DIR, exist_ok=True)
os.makedirs(MD_DIR, exist_ok=True)
os.makedirs("data/main/processed", exist_ok=True)

SERVER = "http://localhost:11434"
MODEL = "mistral"
EMBEDDING_MODEL = "nomic-embed-text"

LLAMA_API_KEY = os.getenv("LLAMA_CLOUD_API_KEY")
os.environ["LLAMA_CLOUD_API_KEY"] = LLAMA_API_KEY


# ============================================================================
# UTILITAIRES
# ============================================================================

def query_ollama(model: str, prompt: str) -> str:
    """
    Ollama en local via API
    """
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "stream": False
    }
    try:
        r = requests.post(f"{SERVER}/api/chat", json=payload)
        r.raise_for_status()
        response = r.json()
        return response.get("message", {}).get("content", "").strip()
    except requests.exceptions.ConnectionError:
        print("Erreur : Ollama n'est pas lance")
        return ""


def extract_metadata_with_llm(md_text_start):
    """
    Extrait le titre, les auteurs et l'année de publication du début du texte Markdown
    """
    prompt = """You are an expert librarian assistant.
    Analyze the beginning of this scientific document (Markdown format) and extract the following information in strict JSON format:
    - "title": The complete title of the paper.
    - "authors": The list of authors (separated by commas).
    - "year": The publication year (if found, otherwise "Unknown").
    
    TEXT:
    {text}
    
    Reply ONLY with the JSON, no additional explanations.
    """.format(text=md_text_start[:3000])
    
    response = query_ollama(MODEL, prompt)
    
    try:
        content = response.strip()
        metadata = json.loads(content)
        if isinstance(metadata.get("authors"), list):
            metadata["authors"] = ", ".join(metadata["authors"])
        return metadata
    except json.JSONDecodeError:
        return {"title": "Unknown", "authors": "Unknown", "year": "Unknown"}


# ============================================================================
# ETAPE 1 : PDF -> MARKDOWN
# ============================================================================

def step1_llamaparse(pdf_path, output_md_path):
    """
    Convertit un PDF en Markdown avec LlamaParse
    """
    parser = LlamaParse(
        result_type="markdown",
        premium_mode=True,
        verbose=True
    )
    
    documents = parser.load_data(pdf_path)
    full_markdown = "\n\n".join([doc.text for doc in documents])
    
    if os.path.exists(output_md_path):
        print(f"{output_md_path} existe déjà, on saute.")
        return
    
    os.makedirs(os.path.dirname(output_md_path), exist_ok=True)
    with open(output_md_path, "w", encoding="utf-8") as f:
        f.write(full_markdown)
    
    return full_markdown


def step1_process_folder(input_folder, output_folder):
    """
    Convertit tous les PDF d'un dossier en Markdown
    """

    pdf_files = glob.glob(os.path.join(input_folder, "*.pdf"))
    print(f"\n{len(pdf_files)} fichiers PDF detectes")
    
    md_files = []
    for pdf_file in tqdm(pdf_files, desc="Conversion PDFs"):
        base_name = os.path.basename(pdf_file).replace(".pdf", ".md")
        output_md_path = os.path.join(output_folder, base_name)
        step1_llamaparse(pdf_file, output_md_path)
        md_files.append(output_md_path)
    
    return md_files


# ============================================================================
# ETAPE 2 : MARKDOWN -> CHUNKS
# ============================================================================

def step2_markdown_to_json(md_path, json_output_path):
    """
    Convertit un fichier Markdown en chunks JSON avec métadonnées
    """
    with open(md_path, "r", encoding="utf-8") as f:
        md_text = f.read()
    
    meta_globales = extract_metadata_with_llm(md_text)
    
    # Suppression section References
    if "\n# References" in md_text:
        md_text = md_text.split("\n# References")[0]
    elif "\n## References" in md_text:
        md_text = md_text.split("\n## References")[0]
    
    # Découpage par titres Markdown
    markdown_splitter = MarkdownHeaderTextSplitter(
        headers_to_split_on=[
            ("#", "Titre"),
            ("##", "Section"),
            ("###", "Sous_Section"),
        ]
    )
    md_header_splits = markdown_splitter.split_text(md_text)
    
    text_splitter = RecursiveCharacterTextSplitter.from_language(
        language=Language.MARKDOWN,
        chunk_size=1000,
        chunk_overlap=200,
        add_start_index=True,
    )
    final_docs = text_splitter.split_documents(md_header_splits)
    
    # Ajout des métadonnées
    json_output = []
    for doc in final_docs:
        chunk_data = {
            "page_content": doc.page_content,
            "metadata": {
                "source": md_path,
                "section": doc.metadata.get("Section", "Introduction"),
                "sous_section": doc.metadata.get("Sous_Section", ""),
                "titre": doc.metadata.get("Titre", ""),
                "meta_title": str(meta_globales.get("title", "Unknown")),
                "meta_authors": str(meta_globales.get("authors", "Unknown")),
                "meta_year": str(meta_globales.get("year", "Unknown")),
            }
        }
        json_output.append(chunk_data)
    
    with open(json_output_path, "w", encoding="utf-8") as f:
        json.dump(json_output, f, indent=2, ensure_ascii=False)
    
    return json_output


def step2_process_folder(md_files, combined_json_path):
    """
    Convertit tous les fichiers Markdown en chunks JSON combinés
    """
    all_chunks = []
    
    for md_file in tqdm(md_files, desc="Processing Markdowns"):
        base_name = os.path.basename(md_file).replace(".md", "_chunks.json")
        json_output_path = os.path.join(os.path.dirname(md_file), base_name)
        chunks = step2_markdown_to_json(md_file, json_output_path)
        all_chunks.extend(chunks)
    
    with open(combined_json_path, "w", encoding="utf-8") as f:
        json.dump(all_chunks, f, indent=2, ensure_ascii=False)
    
    print(f"\n{len(all_chunks)} chunks combines sauvegardes")
    return all_chunks


# ============================================================================
# ETAPE 3 : CREATION BASE VECTORIELLE
# ============================================================================

def step3_create_vector_db(chunks_json, db_path):
    """
    Crée une base vectorielle Chroma à partir des chunks JSON
    """
    if not os.path.exists(chunks_json):
        print(f"Erreur : {chunks_json} n'existe pas")
        return
    
    if os.path.exists(db_path):
        shutil.rmtree(db_path, ignore_errors=True)
    
    os.makedirs(db_path, exist_ok=True)
    os.chmod(db_path, 0o777)
    
    with open(chunks_json, 'r', encoding='utf-8') as f:
        all_chunks = json.load(f)
    
    documents = []
    for item in tqdm(all_chunks, desc="Creation Documents"):
        doc = Document(
            page_content=item['page_content'],
            metadata=item['metadata']
        )
        documents.append(doc)
    
    embeddings = OllamaEmbeddings(
        model=EMBEDDING_MODEL,
        base_url=SERVER
    )
    
    vector_db = Chroma.from_documents(
        documents=documents,
        embedding=embeddings,
        persist_directory=db_path,
        collection_name="multi_docs_collection"
    )
    
    print(f"\nBase vectorielle creee : {len(documents)} documents indexes")
    return vector_db


# ============================================================================
# FONCTIONS RAG
# ============================================================================

def run_baseline(question):
    """
    Baseline : réponse directe via LLM sans contexte.
    Retourne la réponse et la durée.
    """
    start_time = time.time()
    prompt = f"Reponds a cette question de maniere concise :\n\n{question}"
    response = query_ollama(MODEL, prompt)
    duration = time.time() - start_time
    return response, duration


def run_rag(question, db_path=DB_PATH, top_k=5):
    """
    RAG simple : récupère top-k, génère réponse avec contexte.
    Retourne la réponse, la durée et les sources.
    """
    start_time = time.time()
    
    embeddings = OllamaEmbeddings(model=EMBEDDING_MODEL, base_url=SERVER)
    vector_db = Chroma(
        embedding_function=embeddings,
        persist_directory=db_path,
        collection_name="multi_docs_collection",
    )
    
    results = vector_db.similarity_search(question, k=top_k)
    
    if not results:
        return "Aucune info trouvee dans la base.", 0, []
    
    context_str = ""
    sources_list = []
    
    for doc in results:
        meta = doc.metadata
        titre = meta.get('meta_title', meta.get('title', 'Doc'))
        section = meta.get('section', 'Section Inconnue')
        source_info = f"{titre} > {section}"
        sources_list.append(source_info)
        context_str += f"---\n[Source: {source_info}]\n{doc.page_content}\n"
    
    final_prompt = f"""Tu es un assistant scientifique expert. 
Utilise EXCLUSIVEMENT le contexte ci-dessous pour repondre a la question.

CONTEXTE :
{context_str}

QUESTION : 
{question}

REPONSE :"""
    
    reponse = query_ollama(MODEL, final_prompt)
    duration = time.time() - start_time
    
    return reponse, duration, sources_list


def run_rag_reranking(question, db_path=DB_PATH, top_k=20, final_k=5):
    """
    RAG avec reranking : récupère top-k, rerank avec cross-encoder, génère réponse.
    Retourne la réponse, la durée et les sources.
    """
    start_time = time.time()

    # Embedding et recherche initiale (top-k)
    embeddings = OllamaEmbeddings(model=EMBEDDING_MODEL, base_url=SERVER)
    vector_db = Chroma(
        embedding_function=embeddings,
        persist_directory=db_path,
        collection_name="multi_docs_collection"
    )
    initial_docs = vector_db.similarity_search(question, k=top_k)
    
    if not initial_docs:
        return "Pas de docs", 0, []
    
    # Reranking avec cross-encoder
    reranker = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')
    pairs = [[question, doc.page_content] for doc in initial_docs]
    scores = reranker.predict(pairs)
    ranked_results = sorted(zip(initial_docs, scores), key=lambda x: x[1], reverse=True)
    top_docs = [doc for doc, score in ranked_results[:final_k]]


    # Generation de la reponse avec le contexte reranké 
    context_str = "\n".join([d.page_content for d in top_docs])
    prompt = f"Tu es un expert. Contexte :\n{context_str}\n\nQuestion : {question}\nReponse :"
    response = query_ollama(MODEL, prompt)
    duration = time.time() - start_time
    
    # Formatage des sources
    sources_format = []
    for doc in top_docs:
        meta = doc.metadata
        titre = meta.get('meta_title', meta.get('source', 'Doc'))
        if "/" in titre:
            titre = titre.split("/")[-1]
        section = meta.get('section', 'Section Inconnue')
        source_info = f"{titre} > {section}"
        sources_format.append(source_info)
    
    return response, duration, sources_format


def run_rag_hybrid(question):
    """
    RAG hybride : combine BM25 et recherche vectorielle.
    Retourne la réponse, la durée et les sources.
    """
    start_time = time.time()
    
    embeddings = OllamaEmbeddings(model=EMBEDDING_MODEL, base_url=SERVER)
    vector_db = Chroma(
        embedding_function=embeddings,
        persist_directory=DB_PATH,
        collection_name="pdf_rag_collection",
    )
    
    print(f"RAG Hybride sur : '{question}'")
    
    all_docs_data = vector_db.get()
    documents = []
    for i, content in enumerate(all_docs_data['documents']):
        doc = Document(
            page_content=content,
            metadata=all_docs_data['metadatas'][i]
        )
        documents.append(doc)
        
    bm25_retriever = BM25Retriever.from_documents(documents)
    bm25_retriever.k = 5
    
    results_bm25 = bm25_retriever.invoke(question)
    results_vector = vector_db.similarity_search(question, k=5)
    
    seen = set()
    results = []
    
    for doc in results_bm25 + results_vector:
        doc_id = doc.page_content[:100]
        if doc_id not in seen:
            seen.add(doc_id)
            results.append(doc)
            if len(results) >= 5:
                break
    
    if not results:
        return "Pas de docs", 0, []
    
    context_str = "\n".join([d.page_content for d in results])
    prompt = f"Tu es un expert. Contexte :\n{context_str}\n\nQuestion : {question}\nReponse :"
    
    reponse = query_ollama(MODEL, prompt)
    duration = time.time() - start_time
    
    sources_list = []
    for doc in results:
        meta = doc.metadata
        titre = meta.get('meta_title', 'Doc')
        if "/" in titre:
            titre = titre.split("/")[-1]
        section = meta.get('section', 'Section Inconnue')
        source_info = f"{titre} > {section}"
        sources_list.append(source_info)
    
    return reponse, duration, sources_list

# ============================================================================
# PIPELINE COMPLET
# ============================================================================

def full_pipeline():
    """
    Exécute le pipeline complet : PDF -> Markdown -> Chunks -> Base vectorielle
    """    
    pdf_files = glob.glob(os.path.join(INPUT_DIR, "*.pdf"))
    if len(pdf_files) == 0:
        print(f"\nAucun PDF trouve dans {INPUT_DIR}")
        return
    
    print(f"\n{len(pdf_files)} fichiers PDF detectes")
    
    md_files = step1_process_folder(INPUT_DIR, MD_DIR)
    if not md_files:
        return
    
    all_chunks = step2_process_folder(md_files, CHUNKS_JSON)
    vector_db = step3_create_vector_db(CHUNKS_JSON, DB_PATH)
    
    print("\n" + "-"*10)
    print("Pipeline termine")
    print("-"*10)
    print(f"{len(pdf_files)} PDFs traites")
    print(f"{len(all_chunks)} Chunks indexes")
    print(f"Base vectorielle : {DB_PATH}")


# ============================================================================
# DEMONSTRATION
# ============================================================================

def full_evaluation():
    """
    Démonstration complète avec sauvegarde détaillée pour visualisation Streamlit
    Sauvegarde en CSV et JSON pour maximum de flexibilité
    """
    questions = [
        "Quel est l'objectif principal de la mission Rosetta decrite dans le document BR-215 ?",
        "Que signifie l'acronyme NAGU dans le contexte du service Galileo Open Service (OS) ?",
        "Quelles sont les conditions (nombre de satellites, elevation) requises pour atteindre une disponibilite de 90% sur le service Galileo HAS ?",
        "En quoi consiste le 'Return Link Service' (RLS) pour un utilisateur en detresse utilisant Galileo SAR ?",
        "Quelle est la difference fondamentale d'utilisation entre le service Galileo OS (Open Service) et le service HAS ?",
        "Le service Galileo HAS est-il officiellement autorise pour des applications critiques pour la securite de la vie (safety-critical) ?",
        "Quel dysfonctionnement majeur a frappe le satellite Galileo GSAT-42 en 2026 ?"
    ]
    
    results = []
    
    for idx, q in enumerate(questions, 1):
        print(f"\n{'-'*10}")
        print(f"Question {idx}/{len(questions)} : {q}")
        print('-'*10)
        
        # Baseline
        print("\n[Baseline]")
        resp_baseline, time_baseline = run_baseline(q)
        
        # RAG
        print("\n[RAG]")
        resp_rag, time_rag, src_rag = run_rag(q)
        
        # RAG Hybrid
        print("\n[RAG Hybrid]")
        resp_rag_hybrid, time_rag_hybrid, src_rag_hybrid = run_rag_hybrid(q)

        # Reranking
        print("\n[Reranking]")
        resp_rag_rerank, time_rag_rerank, src_rag_rerank = run_rag_reranking(q)
        
        # Stockage complet des résultats
        results.append({
            'id': idx,
            'question': q,
            
            # Baseline
            'baseline_response': resp_baseline,
            'baseline_time': round(time_baseline, 2),
            'baseline_length': len(resp_baseline),
            
            # RAG
            'rag_response': resp_rag,
            'rag_time': round(time_rag, 2),
            'rag_length': len(resp_rag),
            'rag_sources_count': len(src_rag),
            'rag_sources': ' | '.join(src_rag) if src_rag else 'Aucune',
            
            # RAG Hybrid
            'rag_hybrid_response': resp_rag_hybrid,
            'rag_hybrid_time': round(time_rag_hybrid, 2),
            'rag_hybrid_length': len(resp_rag_hybrid),
            'rag_hybrid_sources_count': len(src_rag_hybrid),
            'rag_hybrid_sources': ' | '.join(src_rag_hybrid) if src_rag_hybrid else 'Aucune',

            # Reranking
            'rerank_response': resp_rag_rerank,
            'rerank_time': round(time_rag_rerank, 2),
            'rerank_length': len(resp_rag_rerank),
            'rerank_sources_count': len(src_rag_rerank),
            'rerank_sources': ' | '.join(src_rag_rerank) if src_rag_rerank else 'Aucune',
        })
    
    # Sauvegarde DataFrame
    df = pd.DataFrame(results)
    
    # Sauvegarde CSV
    df.to_csv('data/main/processed/demo_results.csv', index=False, encoding='utf-8')
    print(f"\nResultats sauvegardes dans data/main/processed/demo_results.csv")
    
    # Sauvegarde JSON
    with open('data/main/processed/demo_results.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"Resultats sauvegardes dans data/main/processed/demo_results.json")
    
    # Sauvegarde Excel
    df.to_excel('data/main/processed/demo_results.xlsx', index=False)
    print(f"Resultats sauvegardes dans data/main/processed/demo_results.xlsx")
    
    # Afficher résumé
    print("\n" + "-"*10)
    print("Résumé : ")
    print("-"*10)
    print(f"\nTemps moyen :")
    print(f"  Baseline  : {df['baseline_time'].mean():.2f}s")
    print(f"  RAG       : {df['rag_time'].mean():.2f}s")
    print(f"  RAG Hybrid: {df['rag_hybrid_time'].mean():.2f}s")
    print(f"  Reranking : {df['rerank_time'].mean():.2f}s")
    
    print(f"\nLongueur moyenne des reponses :")
    print(f"  Baseline  : {df['baseline_length'].mean():.0f} caracteres")
    print(f"  RAG       : {df['rag_length'].mean():.0f} caracteres")
    print(f"  RAG Hybrid: {df['rag_hybrid_length'].mean():.0f} caracteres")
    print(f"  Reranking : {df['rerank_length'].mean():.0f} caracteres")
    
    print(f"\nSources moyennes :")
    print(f"  RAG       : {df['rag_sources_count'].mean():.1f} sources")
    print(f"  RAG Hybrid: {df['rag_hybrid_sources_count'].mean():.1f} sources")
    print(f"  Reranking : {df['rerank_sources_count'].mean():.1f} sources")
    
    return df

# ============================================================================
# POINT D'ENTREE
# ============================================================================

if __name__ == "__main__":
    full_pipeline()
    full_evaluation()