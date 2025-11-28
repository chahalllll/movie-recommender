import pandas as pd

# Load dataset
ratings = pd.read_csv('data/u.data', sep='\t', names=['user_id', 'item_id', 'rating', 'timestamp'])
movies = pd.read_csv('data/u.item', sep='|', encoding='latin-1', usecols=[0, 1], names=['item_id', 'title'])

# Merge datasets
df = pd.merge(ratings, movies, on='item_id')

print("✅ Dataset loaded successfully!")
print(df.head())

# Create a user-item matrix
user_movie_matrix = df.pivot_table(index='user_id', columns='title', values='rating')

# Choose a movie for recommendation
movie_name = "Star Wars (1977)"

# Compute correlations between movies
movie_correlations = user_movie_matrix.corrwith(user_movie_matrix[movie_name])

# Sort results
similar_movies = movie_correlations.dropna().sort_values(ascending=False).head(10)

print("\n🎥 Movies similar to", movie_name, "are:\n")
print(similar_movies)
