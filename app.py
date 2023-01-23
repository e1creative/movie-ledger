import os

from flask import Flask, render_template, request, redirect, flash, jsonify
from flask import session, g
from sqlalchemy.exc import IntegrityError

# import text so we can use fstrings in our filter/sort queries
from sqlalchemy.sql import text

from flask_debugtoolbar import DebugToolbarExtension
from flask_cors import CORS

from forms import (UserAddForm, LoginForm, UserEditForm, 
                    UserDeleteForm, MovieSearchForm, MovieAddEditForm )
from models import db, connect_db, User, Movie
from services import movie_search, movie_search_by_id

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

    Create new user and add to DB. Redirect to /movie-search.

    If form not valid, present form.

    If the there already is a user with that username: flash message
    and re-present form.
    """

    form = UserAddForm()

    if form.validate_on_submit():
        try:
            # send our user info to be registered
            u = User.signup(
                username=form.username.data,
                password=form.password.data,
                email=form.email.data,
                img_url=form.img_url.data # or User.img_url.default.arg
            )

            db.session.commit()

            # after db.session.commit() the user will contain the id from our db
            do_login(u)

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
    """Handle login of user.
    
    Authenticate credentials and redirect to the movies page.
    """

    form = LoginForm()

    if form.validate_on_submit():
        u = User.authenticate(form.username.data, form.password.data)

        if u:
            do_login(u)

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
        u = User.authenticate(g.user.username, editForm.password.data)

        if u:
            try:
                # we already have the user from authenticating

                # update our user with the new data
                u.username = editForm.username.data
                u.email = editForm.email.data
                u.img_url = editForm.img_url.data

                # if user is changing passwords, hash the new pw before commiting
                if editForm.new_password.data:
                    newPW = User.hash_password(editForm.new_password.data)
                    u.password = newPW

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
        u = User.authenticate(g.user.username, deleteForm.password.data)

        if u:
            # need to use db.session.delete(obj) if we want the delete cascade to work
            db.session.delete(u)
            db.session.commit()

            do_logout()

            flash("Your profile has been deleted!", "danger")
            return redirect("/")

        flash("Incorrect password! Your profile has not been deleted!", "danger")
        return redirect("/profile")
    
    return redirect("/profile")


###############################################################################
# movie routes

@app.route('/movies', methods=["GET", "POST"])
def show_my_movies():
    """Show all users movies."""

    if not g.user:
        flash("Please login!", "danger")
        return redirect("/login")

    # initialize our **kwargs for filter_by()
    kwargs = {"user_id": g.user.id}

    # initalize our filter flags list to pass to our template
    filters = {}

    ##############################################
    # filter check

    # if there's a filter append to our filter_by() **kwargs
    # and also add to our filter flags list arg
    if request.args.get('filter'):

        print("\n***************")
        print("Filter detected!")
        print("Args: ", request.args['filter'])
        print("***************\n")

        kwargs["favorite"] = True
        filters["filters"] = ['favorites']

    # if there's no filter, print to console and move on
    else:
        
        print("\n***************")
        print("No filter detected!")
        print("***************\n")

    ##############################################
    # sort check

    # if there's a sort option, begin our sort_str
    if request.args.get('sort'):

        print("\n***************")
        print("Sort detected!")
        print("Sort: ", request.args['sort'])
        print("***************\n")

        # initialize our sort_str
        sort_str = ""

        # append to our sort_str based on the query string arg
        # and add to our filters flags list arg
        if request.args['sort'] == "title":
            sort_str = sort_str + "title"
            filters["sort"] = 'title'
        if request.args['sort'] == "year":
            sort_str = sort_str + "year"
            filters["sort"] = 'year'
        if request.args['sort'] == "date_added":
            sort_str = sort_str + "date_added"
            filters["sort"] = 'date_added'
        if request.args['sort'] == "date_viewed":
            sort_str = sort_str + "date_viewed"
            filters["sort"] = 'date_viewed'

        # if there's an order, append the order to our sort_str
        if request.args.get("order"):

            print("\n***************")
            print("Order detected!")
            print("Order: ", request.args['order'])
            print("***************\n")                

            # ascending order
            if request.args['order'] == "asc":
                sort_str = sort_str + " asc"
                filters["order"] = 'ascending'

            # descending order
            if request.args['order'] == "desc":
                sort_str = sort_str + " desc"
                filters["order"] = 'descending'

        # if there's NO order arg, notify our console and move on
        else:
            print("\n***************")
            print("No order detected (order default)")
            print("***************\n")

        # make our final query using our built sort_str
        movies = Movie.query.filter_by(**kwargs).order_by(text(sort_str)).all()

        # be sure to pass the necessary flags to the template
        return render_template('movies.html', user=g.user, movies=movies, filters=filters)

    else:
        # if there's NO sort option notify our console and move on
        print("\n***************")
        print("No sort detected")
        print("***************\n")

    # our final query with filter_by(**kwargs) only
    movies = Movie.query.filter_by(**kwargs).all()

    return render_template('movies.html', user=g.user, movies=movies, filters=filters)
    

@app.route("/movie/<movie_id>", methods=["GET", "POST"])
def handle_movie(movie_id):
    """Get a single movie based on the id.
    Add the movie if a post request is coming in.
    """

    # since this route will handle both our add function and
    # edit function, we need to pre-populate the fields with
    # both api information, as well as db information (if the
    # movie exists in our db).
    #
    # if the movie already exists in our database, we should
    # should replace the "add to ledger" button with an "update" 
    # button and a note that the movie is
    # already in our list.
    # 
    # on submission of the form, we should check to see if the
    # movie is in our db again
    #


    # if a user is NOT in the session then redirect to login
    if not g.user:
        flash("Please login!", "danger")
        return redirect("/login")


    form = MovieAddEditForm()

    # if form data is submitted (our movie detail page)
    if form.validate_on_submit():

        # update a movie
        if form.date_added.data:

            # query our movie object from the db
            m = Movie.query.filter_by(imdb_id=movie_id, user_id=g.user.id).first()
            
            # update values.  there will only be 3 that we can modify
            m.favorite=form.favorite.data
            m.platform=None if not form.platform.data else form.platform.data
            m.date_viewed=form.date_viewed.data

            db.session.commit()

            flash("Movie updated!", "success")

        # save a new movie
        else:

            # date_added will take the default from our model

            # date_viewed will be set to None <class 'NoneType'> if user doesn't
            #   add a date so our db entry will be empty

            # platform needs to be explicitly set to None <class 'NoneType'>
            #   if no data is sent because wtforms sends us an empty string
            #   for value="" (different than date_viewed) and sqlalchemy will
            #   store that empty string in our db.

            m = Movie(imdb_id=movie_id,
                        user_id=g.user.id,
                        title=form.title.data,
                        year=form.year.data[0:4],
                        actors=form.actors.data,
                        favorite=form.favorite.data,
                        platform=None if not form.platform.data else form.platform.data,
                        date_viewed=form.date_viewed.data,
                        imdb_img=form.imdb_img.data
                        )

            try:
                db.session.add(m)

                db.session.commit()

            except IntegrityError as exc:
                flash("Movie is already in your list!", "danger")
                return redirect("/movies")

            flash("Movie added to your list!", "success")

        return redirect("/movies")


    # for requests coming from an ajax page (our search page)
    if request.headers.get('Content-Type') == "application/json":

        # to get actors, we need to make an api call
        # our movie_id comes from the route, which is
        # created in our js code
        movie = movie_search_by_id(movie_id)

        # favorite will take the default value from our model
        # date_added will take the default from our model
        # date_viewed is optional so None <class 'NoneType'> will
        #   be our value and db field will be blank
        # platform is optional so None <class 'NoneType'> will
        #   be our value and db field will be blank
        m = Movie(imdb_id=request.json["imdb_id"],
                    user_id=g.user.id,
                    title=request.json["title"],
                    year=request.json["year"][0:4],
                    actors=movie['Actors'],
                    imdb_img=request.json["imdb_img"]
                    )

        try:
            db.session.add(m)

            db.session.commit()

        except IntegrityError as exc:
            resp = jsonify({"message": "There was an error"})
            return (resp, 400)

        # success response goes here
        resp = jsonify({"message": "Movie added to list!"})
        return (resp, 201)


    # the functionality below is placed there because we don't
    # need this functionality to run on a post request.  if we
    # placed this functionality at the top of our view function
    # we would be making unnecessary api and db calls when a
    # post request is made.

    # get the movie data from the api
    # movie data returned will be a dictionary
    movie = movie_search_by_id(movie_id)

    # update our wtform data on the front end to match the movie
    # details of the movie we are viewing, so when we submit the
    # add-movie-form our values will correct
    form.title.data=movie['Title']
    form.year.data=movie['Year']
    form.actors.data=movie['Actors']
    form.imdb_img.data=movie['Poster']

    # check if this movie is already in our database...
    # .first() returns the movie, or no movies
    movie_in_db = Movie.query.filter_by(imdb_id=movie_id, user_id=g.user.id).first()

    # if the movie is already in our ledger we can pre-populate
    # the date that is exclusive to our db into our form as well.
    # the date_added hidden field is added in wtforms as a flag
    # for our post route so we can determine if the post is a
    # new save, or an update
    if movie_in_db:
        form.favorite.data=movie_in_db.favorite
        form.platform.data=movie_in_db.platform
        form.date_viewed.data=movie_in_db.date_viewed
        form.date_added.data=movie_in_db.date_added

    return render_template("movie-detail.html", form=form, movie=movie, movie_in_db=movie_in_db)


# internal api routes
@app.route("/movie/<movie_id>", methods=["DELETE"])
def delete_movie(movie_id):
    """Delete a movie from our db."""

    # below we delete the item in sqlalchemy, but we need db.session.commit()
    Movie.query.filter_by(imdb_id=movie_id, user_id=g.user.id).delete()

    db.session.commit()

    resp = jsonify({"message": "success"})

    return (resp, 200)


# internal api routes
@app.route('/movie/<movie_id>/favorite', methods=["POST"])
def add_remove_favorite(movie_id):
    """Add or remove a movie as a favorite"""

    m = Movie.query.filter_by(user_id=g.user.id, imdb_id=movie_id).first()

    m.favorite = not m.favorite

    db.session.commit();

    # send back our boolean value for "favorite"so we can 
    # keep the front end in sync with our database data
    resp = jsonify({"message": "success", "favorite": m.favorite})

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