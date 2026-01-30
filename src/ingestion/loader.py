import os
import arxiv
from datetime import datetime

os.makedirs('data/raw', exist_ok=True)

client = arxiv.Client()

query_string = (
    'ABSTRACT:"network slicing" OR '
    'ABSTRACT: "EcoSlice" OR '
    'ABSTRACT:"5G RAN slicing" OR '
    'ABSTRACT:"massive MIMO" OR '
    'ABSTRACT:"beamforming 5G" OR '
    'ABSTRACT:"6G architecture" OR '
    'ABSTRACT:"intelligent reflecting surface" OR '
    'ABSTRACT:"deep reinforcement learning resource allocation"'
)

search = arxiv.Search(
    query=query_string,
    max_results=100,
    sort_by=arxiv.SortCriterion.Relevance,
)

for result in client.results(search):
    # Filtre : garder uniquement les docs après 2023
    if result.published.year <= 2023:
        continue
    
    file_name = f"{result.get_short_id()}.pdf"
    file_path = os.path.join('data/raw', file_name)
    
    if not os.path.exists(file_path):
        print(f"Downloading {file_name}...")
        result.download_pdf(dirpath='data/raw', filename=file_name)
    else:
        print(f"{file_name} already exists.")

print("Download complete.")