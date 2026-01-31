from langchain_text_splitters import Language, MarkdownHeaderTextSplitter, RecursiveCharacterTextSplitter
import requests
from src.config import INPUT_DIR, MD_DIR, CHUNKS_JSON, DB_PATH, EMBEDDING_MODEL, MODEL, SERVER
import os
import glob
import json
import shutil
from tqdm import tqdm
from llama_parse import LlamaParse
from langchain_core.documents import Document
from langchain_ollama import OllamaEmbeddings
from langchain_chroma import Chroma



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
