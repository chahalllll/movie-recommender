# Movie Recommender — OTT UI

Project highlights:
- Hybrid content-based recommendations using TF-IDF + cosine similarity
- Netflix-style responsive UI with posters, autosuggest, modal details & trailer links
- TMDB integration (posters + trailer) with local caching
- Fast fuzzy search and autosuggest for robust UX

Run locally:
1. Copy dataset to `data/movies_merged.csv` (sample provided).
2. Set TMDB key: `export TMDB_KEY="your_key"` (or PowerShell var).
3. Install: `pip install -r requirements.txt`
4. Run: `python app.py`
5. Open `http://127.0.0.1:5000`

Author: Abrar Khan — https://github.com/chahalllll
