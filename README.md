# Projet RAG ESA/Galileo

Ce projet propose un pipeline complet de RAG (Retrieval-Augmented Generation) pour l’analyse, l’indexation et l’interrogation de documents techniques (PDF) liés à Galileo/ESA. Il inclut la création d’une base vectorielle, l’évaluation automatique de différentes stratégies RAG, et une interface web interactive pour le chat et la visualisation des résultats.

## Corpus de documents
Le corpus utilisé dans ce projet est composé de documents techniques au format PDF liés aux systèmes Galileo / ESA.
Ces documents constituent la base de connaissances interrogée par le pipeline RAG.
Ils contiennent principalement :
des descriptions techniques de systèmes, composants ou architectures,
des documents de référence (rapports, spécifications, notes techniques),
des contenus structurés en sections, sous-sections et paragraphes, adaptés à une exploitation par recherche sémantique.
Les documents sont automatiquement convertis en texte (Markdown), puis segmentés en chunks cohérents afin de faciliter l’indexation vectorielle et la récupération d’informations pertinentes lors des requêtes utilisateur.
Ce corpus permet ainsi de simuler un cas d’usage réaliste de RAG appliqué à des documents techniques complexes, typiques du contexte spatial et industriel (ESA/Galileo).

---

## Structure du projet

```
Projet_RAG/
├── main.py                  # Script principal (pipeline & évaluation)
├── app.py                   # Interface Streamlit (chat & analyse)
├── src/                     # Code source (modules)
│   ├── config.py
│   ├── utils.py
│   ├── rag_engine.py
│   └── pipeline_multi_docs.py
├── data/
│   ├── main/
│   │   ├── raw/             # PDFs originaux
│   │   ├── intermediate/    # Markdowns et chunks intermédiaires
│   │   └── processed/       # Chunks finaux, résultats, etc.
│   └── test/                # Données de test
├── db_multi_docs/           # Base vectorielle principale (Chroma)
├── db_local/                # Base vectorielle de test
├── requirements.txt         # Dépendances Python
└── README.md
```

---

## Installation

1. **Cloner le dépôt**
   ```bash
   git clone https://github.com/aware37/Projet_RAG.git
   cd Projet_RAG
   ```

2. **Créer un environnement virtuel et installer les dépendances**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

3. **Installer Ollama et lancer le serveur local**
   - [Ollama](https://ollama.com/) doit être installé et lancé sur `localhost:11434`.
   - Télécharger les modèles nécessaires (`mistral`, `nomic-embed-text`, etc.) via la commande Ollama.

4. **(Optionnel) Configurer la clé API dans un fichier `.env`**
   ```
   LLAMA_CLOUD_API_KEY=your_key_here
   ```

---

## Utilisation

### 1. **Pipeline de traitement et création de la base vectorielle**
Convertit les PDFs en markdown, segmente en chunks, et crée la base vectorielle Chroma.
```bash
python main.py --mode database
```

### 2. **Évaluation automatique (questions prédéfinies)**
Génère un benchmark sur plusieurs questions et sauvegarde les résultats dans `data/main/processed/demo_results.csv`.
```bash
python main.py --mode eval
```

### 3. **Tout faire (pipeline + évaluation)**
```bash
python main.py --mode all
```

### 4. **Lancer l’interface web Streamlit**
Permet de chatter avec vos documents et d’analyser les résultats.
```bash
streamlit run app.py --server.fileWatcherType none
```

---

## Fonctionnalités principales

- **Extraction** des textes PDF (via LlamaParse).
- **Segmentation avancée** en chunks avec conservation des sections.
- **Indexation vectorielle** (Ollama + ChromaDB).
- **Recherche hybride** (vectorielle + BM25).
- **Reranking** des résultats (CrossEncoder).
- **Évaluation comparative** des stratégies RAG.
- **Interface web** pour le chat et la visualisation des performances.

---

## Données

- Placez vos PDFs dans `data/main/raw/` ou `data/test/raw/`.
- Les résultats et bases vectorielles sont générés automatiquement dans les dossiers `processed/` et `db_multi_docs/` ou `db_local/`.

---

