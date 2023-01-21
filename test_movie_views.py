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

        self.client = app.test_client()

        # create an initial user
        self.testuser = User.signup(username="testuser",
                                    email="test@test.com",
                                    password="testuser",
                                    img_url='')

        db.session.commit()


    def test_add_movie_by_form(self):
        """Can user add a message?"""

        with self.client as c:
            # Since we need to change the session to mimic logging in,
            # we need to use the changing-session trick:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            data = {
                'imdb_id': 'testID123',
                'title': 'Test Movie',
                'year': '2023',
                'imdb_img': 'http://www.test-url.com/test-directory/static/images/test.jpg'
            }

            resp = c.post("/movie", data=data)

            # Make sure it redirects
            self.assertEqual(resp.status_code, 302)

            movie = Movie.query.one()
            self.assertEqual(movie.imdb_id, "testID123")


    def test_add_movie_by_json(self):
        """Can user add a message?"""

        with self.client as c:
            # Since we need to change the session to mimic logging in,
            # we need to use the changing-session trick:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            json = {
                'imdb_id': 'testID123',
                'title': 'Test Movie',
                'year': '2023',
                'imdb_img': 'http://www.test-url.com/test-directory/static/images/test.jpg'
            }

            resp = c.post("/movie", json=json)

            self.assertEqual(resp.status_code, 201)
            self.assertEqual(resp.json, {"message": "Movie added to list!"})

            movie = Movie.query.one()
            self.assertEqual(movie.imdb_id, "testID123")


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
