import os

from flask import Flask, render_template, request, redirect, flash, jsonify
from flask import session, g
from sqlalchemy.exc import IntegrityError
from flask_debugtoolbar import DebugToolbarExtension
from flask_cors import CORS

from services import movie_search, movie_search_by_id
from forms import UserAddForm, LoginForm, UserEditForm, UserDeleteForm, MovieSearchForm, MovieAddForm
from models import db, connect_db, User, Movie

app = Flask(__name__)
cors = CORS()

# Get DB_URI from environ variable (useful for production/testing) or,
# if not set there, use development local db.
app.config['SQLALCHEMY_DATABASE_URI'] = (
    os.environ.get('DATABASE_URL', 'postgresql:///movie_ledger'))
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = True
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', "it's a secret")


connect_db(app)

toolbar = DebugToolbarExtension(app)

CURR_USER_KEY = "curr_user"

###############################################################################
# do this before every request!

@app.before_request
def add_user_to_g():
    """If we're logged in, add curr user to Flask global."""

    # g.user will contain movies as well, since we set up the relationship in our model
    if CURR_USER_KEY in session:
        g.user = User.query.get(session[CURR_USER_KEY])

    else:
        g.user = None

    # print("\n***************")
    # print("From app.before_request, g.user: ", g.user)
    # print("***************\n")

###############################################################################
# login, signup, logout

def do_login(user):
    """Log in user."""

    session[CURR_USER_KEY] = user.id


def do_logout():
    """Logout user."""

    if CURR_USER_KEY in session:
        del session[CURR_USER_KEY]


@app.route('/signup', methods=["GET", "POST"])
def signup():
    """Handle user signup.

    Create new user and add to DB. Redirect to home page.

    If form not valid, present form.

    If the there already is a user with that username: flash message
    and re-present form.
    """

    form = UserAddForm()

    if form.validate_on_submit():
        try:
            # send our user info to be registered
            user = User.signup(
                username=form.username.data,
                password=form.password.data,
                email=form.email.data,
                img_url=form.img_url.data # or User.img_url.default.arg
            )

            db.session.commit()

            # after db.session.commit() the user will contain the id from our db
            do_login(user)

        except IntegrityError:
            #
            # need to find a way to figure out which error
            #
            flash("Username already taken", 'danger')
            return render_template('/signup.html', form=form)

        return redirect('/movie-search')

    return render_template('signup.html', form=form)


@app.route('/login', methods=["GET", "POST"])
def login():
    """Handle login of user."""

    form = LoginForm()

    if form.validate_on_submit():
        user = User.authenticate(form.username.data, form.password.data)

        if user:
            do_login(user)

            return redirect("/movies")
        
        flash("Invalid login credentials.", 'danger')
        return redirect('/login')

    return render_template('login.html', form=form)


@app.route('/logout')
def logout():
    """Handle logout of user."""

    do_logout()

    flash("You have been logged out successfully!", "success")
    return redirect('/')


###############################################################################
# user routes

@app.route("/profile", methods=["GET", "POST"])
def edit_profile():
    """Show/handle the user profile editing page.  Require auth!"""

    # if a user is NOT in the session then redirect to login
    if not g.user:
        flash("Please login!", "danger")
        return redirect("/login")

    editForm = UserEditForm(obj=g.user)
    deleteForm = UserDeleteForm()

    if editForm.validate_on_submit():
        # auth check if password is correct
        user = User.authenticate(g.user.username, editForm.password.data)

        if user:
            try:
                # we already have the user from authenticating

                # update our user with the new data
                user.username = editForm.username.data
                user.email = editForm.email.data
                user.img_url = editForm.img_url.data

                # if user is changing passwords, hash the new pw before commiting
                if editForm.new_password.data:
                    newPW = User.hash_password(editForm.new_password.data)
                    user.password = newPW

                # we do not need to db.session.add() since sqlalchemy 
                # already has the user in memory        
                db.session.commit()

            except IntegrityError as exc:

                flash("Username already exists!", "danger")
                return redirect("/profile")

            flash("Your profile has been updated!", "success")
            return redirect("/profile")

        flash("Current password incorrect!", "danger")
        return redirect("/profile")

    return render_template("profile.html", editForm=editForm, deleteForm=deleteForm, user=g.user)


@app.route('/profile/delete', methods=["POST"])
def delete_profile():
    """Delete the current users information.  Require auth!"""

    # if a user is NOT in the session then redirect to login
    if not g.user:
        flash("Please login!", "danger")
        return redirect("/login")

    deleteForm = UserDeleteForm()

    if deleteForm.validate_on_submit():
        # auth check if password is correct
        user = User.authenticate(g.user.username, deleteForm.password.data)

        if user:
            # coudn't use User.query.get(id) here; had to use filter_by(). ???
            # User.query.filter_by(id=g.user.id).delete()

            # need to use db.session.delete(obj) if we want the delete cascade to work
            db.session.delete(user)
            db.session.commit()

            do_logout()

            flash("Your profile has been deleted!", "danger")
            return redirect("/")

        flash("Incorrect password! Your profile has not been deleted!", "danger")
        return redirect("/profile")
    
    return redirect("/profile")


###############################################################################
# movie routes (internal api routes)

@app.route('/movies')
def show_my_movies():
    """Show all users movies."""

    if not g.user:
        flash("Please login!", "danger")
        return redirect("/login")
    
    return render_template('movies.html', user=g.user)
    

@app.route("/movie/<movie_id>", methods=["GET", "POST"])
def handle_movie(movie_id):
    """Get a single movie based on the id.
    Add the movie if a post request is coming in.
    """

    # if a user is NOT in the session then redirect to login
    if not g.user:
        flash("Please login!", "danger")
        return redirect("/login")


    form = MovieAddForm()

    # if form data is submitted (our movie detail page)
    if form.validate_on_submit():

        movie = Movie(imdb_id=movie_id,
                    user_id=g.user.id,
                    title=request.form["title"],
                    year=request.form["year"],
                    actors=request.form['actors'],
                    imdb_img=request.form["imdb_img"]
                    )
        
        try:
            db.session.add(movie)

            db.session.commit()

        except IntegrityError as exc:
            flash("Movie is already in your list!", "danger")
            return redirect("/movies")

        flash("Movie added to your list!", "success")
        return redirect("/movies")


    # for requests coming from an ajax page (our search page)
    if request.headers.get('Content-Type') == "application/json":

        movie = Movie(imdb_id=request.json["imdb_id"],
                    user_id=g.user.id,
                    title=request.json["title"],
                    year=request.json["year"],
                    imdb_img=request.json["imdb_img"]
                    )
    
        try:
            db.session.add(movie)

            db.session.commit()

        except IntegrityError as exc:
            resp = jsonify({"message": "There was an error"})
            return (resp, 400)

        # success response goes here
        resp = jsonify({"message": "Movie added to list!"})
        return (resp, 201)


    # if the form has not been submitted (get request) then
    # load the movie info: get data from our api and pass
    # to our form

    # movie data returned will be a dictionary
    movie = movie_search_by_id(movie_id)

    # check if this movie is already in our database...
    # .first() returns the movie, or no movies
    movie_in_db = Movie.query.filter_by(imdb_id=movie_id, user_id=g.user.id).first()

    form.title.data=movie['Title']
    form.year.data=movie['Year']
    form.actors.data=movie['Actors']
    form.imdb_img.data=movie['Poster']

    return render_template("movie-detail.html", form=form, movie=movie, movie_in_db=movie_in_db)


# delete a movie from our user's movie list
@app.route("/movie/<movie_id>", methods=["DELETE"])
def delete_movie(movie_id):
    """Delete a movie from our db."""

    # below we delete the item in sqlalchemy, but we need db.session.commit()
    Movie.query.filter_by(imdb_id=movie_id, user_id=g.user.id).delete()

    db.session.commit()

    resp = jsonify({"message": "success"})

    return (resp, 200)


###############################################################################
# external api routes

# search movies from the omdb database.  must be logged in!
@app.route("/movie-search", methods=["GET", "POST"])
def search_movies():
    """Get all the movies based on a search term from form data"""
     
    # if a user is NOT in the session then redirect to login
    if not g.user:
        flash("Please login!", "danger")
        return redirect("/login")

    
    form = MovieSearchForm()

    if form.validate_on_submit():
        search_term = form.search_term.data

        # make the call to our external api
        # results will be a list from our services.py file
        results = movie_search(search_term)

        # before we send our results to the user, check if any of the
        # returned movies are already in our list and if so, set an attribute
        user_movies = [movie.imdb_id for movie in g.user.movies]

        for movie in results['Search']:
            if movie['imdbID'] in user_movies:
                movie["ml_inList"] = True

        # we use axios to make the ajax request
        resp = jsonify(results['Search'])
        
        return (resp, 200)
    
    return render_template("movie-search.html", form=form, user=g.user)


###############################################################################
# homepage

@app.route("/")
def homepage():
    """Show homepage."""
    return render_template("home.html")