"""Movie View tests."""

# run these tests like:
#    FLASK_ENV=production python -m unittest test_message_views.py

import os
from unittest import TestCase

from models import db, connect_db, User, Movie


# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///movie_ledger_test"


# Now we can import app

from app import app, CURR_USER_KEY


# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.create_all()


################################################################################
# testing config

app.config['TESTING'] = True
app.config['DEBUG_TB_HOSTS'] = ['dont-show-debug-toolbar']
app.config['SQLALCHEMY_ECHO'] = False

# Don't have WTForms use CSRF at all, since it's a pain to test

app.config['WTF_CSRF_ENABLED'] = False


################################################################################
# tests

class MovieViewTestCase(TestCase):
    """Test views for movies."""

    def setUp(self):
        """Create test client, add sample data."""

        Movie.query.delete()
        User.query.delete()

        # create an initial user
        self.testuser = User.signup(username="testuser",
                                    email="test@test.com",
                                    password="testuser",
                                    img_url='')

        db.session.commit()

        # create an initial movie
        self.testmovie = Movie(
                imdb_id="testID123",
                user_id=self.testuser.id,
                title="Test Movie",
                year="2023",
                favorite=True,
                imdb_img='http://www.test-url.com/test-directory/static/images/test.jpg'
            )

        db.session.add(self.testmovie)
        db.session.commit()

        
        self.client = app.test_client()

    def test_movies_get_route_no_auth(self):
        """Are we redirected if not logged in?"""

        with self.client as c:
            resp = c.get("/movies")
            html = resp.get_data(as_text=True)

            # check that we are redirected if we are not logged in
            self.assertEqual(resp.status_code, 302)


    def test_movies_get_route_with_auth(self):
        """Can we retrieve list of movies."""

        with self.client as c:
            # Since we need to change the session to mimic logging in,
            # we need to use the changing-session trick:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            resp = c.get("/movies")
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            # check that our logged in username is showing up
            self.assertIn(f"{self.testuser.username}'s Ledger", html)
            # check that our movie is showing up
            self.assertIn("Test Movie", html)


    def test_movies_get_route_favorites(self):
        """Does our favorite filter work."""

        with self.client as c:
            # Since we need to change the session to mimic logging in,
            # we need to use the changing-session trick:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            resp = c.get("/movies?filter=favorites")
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            # check that our logged in username is showing up
            self.assertIn(f"{self.testuser.username}'s Ledger", html)
            # check that our movie is showing up as favorite
            self.assertIn("Test Movie", html)


    # can test sorting for /movies route, including the sorting


    def test_get_movie_detail_no_auth(self):
        """Are we redirected if we are not logged in?"""

        with self.client as c:
            resp = c.get(f"/movie/{self.testmovie.imdb_id}")

            # check that we are redirected if we are not logged in
            self.assertEqual(resp.status_code, 302)


    def test_get_movie_detail_with_auth(self):
        """Can we view movie details if we are logged in?"""

        with self.client as c:
            # Since we need to change the session to mimic logging in,
            # we need to use the changing-session trick:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            # since this will fail on our api side, we should get a 302
            resp = c.get("/movie/testID123")
            html = resp.get_data(as_text=True)

            # check that we are redirected if we are not logged in
            self.assertEqual(resp.status_code, 302)


    # def test_add_movie_by_form(self):
    #     """Can user add a movie?"""

    #     with self.client as c:
    #         # Since we need to change the session to mimic logging in,
    #         # we need to use the changing-session trick:
    #         with c.session_transaction() as sess:
    #             sess[CURR_USER_KEY] = self.testuser.id

    #         data = {
    #             'imdb_id': 'testID456',
    #             'title': 'Test Movie',
    #             'year': '2023',
    #             'imdb_img': 'http://www.test-url.com/test-directory/static/images/test.jpg'
    #         }

    #         resp = c.post("/movie/{{movieid}}", data=data)

    #         # Make sure it redirects
    #         self.assertEqual(resp.status_code, 302)

    #         movie = Movie.query.one()
    #         self.assertEqual(movie.imdb_id, "testID456")


    # def test_add_movie_by_json(self):
    #     """Can user add a message?"""

    #     with self.client as c:
    #         # Since we need to change the session to mimic logging in,
    #         # we need to use the changing-session trick:
    #         with c.session_transaction() as sess:
    #             sess[CURR_USER_KEY] = self.testuser.id

    #         json = {
    #             'imdb_id': 'testID123',
    #             'title': 'Test Movie',
    #             'year': '2023',
    #             'imdb_img': 'http://www.test-url.com/test-directory/static/images/test.jpg'
    #         }

    #         resp = c.post("/movie/movieid", json=json)

    #         self.assertEqual(resp.status_code, 201)
    #         self.assertEqual(resp.json, {"message": "Movie added to list!"})

    #         movie = Movie.query.one()
    #         self.assertEqual(movie.imdb_id, "testID123")


    def test_delete_movie_json(self):
        """Can user delete a movie?"""

        with self.client as c:
            # Since we need to change the session to mimic logging in,
            # we need to use the changing-session trick:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            m = Movie(
                imdb_id="test123",
                user_id=self.testuser.id,
                title="Test Movie",
                year="2023",
                imdb_img="http://www.test-url.com/test-directory/static/images/test.jpg"
            )

            db.session.add(m)
            db.session.commit()

            resp = c.delete(f"/movie/{m.imdb_id}")
            
            self.assertEqual(resp.status_code, 200)
            self.assertEqual(resp.json, {"message": "success"})
