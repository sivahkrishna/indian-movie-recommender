import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

def get_recommendations(movie_id, movies):
    """
    movie_id: selected movie id
    movies: list of Movie objects from DB
    """

    # Convert movie objects to DataFrame
    data = []
    for m in movies:
        data.append({
            "id": m.id,
            "combined": f"{m.genre} {m.language} {m.keywords} {m.cast} {m.director}"
        })

    df = pd.DataFrame(data)

    # Vectorize text
    tfidf = TfidfVectorizer(
    stop_words="english",
    ngram_range=(1, 2),
    min_df=1
    )
    vectors = tfidf.fit_transform(df["combined"])
    # Cosine similarity
    similarity = cosine_similarity(vectors)

    # Find index of selected movie
    index = df[df["id"] == movie_id].index[0]

    scores = list(enumerate(similarity[index]))
    scores = sorted(scores, key=lambda x: x[1], reverse=True)

    # Get top 5 similar movie IDs (excluding itself)
    recommended_ids = [int(df.iloc[i[0]]["id"]) for i in scores[1:6]]

    return recommended_ids
