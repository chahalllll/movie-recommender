# recommender.py
import os, re
import pandas as pd
from fuzzywuzzy import process
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from tmdb import search_movie

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(BASE_DIR, "data", "movies_final_updated.csv")

DATA_PATH = os.path.join("data", "movies_final_updated.csv")
MIN_FUZZY = 60

if not os.path.exists(DATA_PATH):
    raise FileNotFoundError(f"Put your CSV at {DATA_PATH} (or adjust path).")

movies = pd.read_csv(DATA_PATH, encoding="latin1")
movies.columns = movies.columns.str.lower().str.strip()

# detect columns
def pick(cols):
    for c in cols:
        if c in movies.columns:
            return c
    return None

title_col = pick(["title","movie_title","name"])
overview_col = pick(["overview","description","plot","synopsis","story"])
genre_col = pick(["genres","genre","categories"])
year_col = pick(["year","release_year","release_date"])
poster_col = pick(["poster","poster_url","image","img"])

if not title_col:
    raise ValueError("No title column found in dataset.")

# ensure columns exist
if not overview_col:
    movies["overview"] = ""
    overview_col = "overview"
if not genre_col:
    movies["genres"] = ""
    genre_col = "genres"

movies[overview_col] = movies[overview_col].fillna("").astype(str)
movies[genre_col] = movies[genre_col].fillna("").astype(str)
movies[title_col] = movies[title_col].fillna("").astype(str)

def clean_text(x):
    if pd.isna(x):
        return ""
    x = str(x).lower()
    x = re.sub(r"[^a-z0-9 ]+", " ", x)
    return x

movies["combined"] = (movies[title_col].astype(str) + " " +
                      movies[overview_col].astype(str) + " " +
                      movies[genre_col].astype(str))

# TF-IDF
tfidf = TfidfVectorizer(stop_words="english", max_features=20000)
tfidf_matrix = tfidf.fit_transform(movies["combined"].values)
cosine_sim = cosine_similarity(tfidf_matrix, tfidf_matrix)
indices = pd.Series(movies.index, index=movies[title_col].str.lower()).drop_duplicates()

# populate poster_url column if missing
if "poster_url" not in movies.columns:
    movies["poster_url"] = None

def populate_missing_posters(limit=200):
    missing = movies[movies["poster_url"].isnull() | (movies["poster_url"]=="")]
    count = 0
    for idx, row in missing.iterrows():
        if count >= limit:
            break
        title = row[title_col]
        year = None
        if year_col and year_col in movies.columns:
            year = row.get(year_col)
        meta = search_movie(title, year=year)
        if meta and meta.get("poster_url"):
            movies.at[idx, "poster_url"] = meta["poster_url"]
        count += 1
    try:
        movies.to_csv(DATA_PATH, index=False)
    except Exception:
        pass

# You can call populate_missing_posters() manually if you want to fill more posters slowly.

# API helpers
def get_suggestions(query, limit=8):
    choices = movies[title_col].astype(str).tolist()
    results = process.extract(query, choices, limit=limit)
    # return just titles
    return [r[0] for r in results]

def get_recommendations_with_meta(query, top_n=12):
    if not query or str(query).strip()=="":
        return [], None, "Please enter a movie name."

    choices = movies[title_col].astype(str).tolist()
    best, score = process.extractOne(query, choices)
    if score < MIN_FUZZY:
        # return suggestion list
        suggests = process.extract(query, choices, limit=5)
        suglist = [s[0] for s in suggests]
        return [], None, f"No close match found. Did you mean: {', '.join(suglist)}?"

    idx = indices.get(best.lower())
    if idx is None:
        return [], None, "Matched title not found."

    sim_scores = list(enumerate(cosine_sim[idx]))
    sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)[1:top_n+1]

    out = []
    for i, score in sim_scores:
        r = movies.iloc[i]
        out.append({
            "title": str(r.get(title_col,"")),
            "genres": str(r.get(genre_col,"")),
            "poster_url": str(r.get("poster_url","")) if r.get("poster_url") else None,
            "year": str(r.get(year_col,"")) if year_col in movies.columns else "",
            "score": round(float(score), 3)
        })
    return out, best, None


