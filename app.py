import os

from flask import Flask, render_template, request, redirect, flash, jsonify
from flask import session, g
from sqlalchemy.exc import IntegrityError
from flask_debugtoolbar import DebugToolbarExtension
from flask_cors import CORS

from services import movie_search, movie_search_by_id
from forms import UserAddForm, LoginForm, UserEditForm, UserDeleteForm, MovieSearchForm
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
API_KEY = os.environ.get('API_KEY')

###############################################################################
# do this before every request!

# "g" is 

@app.before_request
def add_user_to_g():
    """If we're logged in, add curr user to Flask global."""

    # g.user will contain movies as well, since we set up the relationship in our model
    if CURR_USER_KEY in session:
        g.user = User.query.get(session[CURR_USER_KEY])

    else:
        g.user = None


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

        return redirect('/profile')

    return render_template('signup.html', form=form)


@app.route('/login', methods=["GET", "POST"])
def login():
    """Handle login of user."""

    form = LoginForm()

    if form.validate_on_submit():
        user = User.authenticate(form.username.data, form.password.data)

        if user:
            do_login(user)

            return redirect("/profile")
        
        flash("Invalid login credentials.", 'danger')
        return redirect('/login')

    return render_template('login.html', form=form)


@app.route('/logout')
def logout():
    """Handle logout of user."""

    do_logout()

    flash("You have been logged out successfully!", "success")
    return redirect('/login')


###############################################################################
# user routes

# this route should only be shown if a user is logged in!
@app.route("/profile")
def show_profile():
    """Show the current user information including the list of movies.
        With a section to add movies."""

    # if a user is NOT in the session then redirect to login
    if not g.user:
        flash("Please login!", "danger")
        return redirect("/login")

    return render_template("profile.html", user=g.user)


@app.route("/profile/edit", methods=["GET", "POST"])
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
                return redirect("/profile/edit")

            flash("Your profile has been updated!", "success")
            return redirect("/profile")

        flash("Current password incorrect!", "danger")
        return redirect("/profile/edit")

    return render_template("edit-profile.html", editForm=editForm, deleteForm=deleteForm, user=g.user)


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
            User.query.filter_by(id=g.user.id).delete()

            db.session.commit()

            do_logout()

            flash("Your profile has been deleted!", "danger")
            return redirect("/")

        flash("Incorrect password! Your profile has not been deleted!", "danger")
        return redirect("/profile/edit")
    
    return redirect("/profile/edit")


###############################################################################
# movie routes (internal api routes)

# add a movie to our db for a user
@app.route('/movie', methods=["POST"])
def add_movie():
    """Add a movie to our db.
        Extract our data based on incoming request and adjust response accordingly."""

    request_type = request.headers.get('Content-Type')

    # for requests coming from a form (our movie detail page)
    if request_type == "application/x-www-form-urlencoded":

        movie = Movie(imdb_id=request.form["imdb_id"],
                    user_id=g.user.id,
                    title=request.form["title"],
                    year =request.form["year"],
                    imdb_img=request.form["imdb_img"]
                    )
        
        try:
            db.session.add(movie)

            db.session.commit()

        except IntegrityError as exc:
            flash("Movie is already in your list!", "danger")
            return redirect("/profile")

        flash("Movie added to your list!", "success")
        return redirect("/profile")


    # for requests coming from an ajax page (our search page)
    if request_type == "application/json":

        movie = Movie(imdb_id=request.json["imdb_id"],
                    user_id=g.user.id,
                    title=request.json["title"],
                    year =request.json["year"],
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


# get the info for movie using the movie id.
# this is a hybrid of our api route.
@app.route("/movie/<movie_id>")
def get_movie_detail(movie_id):
    """Get a single movie based on the id."""

    # if a user is NOT in the session then redirect to login
    if not g.user:
        flash("Please login!", "danger")
        return redirect("/login")

    # movie data returned will be a dictionary
    movie = movie_search_by_id(movie_id)

    # check if this movie is already in our database...
    movie_in_db = Movie.query.filter_by(imdb_id=movie_id, user_id=g.user.id).first()

    # if so, then do not show the "add to my movies button" and
    # show a note saying that the movie is already in your db
    show_add = False if movie_in_db else True

    return render_template("single-movie.html", movie=movie, show_add=show_add)


# delete a movie from our user's movie list
@app.route("/movie/<movie_id>", methods=["DELETE"])
def delete_movie(movie_id):
    """Delete a movie from our db."""

    # below we delete the item in sqlalchemy, but we need db.session.commit()
    Movie.query.filter_by(imdb_id=movie_id, user_id=g.user.id).delete()

    db.session.commit()

    return jsonify({"message": "success"}, 200)


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

        for movie in results:
            if movie['imdbID'] in user_movies:
                movie["ml_inList"] = True

        # print("\n***********")
        # print("new movies result: ", results)
        # print("***********\n")

        # we use axios to make the ajax request
        return jsonify(results)
    
    return render_template("movie-search.html", form=form)


###############################################################################
# homepage

@app.route("/")
def homepage():
    """Show homepage."""
    return render_template("home.html")