from flask import Flask, render_template, request, redirect, url_for, abort, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import (
    LoginManager, UserMixin,
    login_user, login_required,
    logout_user, current_user
)
from werkzeug.security import generate_password_hash, check_password_hash
from recommender import get_recommendations
from werkzeug.utils import secure_filename
import os
from functools import wraps


app = Flask(__name__)
app.secret_key = "movie_secret_key"

UPLOAD_FOLDER = "static/uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_admin:
            abort(403)
        return f(*args, **kwargs)
    return decorated

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
    profile_image = db.Column(db.String(200), default="default.png")
    is_admin = db.Column(db.Boolean, default=False)



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

# ---------------- WISHLIST MODEL ----------------
class Wishlist(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    movie_id = db.Column(db.Integer, db.ForeignKey("movie.id"))

    user = db.relationship("User", backref="wishlist_items")
    movie = db.relationship("Movie")

class Rating(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    movie_id = db.Column(db.Integer, db.ForeignKey("movie.id"))
    rating = db.Column(db.Integer, nullable=False)
    review = db.Column(db.Text)   # 👈 NEW

    user = db.relationship("User")
    movie = db.relationship("Movie")


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

@app.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    if request.method == "POST":
        file = request.files.get("image")
        if file:
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
            current_user.profile_image = filename
            db.session.commit()
            flash("Profile image updated", "success")

    return render_template("profile.html")

@app.route("/admin")
@login_required
@admin_required
def admin_dashboard():
    users = User.query.all()
    movies = Movie.query.all()
    return render_template("admin/dashboard.html", users=users, movies=movies)


# ---------- ADD TO WISHLIST ----------
@app.route("/wishlist/add/<int:movie_id>")
@login_required
def add_to_wishlist(movie_id):
    existing = Wishlist.query.filter_by(
        user_id=current_user.id,
        movie_id=movie_id
    ).first()

    if not existing:
        item = Wishlist(user_id=current_user.id, movie_id=movie_id)
        db.session.add(item)
        db.session.commit()
        flash("Added to wishlist ❤️", "success")
    else:
        flash("Already in wishlist", "info")

    return redirect(request.referrer)


# ---------- VIEW WISHLIST ----------
@app.route("/wishlist")
@login_required
def wishlist():
    items = Wishlist.query.filter_by(user_id=current_user.id).all()
    return render_template("wishlist.html", items=items)


# ---------- REMOVE FROM WISHLIST ----------
@app.route("/wishlist/remove/<int:item_id>")
@login_required
def remove_from_wishlist(item_id):
    item = Wishlist.query.get_or_404(item_id)

    if item.user_id == current_user.id:
        db.session.delete(item)
        db.session.commit()
        flash("Removed from wishlist", "warning")

    return redirect(url_for("wishlist"))

@app.route("/rate/<int:movie_id>", methods=["POST"])
@login_required
def rate_movie(movie_id):
    value = int(request.form["rating"])
    review_text = request.form.get("review")

    existing = Rating.query.filter_by(
        user_id=current_user.id,
        movie_id=movie_id
    ).first()

    if existing:
        existing.rating = value
        existing.review = review_text
    else:
        r = Rating(
            user_id=current_user.id,
            movie_id=movie_id,
            rating=value,
            review=review_text
        )
        db.session.add(r)

    db.session.commit()
    flash("Rating & review saved ⭐", "success")
    return redirect(url_for("movie_detail", movie_id=movie_id))


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

    # All ratings for this movie
    ratings = Rating.query.filter_by(movie_id=movie_id).all()

    # Average rating
    avg_rating = None
    if ratings:
        avg_rating = round(
            sum(r.rating for r in ratings) / len(ratings), 1
        )

    # Recommendations (already working)
    all_movies = Movie.query.all()
    recommended_ids = get_recommendations(movie_id, all_movies)
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

    return render_template(
        "movie_detail.html",
        movie=movie,
        recommendations=recommended_movies,
        ratings=ratings,
        avg_rating=avg_rating
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
    search = request.args.get("search")
    language = request.args.get("language")
    genre = request.args.get("genre")
    year = request.args.get("year")

    query = Movie.query

    if search:
        query = query.filter(Movie.title.ilike(f"%{search}%"))

    if language:
        query = query.filter(Movie.language == language)

    if genre:
        query = query.filter(Movie.genre.ilike(f"%{genre}%"))

    if year:
        query = query.filter(Movie.release_year == year)

    movies = query.all()

    # For dropdown values
    languages = db.session.query(Movie.language).distinct().all()
    genres = db.session.query(Movie.genre).distinct().all()
    years = db.session.query(Movie.release_year).distinct().order_by(Movie.release_year.desc()).all()

    return render_template(
        "movies.html",
        movies=movies,
        languages=[l[0] for l in languages],
        genres=[g[0] for g in genres],
        years=[y[0] for y in years]
    )

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)

print(app.url_map)
print(app.url_map)

