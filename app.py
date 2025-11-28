# app.py
from flask import Flask, request, render_template, jsonify
from recommender import get_recommendations_with_meta, get_suggestions, populate_missing_posters
from tmdb import search_movie
import os

app = Flask(__name__, template_folder="templates", static_folder="static")

@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")

# AJAX: suggestions
@app.route("/suggest", methods=["GET"])
def suggest():
    q = request.args.get("q","").strip()
    if not q:
        return jsonify({"suggestions":[]})
    s = get_suggestions(q, limit=8)
    return jsonify({"suggestions": s})

# AJAX: main recommendations (returns JSON)
@app.route("/api/recommend", methods=["POST"])
def api_recommend():
    data = request.json or {}
    q = data.get("q","").strip()
    top = int(data.get("top",12))
    results, matched, error = get_recommendations_with_meta(q, top_n=top)
    return jsonify({"results":results, "matched":matched, "error": error})

# API: movie detail via TMDB lookup (poster/trailer + more)
@app.route("/api/movie_meta", methods=["GET"])
def api_movie_meta():
    title = request.args.get("title","").strip()
    year = request.args.get("year")
    meta = search_movie(title, year=year)
    if not meta:
        return jsonify({"meta":None})
    return jsonify({"meta":meta})

if __name__ == "__main__":
    # optionally populate few posters on startup but keep limit low
    # from recommender import populate_missing_posters
    # populate_missing_posters(limit=100)
    app.run(debug=True)
