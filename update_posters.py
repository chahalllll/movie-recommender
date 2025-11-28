import pandas as pd
import time
from tmdb import search_movie

INPUT = "data/movies_final.csv"
OUTPUT = "data/movies_final_updated.csv"

df = pd.read_csv(INPUT)
updated = 0

def clean_year(y):
    try:
        y = str(y)
        return int(y[:4])
    except:
        return None

for i, row in df.iterrows():
    if isinstance(row.get("poster_url"), str) and row["poster_url"].strip():
        continue

    title = row["title"]
    year = clean_year(row.get("year"))

    print(f"\nFetching poster → {title} ({year})")

    result = search_movie(title, year)

    if result and result.get("poster_url"):
        df.at[i, "poster_url"] = result["poster_url"]
        updated += 1
        print("✔ Poster updated")

    time.sleep(1)  # rate limit protection

df.to_csv(OUTPUT, index=False)
print("\n==============================")
print(f"UPDATED POSTERS: {updated}")
print("Saved:", OUTPUT)
