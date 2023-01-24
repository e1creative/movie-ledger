"""User view tests."""

# run these tests like:
#    FLASK_ENV=production python -m unittest test_message_views.py

import os
from unittest import TestCase

from flask import session

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

db.drop_all()
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

class UserViewTestCase(TestCase):
    """Test views for users."""

    def setUp(self):
        """Create test client, add sample data."""

        Movie.query.delete()
        User.query.delete()

        self.client = app.test_client()

        # create an initial user
        self.testuser = User.signup(username="testuser",
                                    email="test@test.com",
                                    password="password",
                                    img_url="")

        db.session.commit()

        # create a movie
        self.testmovie = Movie(
                imdb_id="testID123",
                user_id=self.testuser.id,
                title="Test Movie",
                year="2023",
                imdb_img='http://www.test-url.com/test-directory/static/images/test.jpg'
            )

        db.session.add(self.testmovie)
        db.session.commit()


    def test_signup_get(self):
        """Test the signup view GET route."""
        with app.test_client() as client:
            resp = client.get('/signup')
            html = resp.get_data(as_text=True)
            
            self.assertEqual(resp.status_code, 200)
            self.assertIn('<button type="submit">Signup</button>', html)


    def test_signup_post(self):
        """ Test the signup view POST route with data."""
        with app.test_client() as client:
            # we already have a user with username "testuser"
            data = {
                'username': 'testuser2',
                'password': 'password2',
                'email': 'test2@test.com',
                'img_url': ''
            }
            resp = client.post('/signup', data=data)

            # check that our response code is the redirect coming from the view
            self.assertEqual(resp.status_code, 302)


            u = User.query.filter_by(username="testuser2").first()
            
            # check that the user that we added is added to the session
            self.assertEqual(session[CURR_USER_KEY], u.id)


    def test_login_get(self):
        """ Test the login view GET route."""
        with app.test_client() as client:
            resp = client.get('/login')
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("create an account here!", html)


    def test_login_post(self):
        """ Test the login view POST route with data."""
        with app.test_client() as client:
            data = {
                    'username': 'testuser',
                    'password': 'password'
                }
            # following the redirect to the "/" route
            resp = client.post('/login', data=data, follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            # username is test user and it should be flashed on the page for a successful redirect
            self.assertIn("testuser's Ledger", html)


    def test_logout(self):
        """ Test the logout view GET route."""

        with app.test_client() as client:
            # we should be logged in for this route, so we add our test user_id to the session
            with client.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            # following the redirect to the "/" route
            resp = client.get('/logout', follow_redirects=True)
            html = resp.get_data(as_text=True)

            # check that we are redirected to the home page
            self.assertEqual(resp.status_code, 200)
            self.assertIn("You have been logged out successfully!", html)

            # check that session has been cleared after running do_logout()
            self.assertNotIn(CURR_USER_KEY, session)


            # print("\n***************")
            # print("From test_logout(), g.user: ", g.user)
            # print("***************\n")

            # check that flask g has been cleared after running do_logout()
            # self.assertEqual(g.user, None)


    def test_user_profile_get_no_auth(self):
        """ Test that profile route is inaccessible without logging in."""
        with app.test_client() as client:
            resp = client.get('/profile', follow_redirects=True)
            html = resp.get_data(as_text=True)

            # that we are redirected to the login page
            self.assertEqual(resp.status_code, 200)
            self.assertIn('<h1>Movie Ledger Login</h1>', html)


    def test_user_profile_get(self):
        """ Test user show profile route."""
        with app.test_client() as client:
            # we should be logged in for this route, so we add our test user_id to the session
            with client.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            # check that the profile page is displayed
            resp = client.get('/profile')
            html = resp.get_data(as_text=True)

            # check our status code
            self.assertEqual(resp.status_code, 200)
            # check that our username is in the html
            self.assertIn("testuser's Profile", html)


    def test_user_profile_post_correct_pw(self):
        """ Test our edit profile POST route with correct password"""
        with app.test_client() as client:
            # we should be logged in for this route, so we add our test user_id to the session
            with client.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            # changing our profile details (except for pw)
            data = {
                'username': 'testuser2',
                'password': 'password',
                'email': 'test2@test.com',
                'img_url': ''
            }

            resp = client.post('/profile', data=data, follow_redirects=True)
            html = resp.get_data(as_text=True)

            # check that we are redirected to the profile page with our new username
            self.assertEqual(resp.status_code, 200)
            self.assertIn("testuser2's Profile", html)


    def test_user_profile_post_incorrect_pw(self):
        """ Test our edit profile POST route with incorrect password."""
        with app.test_client() as client:
            # we should be logged in for this route, so we add our test user_id to the session
            with client.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            # changing our profile details (except for pw)
            data = {
                'username': 'testuser2',
                'password': 'incorrectpassword',
                'email': 'test2@test.com',
                'img_url': ''
            }

            resp = client.post('/profile', data=data, follow_redirects=True)
            html = resp.get_data(as_text=True)

            # check that we are redirected to the profile page with our new username
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Current password incorrect!", html)


    def test_delete_user_correct_pw(self):
        """ Test profile delete POST route with the correct pw."""
        with app.test_client() as client:
            # we should be logged in for this route, so we add our test user_id to the session
            with client.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            # include correct password
            resp = client.post('/profile/delete', data={"password": "password"}, follow_redirects=True)
            html = resp.get_data(as_text=True)

            # check that we are redirected to the home page with our flash message
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Your profile has been deleted!", html)

            # check that our user has been deleted
            num_users = User.query.filter_by(id=self.testuser.id).count()
            self.assertEqual(num_users, 0)


    def test_delete_user_incorrect_pw(self):
        """ Test profile delete POST route with an incorrect pw."""
        with app.test_client() as client:
            # we should be logged in for this route, so we add our test user_id to the session
            with client.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            # include incorrect pw
            resp = client.post('/profile/delete', data={"password": "drowssap"})

            # check that we are redirected to the edit profile page
            self.assertEqual(resp.status_code, 302)

