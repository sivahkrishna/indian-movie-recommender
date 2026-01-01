import csv
from app import db, Movie, app

with app.app_context():
    with open("dataset/movies.csv", encoding="utf-8") as file:
        reader = csv.DictReader(file)

        for row in reader:
            movie = Movie(
                title=row["title"],
                language=row["language"],
                genre=row["genre"],
                keywords=row["keywords"],
                cast=row["cast"],
                director=row["director"],
                description=row["description"],
                release_year=int(row["release_year"]),
                poster=row["poster"]
            )
            db.session.add(movie)

        db.session.commit()
        print("✅ Dataset imported successfully")
