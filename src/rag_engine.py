import time
from langchain_chroma import Chroma
from langchain_community.retrievers import BM25Retriever
from sentence_transformers import CrossEncoder
from src.utils import query_ollama
from src.config import DB_PATH, EMBEDDING_MODEL, MODEL, SERVER
from langchain_ollama import OllamaEmbeddings
from langchain_core.documents import Document


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


def run_rag(question, db_path=DB_PATH, collection_name="multi_docs_collection", top_k=5):
    """
    RAG simple : récupère top-k, génère réponse avec contexte.
    Retourne la réponse, la durée et les sources.
    """
    start_time = time.time()
    
    # Chargement base vectorielle
    embeddings = OllamaEmbeddings(model=EMBEDDING_MODEL, base_url=SERVER)
    vector_db = Chroma(
        embedding_function=embeddings,
        persist_directory=db_path,
        collection_name=collection_name,
    )
    
    results = vector_db.similarity_search(question, k=top_k)
    
    if not results:
        return "Aucune info trouvee dans la base.", 0, []
    
    context_str = ""
    sources_list = []
    
    # Formatage des sources
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


def run_rag_reranking(question, db_path=DB_PATH, collection_name="multi_docs_collection", top_k=20, final_k=5):
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
        collection_name=collection_name
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


def run_rag_hybrid(question, db_path=DB_PATH, collection_name="multi_docs_collection"):
    """
    RAG hybride : combine BM25 et recherche vectorielle.
    Retourne la réponse, la durée et les sources.
    """
    start_time = time.time()
    
    # Chargement base vectorielle
    embeddings = OllamaEmbeddings(model=EMBEDDING_MODEL, base_url=SERVER)
    vector_db = Chroma(
        embedding_function=embeddings,
        persist_directory=db_path,
        collection_name=collection_name,
    )
    
    # Chargement des documents depuis la base vectorielle
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
    
    # Recherche hybride
    results_bm25 = bm25_retriever.invoke(question)
    results_vector = vector_db.similarity_search(question, k=5)
    
    seen = set()
    results = []
    
    # Fusion des résultats BM25 et vectoriels
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
    
    # Formatage des sources
    sources_list = []
    for doc in results:
        meta = doc.metadata
        titre = meta.get('meta_title', meta.get('source', 'Doc'))
        if "/" in titre:
            titre = titre.split("/")[-1]
        section = meta.get('section', 'Section Inconnue')
        source_info = f"{titre} > {section}"
        sources_list.append(source_info)
    
    return reponse, duration, sources_list
