from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import (
    LoginManager, UserMixin,
    login_user, login_required,
    logout_user, current_user
)
from werkzeug.security import generate_password_hash, check_password_hash
from recommender import get_recommendations


app = Flask(__name__)
app.secret_key = "movie_secret_key"

# Database config
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# ---------------- LOGIN MANAGER ----------------
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

# ---------------- USER MODEL ----------------
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

# ---------------- MOVIE MODEL ----------------
class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    language = db.Column(db.String(50), nullable=False)
    genre = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    cast = db.Column(db.Text, nullable=False)
    director = db.Column(db.String(100), nullable=False)
    keywords = db.Column(db.Text, nullable=False)
    release_year = db.Column(db.Integer, nullable=False)
    poster = db.Column(db.String(300), nullable=False)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ---------------- ROUTES ----------------
@app.route("/")
def home():
    return render_template("home.html")

# ---------- REGISTER ----------
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]

        if User.query.filter_by(email=email).first():
            flash("Email already registered", "danger")
            return redirect(url_for("register"))

        hashed_password = generate_password_hash(password)
        new_user = User(username=username, email=email, password=hashed_password)

        db.session.add(new_user)
        db.session.commit()

        flash("Registration successful! Please login.", "success")
        return redirect(url_for("login"))

    return render_template("register.html")

# ---------- LOGIN ----------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password, password):
            login_user(user)
            flash("Login successful", "success")
            return redirect(url_for("dashboard"))
        else:
            flash("Invalid email or password", "danger")

    return render_template("login.html")

@app.route("/add-movie", methods=["GET", "POST"])
@login_required
def add_movie():
    if request.method == "POST":
        movie = Movie(
            title=request.form["title"],
            language=request.form["language"],
            genre=request.form["genre"],
            description=request.form["description"],
            cast=request.form["cast"],
            director=request.form["director"],
            keywords=request.form["keywords"],
            release_year=request.form["release_year"],
            poster=request.form["poster"]
        )
        db.session.add(movie)
        db.session.commit()
        flash("Movie added successfully!", "success")
        return redirect(url_for("add_movie"))

    return render_template("add_movie.html")

@app.route("/movie/<int:movie_id>")
def movie_detail(movie_id):
    movie = Movie.query.get_or_404(movie_id)
    all_movies = Movie.query.all()

    print("TOTAL MOVIES IN DB:", len(all_movies))
    print("CURRENT MOVIE ID:", movie_id)

    recommended_ids = get_recommendations(movie_id, all_movies)

    print("RECOMMENDED IDS:", recommended_ids)

    recommended_movies = []
    if recommended_ids:
        movie_map = {
            m.id: m for m in Movie.query.filter(
                Movie.id.in_(recommended_ids)
            ).all()
        }
        for mid in recommended_ids:
            if mid in movie_map:
                recommended_movies.append(movie_map[mid])

    print("RECOMMENDED MOVIES TITLES:",
          [m.title for m in recommended_movies])

    return render_template(
        "movie_detail.html",
        movie=movie,
        recommendations=recommended_movies
    )

# ---------- DASHBOARD (PROTECTED) ----------
@app.route("/dashboard")
@login_required
def dashboard():
    return render_template("dashboard.html", user=current_user)

# ---------- LOGOUT ----------
@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Logged out successfully", "info")
    return redirect(url_for("login"))

@app.route("/movies")
def movies():
    all_movies = Movie.query.all()
    return render_template("movies.html", movies=all_movies)


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)

print("Recommended IDs:", recommended_ids)
print("Movies fetched:", [m.title for m in recommended_movies])
