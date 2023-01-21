"""User model tests."""

# run these tests like:
#    python -m unittest test_user_model.py

import os
from unittest import TestCase

from models import db, User, Movie


# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///movie_ledger_test"


# Now we can import app

from app import app


################################################################################
# testing config
app.config['SQLALCHEMY_ECHO'] = False


# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.create_all()


################################################################################
# tests

class UserModelTestCase(TestCase):
    """Test User model."""

    def setUp(self):
        """Create test client, add sample data."""

        # start fresh with no db entries
        User.query.delete()

        self.client = app.test_client()


    def tearDown(self):
        """Rollback on exit"""

        db.session.rollback()

    
    def test_user_model(self):
        """Does the basic user model work?"""

        u = User(
                username="testuser",
                email="test@test.com",
                password="HASHED_PASSWORD",
                img_url=""
            )

        db.session.add(u)
        db.session.commit()

        # fresh user should have no movies
        self.assertEqual(len(u.movies), 0)

        # User __repr__ should return "<User #{self.id}: {self.username}, {self.email}>
        self.assertEqual(str(u), f"<User id={u.id} username={u.username} img_url={u.img_url}>")


    def test_user_signup(self):
        """Does User.signup successfully create a new user given valid credentials?"""

        User.signup(
            username="TestUser", 
            email="test@test.com", 
            password="HASHED_PASSWORD", 
            img_url="/static/images/test.jpg"
            )
        
        db.session.commit()

        user = User.query.all()

        print("\n***************")
        print(user)
        print("***************\n")

        self.assertEqual(user, user)


    def test_user_signup_fail_username(self):
        """Does User.signup fail to create a new user if any of the validations (e.g. uniqueness, non-nullable fields) fail?"""

        User.signup(
            username="TestUser", 
            email="test@test.com", 
            password="HASHED_PASSWORD", 
            img_url="/static/images/test.jpg"
            )

        db.session.commit()
        
        u1 = User(
            username="TestUser",
            email="test1@test.com",
            password="HASHED_PASSWORD"
        )

        # this should fail because u1.username is the same as u
        db.session.add(u1)

        from sqlalchemy.exc import IntegrityError
        self.assertRaises(IntegrityError, db.session.commit)


    def test_user_authenticate(self):
        """Does User.authenticate successfully return a user when given a valid username and password?"""

        # add a user to our db to test against, use User.signup to 
        u = User.signup(
            username="TestUser", 
            email="test@test.com", 
            password="HASHED_PASSWORD", 
            img_url="/static/images/test.jpg"
            )

        db.session.commit()

        # check User.authenticate
        self.assertEqual(User.authenticate(username="TestUser", password="HASHED_PASSWORD"), u)


    def test_user_authenticate_fail_username(self):
        """Does User.authenticate fail to return a user when the username is invalid?"""

        # add a user to our db to test against, use User.signup to 
        User.signup(
            username="TestUser", 
            email="test@test.com", 
            password="HASHED_PASSWORD", 
            img_url="/static/images/test.jpg"
            )
        db.session.commit()

        self.assertEqual(User.authenticate(username="TestUser2", password="HASHED_PASSWORD"), False)


    def test_user_authenticate_fail_password(self):
        """Does User.authenticate fail to return a user when the password is invalid?"""

        # add a user to our db to test against, use User.signup to 
        User.signup(
            username="TestUser", 
            email="test@test.com", 
            password="HASHED_PASSWORD", 
            img_url="/static/images/test.jpg"
            )
        db.session.commit()

        self.assertEqual(User.authenticate(username="TestUser", password="HSHD_PWD"), False)
