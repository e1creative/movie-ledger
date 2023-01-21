"""Movie model tests."""

# run these tests like:
#    python -m unittest test_movie_model.py

import os
from unittest import TestCase

from models import db, Movie, User


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

class MovieModelTestCase(TestCase):
    """Test Movie model."""

    def setUp(self):
        """Create test client, add sample data."""


        # start fresh with no db
        Movie.query.delete()
        User.query.delete()


        # create  2 users in our Users model.
        u1 = User(
                username="testuser",
                email="test@test.com",
                password="HASHED_PASSWORD",
                img_url=""
            )

        u2 = User(
                username="testuser2",
                email="test@test.com",
                password="HASHED_PASSWORD",
                img_url=""
            )

        db.session.add(u1)
        db.session.add(u2)
        db.session.commit()


        self.client = app.test_client()


    def tearDown(self):
        """Rollback on exit"""

        db.session.rollback()


    def test_movie_model(self):
        """Does basic model work?"""

        # get our testuser
        u = User.query.filter_by(username="testuser").first()

        # create a movie for our user
        m = Movie(
                imdb_id="testID123",
                user_id=u.id,
                title="Test Movie",
                year="2023",
                imdb_img='http://www.test-url.com/test-directory/static/images/test.jpg'
            )

        db.session.add(m)
        db.session.commit()

        # User should have 1 movie
        self.assertEqual(len(u.movies), 1)

        # create another movie from the recently created user
        m2 = Movie(
                imdb_id="testID456",
                user_id=u.id,
                title="Test Movie 2",
                year="2023",
                imdb_img='http://www.test-url.com/test-directory/static/images/test.jpg'
            )

        db.session.add(m2)
        db.session.commit()

        # User should have 2 messages
        self.assertEqual(len(u.movies), 2)


    def test_duplicate_movie_different_user(self):
        """Can duplicate movies be added with different user id's?"""

        # get our users
        u1 = User.query.filter_by(username="testuser").first()
        u2 = User.query.filter_by(username="testuser2").first()

        # create a movie for user1
        m1 = Movie(
                imdb_id="testID456",
                user_id=u1.id,
                title="Test Movie 2",
                year="2023",
                imdb_img='http://www.test-url.com/test-directory/static/images/test.jpg'
            )

        # create the same movie for user2
        m2 = Movie(
                imdb_id="testID456",
                user_id=u2.id,
                title="Test Movie 2",
                year="2023",
                imdb_img='http://www.test-url.com/test-directory/static/images/test.jpg'
            )

        db.session.add(m1)
        db.session.add(m2)
        db.session.commit()

        # movie db should have 2 movies
        self.assertEqual(len(Movie.query.all()), 2)


    def test_fail_on_duplicate_movie_same_user(self):
        """Does movie fail on adding a duplicate movie with the same user_id?"""

        # get our users
        u = User.query.filter_by(username="testuser").first()

        user_id = u.id

        # create a movie for the user
        m1 = Movie(
                imdb_id="testID456",
                user_id=user_id,
                title="Test Movie 2",
                year="2023",
                imdb_img='http://www.test-url.com/test-directory/static/images/test.jpg'
            )

        db.session.add(m1)
        db.session.commit()

        # need to close the current session or sqlalchemy will throw an error
        db.session.close()

        # create the a movie for recently created user
        dupMovie = Movie(
                imdb_id="testID456",
                user_id=user_id,
                title="Test Movie 2",
                year="2023",
                imdb_img='http://www.test-url.com/test-directory/static/images/test.jpg'
            )

        db.session.add(dupMovie)

        # should raise an IntegrityError on commit
        from sqlalchemy.exc import IntegrityError
        self.assertRaises(IntegrityError, db.session.commit)


    def test_fail_on_nonexistent_user_id(self):
        """Does movie fail if a user_id doesn't exist in the user's table?"""

        # get the 2nd  user.  the id should be the highest id in our db.
        u2 = User.query.filter_by(username="testuser2").first()

        # create a movie from the recently created user with a user ID that doesn't exist
        m = Movie(
                imdb_id="testID456",
                user_id=u2.id+1,
                title="Test Movie 2",
                year="2023",
                imdb_img='http://www.test-url.com/test-directory/static/images/test.jpg'
            )

        db.session.add(m)

        from sqlalchemy.exc import IntegrityError
        self.assertRaises(IntegrityError, db.session.commit)


    def test_movie_user_relationship(self):
        """Does the User relationship work properly on the Movie model?"""

        # get our test user 1
        u = User.query.filter_by(username="testuser").first()

        m = Movie(
                imdb_id="testID456",
                user_id=u.id,
                title="Test Movie 2",
                year="2023",
                imdb_img='http://www.test-url.com/test-directory/static/images/test.jpg'
            )

        db.session.add(m)
        db.session.commit()

        self.assertEqual(m.user.username, u.username)


    def test_movie_user_delete(self):
        """Does the deleting a user also delete the associated movies?"""

        # get our user
        u = User.query.filter_by(username="testuser").first()

        user_id = u.id

        # create a movie associated to our user
        m = Movie(
                imdb_id="testID456",
                user_id=u.id,
                title="Test Movie 2",
                year="2023",
                imdb_img='http://www.test-url.com/test-directory/static/images/test.jpg'
            )

        db.session.add(m)
        db.session.commit()

        # delete our test user
        db.session.delete(u)
        db.session.commit()


        num_movies = Movie.query.filter_by(user_id=user_id).count()

        # there should be no movies with our user_id in our db
        self.assertEqual(num_movies, 0)
