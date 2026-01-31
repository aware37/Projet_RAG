import argparse
import os
import glob
import json
from turtle import pd
from src.config import INPUT_DIR, MD_DIR, CHUNKS_JSON, DB_PATH
from src.utils import step1_process_folder, step2_process_folder, step3_create_vector_db
from src.rag_engine import run_baseline, run_rag, run_rag_hybrid, run_rag_reranking
import pandas as pd


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


def full_evaluation():
    """
    Démonstration complète avec sauvegarde détaillée pour visualisation Streamlit
    Sauvegarde en CSV et JSON pour maximum de flexibilité
    """
    questions = [
        "Que signifie l'acronyme SAR dans le contexte du système Galileo et quel est son but principal ?",
        "Quelle est la précision horizontale (Horizontal Accuracy) visée à 95% pour le service Galileo HAS Service Level 1 (SL1) ?",
        "Quelles sont les deux méthodes de distribution des corrections HAS (SIS vs IDD) décrites dans le document HAS SDD ?",
        "Quelles informations spécifiques doit contenir le champ 'SIGNAL(S) AFFECTED' dans une notification NAGU selon le standard OS SDD ?",
        "Le service Galileo HAS est-il officiellement garanti pour des applications critiques pour la sécurité de la vie (safety-of-life) ?",
        "Comment activer la communication vocale bidirectionnelle avec les secours via le service Galileo SAR ?",
        "Quelle est la précision exacte du signal militaire américain 'GPS M-Code' selon ces rapports ?"
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


if __name__ == "__main__":
    # Utilisation d'arguments pour sélectionner le mode
    parser = argparse.ArgumentParser(description="Pipeline RAG ESA")
    
    parser.add_argument(
        "--mode", 
        choices=["database", "eval", "all"], 
        default="all",
        help="Choisir le mode : 'database' (création DB), 'eval' (test questions), ou 'all' (les deux)"
    )
    
    args = parser.parse_args()

    # Logique de sélection
    if args.mode == "database":
        print("Mode sélectionné : Création Base Vectorielle Uniquement")
        full_pipeline()
        
    elif args.mode == "eval":
        print("Mode sélectionné : Évaluation Uniquement")
        full_evaluation()
        
    else:
        print("Mode sélectionné : Tout (Base Vectorielle + Évaluation)")
        full_pipeline()
        full_evaluation()