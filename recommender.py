# recommender.py

import pandas as pd
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity


def get_recommendations(movie_id, movies, watched_ids=None):
    """
    movie_id     : int (current movie)
    movies       : list of Movie objects
    watched_ids  : list of movie IDs already watched by user
    """

    # -----------------------------
    # 1️⃣ Build dataframe
    # -----------------------------
    data = []

    for m in movies:
        combined = f"""
        {m.genre or ''}
        {m.language or ''}
        {m.cast or ''}
        {m.director or ''}
        {m.keywords or ''}
        """

        data.append({
            "id": m.id,
            "combined": combined
        })

    df = pd.DataFrame(data)

    # Safety check
    if df.empty or len(df) < 2:
        return []

    # -----------------------------
    # 2️⃣ Vectorize text
    # -----------------------------
    vectorizer = CountVectorizer(stop_words="english")
    vectors = vectorizer.fit_transform(df["combined"])

    # -----------------------------
    # 3️⃣ Similarity matrix
    # -----------------------------
    similarity = cosine_similarity(vectors)

    # -----------------------------
    # 4️⃣ Find current movie index
    # -----------------------------
    if movie_id not in df["id"].values:
        return []

    index = df[df["id"] == movie_id].index[0]
    scores = list(enumerate(similarity[index]))

    # -----------------------------
    # 5️⃣ BOOST using watched history
    # -----------------------------
    if watched_ids:
        for i, row in df.iterrows():
            if row["id"] in watched_ids:
                scores[i] = (scores[i][0], scores[i][1] + 0.15)

    # -----------------------------
    # 6️⃣ Sort & select top movies
    # -----------------------------
    scores = sorted(scores, key=lambda x: x[1], reverse=True)

    # Remove the same movie
    scores = [
        s for s in scores
        if df.iloc[s[0]]["id"] != movie_id
    ]

    # Take top 5
    top_scores = scores[:5]

    # -----------------------------
    # 7️⃣ Return movie IDs
    # -----------------------------
    return [df.iloc[i[0]]["id"] for i in top_scores]
