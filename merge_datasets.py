# merge_datasets.py
import os
import pandas as pd
from pathlib import Path
import re

PROJECT_ROOT = Path(__file__).resolve().parent
DATA_DIR = PROJECT_ROOT / "data"
EXTRACTED_DIR = DATA_DIR / "archive_extracted"   # where you should extract the uploaded archive
BOLLYWOOD_PATH = DATA_DIR / "movies_merged.csv"  # your existing file
OUTPUT_PATH = DATA_DIR / "movies_final.csv"

def normalize_colnames(df):
    df.columns = [c.lower().strip() for c in df.columns]
    return df

def extract_year(val):
    if pd.isna(val):
        return ""
    s = str(val)
    m = re.search(r"(\d{4})", s)
    return m.group(1) if m else ""

def load_best_csv(extracted_dir):
    candidates = ["movies_metadata.csv","IMDB-Movie-Data.csv","movies.csv"]
    csv_files = []
    for root, dirs, files in os.walk(extracted_dir):
        for f in files:
            if f.lower().endswith(".csv"):
                csv_files.append(os.path.join(root, f))
    for name in candidates:
        for p in csv_files:
            if p.lower().endswith(name.lower()):
                return p
    if not csv_files:
        return None
    csv_files.sort(key=lambda p: -os.path.getsize(p))
    return csv_files[0]

def load_and_clean_hollywood(csv_path):
    print("Loading", csv_path)
    df = pd.read_csv(csv_path, low_memory=False)
    df = normalize_colnames(df)
    def pick(cols):
        for c in cols:
            if c in df.columns:
                return c
        return None

    title_col = pick(["title","name","movie"])
    overview_col = pick(["overview","description","plot","synopsis"])
    genre_col = pick(["genres","genre","listed_in"])
    date_col = pick(["release_date","year","release_year"])
    lang_col = pick(["original_language","language"])
    poster_col = pick(["poster_path","poster","poster_url","image","img","posterurl"])

    cleaned = pd.DataFrame()
    cleaned["title"] = df[title_col].astype(str) if title_col else ""
    cleaned["overview"] = df[overview_col].astype(str) if overview_col else ""
    if genre_col:
        import ast
        def parse_genres(x):
            try:
                if isinstance(x, str) and x.startswith("["):
                    parsed = ast.literal_eval(x)
                    if isinstance(parsed, list):
                        names = []
                        for item in parsed:
                            if isinstance(item, dict):
                                if "name" in item:
                                    names.append(item["name"])
                            elif isinstance(item, str):
                                names.append(item)
                        return "|".join(names)
                return str(x)
            except Exception:
                return str(x)
        cleaned["genres"] = df[genre_col].apply(parse_genres).astype(str)
    else:
        cleaned["genres"] = ""
    cleaned["year"] = df[date_col].apply(lambda x: extract_year(x)) if date_col else ""
    cleaned["language"] = df[lang_col].astype(str) if lang_col else ""
    if poster_col:
        cleaned["poster_url"] = df[poster_col].astype(str)
        cleaned["poster_url"] = cleaned["poster_url"].apply(lambda v: ("https://image.tmdb.org/t/p/w342"+v) if v and v.startswith("/") else v)
    else:
        cleaned["poster_url"] = ""
    cleaned = cleaned[["title","year","genres","overview","language","poster_url"]]
    cleaned["key"] = (cleaned["title"].str.strip().str.lower().fillna("") + "||" + cleaned["year"].fillna("").astype(str))
    cleaned = cleaned.drop_duplicates(subset=["key"])
    cleaned = cleaned.drop(columns=["key"])
    return cleaned

def load_bollywood(path):
    print("Loading bollywood file:", path)
    df = pd.read_csv(path, low_memory=False)
    df = normalize_colnames(df)
    def pick(cols):
        for c in cols:
            if c in df.columns:
                return c
        return None
    title_col = pick(["title","movie_title","name"])
    overview_col = pick(["overview","description","plot","synopsis"])
    genre_col = pick(["genres","genre"])
    year_col = pick(["year","release_year","release_date"])
    poster_col = pick(["poster_url","poster","image","img"])

    cleaned = pd.DataFrame()
    cleaned["title"] = df[title_col].astype(str) if title_col else ""
    cleaned["overview"] = df[overview_col].astype(str) if overview_col else ""
    cleaned["genres"] = df[genre_col].astype(str) if genre_col else ""
    if year_col and year_col in df.columns:
        cleaned["year"] = df[year_col].apply(lambda x: extract_year(x))
    else:
        cleaned["year"] = ""
    if poster_col and poster_col in df.columns:
        cleaned["poster_url"] = df[poster_col].astype(str)
    else:
        cleaned["poster_url"] = ""
    cleaned["language"] = df.get("language", "").astype(str) if "language" in df.columns else "hi"
    cleaned["key"] = (cleaned["title"].str.strip().str.lower().fillna("") + "||" + cleaned["year"].fillna("").astype(str))
    cleaned = cleaned.drop_duplicates(subset=["key"])
    cleaned = cleaned.drop(columns=["key"])
    return cleaned

def merge_and_save(hollywood_df, bolly_df, outpath):
    combined = pd.concat([bolly_df, hollywood_df], ignore_index=True, sort=False)
    combined["title_clean"] = combined["title"].astype(str).str.strip().str.lower()
    combined["year"] = combined["year"].fillna("").astype(str)
    combined["dedupe_key"] = combined["title_clean"] + "||" + combined["year"]
    combined["has_poster"] = combined["poster_url"].fillna("").astype(bool)
    combined["has_overview"] = combined["overview"].fillna("").astype(bool)
    combined = combined.sort_values(by=["title_clean","year","has_poster","has_overview"], ascending=[True,True,False,False])
    combined = combined.drop_duplicates(subset=["dedupe_key"], keep="first")
    final = combined[["title","year","genres","overview","language","poster_url"]].copy()
    final = final.rename(columns={"overview":"description"})
    final.to_csv(outpath, index=False, encoding="utf-8")
    print("Saved merged dataset to:", outpath, "with", len(final), "rows")

def main():
    extracted = EXTRACTED_DIR
    best_csv = load_best_csv(extracted)
    if not best_csv:
        print("No CSV found in extracted archive. Put your hollywood CSV inside data/archive_extracted and run again.")
        return
    hollywood = load_and_clean_hollywood(best_csv)
    bolly = load_bollywood(BOLLYWOOD_PATH)
    merge_and_save(hollywood, bolly, OUTPUT_PATH)

if __name__ == "__main__":
    main()
