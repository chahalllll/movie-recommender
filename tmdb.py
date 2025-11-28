import requests
import time
import os

API_KEY = os.getenv("TMDB_KEY")
BASE_URL = "https://api.themoviedb.org/3/search/movie"
IMG_BASE = "https://image.tmdb.org/t/p/w500"

def search_movie(title, year=None):
    """Stable TMDB search with retries and delay (prevents 10054 errors)."""

    if not API_KEY:
        print("TMDB KEY missing")
        return None

    params = {
        "api_key": API_KEY,
        "query": title,
        "include_adult": False
    }

    if year:
        params["year"] = year

    retries = 3

    for attempt in range(retries):
        try:
            time.sleep(1)  # ← IMPORTANT: prevent TMDB blocking
            response = requests.get(BASE_URL, params=params, timeout=8)

            if response.status_code != 200:
                print("TMDB HTTP ERROR:", response.status_code)
                continue

            data = response.json()

            if not data.get("results"):
                return None

            movie = data["results"][0]

            poster = movie.get("poster_path")
            poster_url = IMG_BASE + poster if poster else None

            return {
                "title": movie.get("title"),
                "year": movie.get("release_date", "")[:4],
                "poster_url": poster_url
            }

        except Exception as e:
            print("TMDB error:", e)
            time.sleep(2)

    return None


