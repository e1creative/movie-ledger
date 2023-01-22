"""Models for Movie Ledger."""

from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt

from datetime import datetime

db = SQLAlchemy()
bcrypt = Bcrypt()


def connect_db(app):
    """Connect to the database."""
    db.app = app
    db.init_app(app)


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer,
                    primary_key=True,
                    autoincrement=True)
    username = db.Column(db.String(20),
                    unique=True,
                    nullable=False)
    email = db.Column(db.Text,
                    nullable=False)
    password = db.Column(db.Text,
                    nullable=False)
    img_url = db.Column(db.String(50), 
                    default=None,
                    nullable=False)


    # define our relationship for users to movies, and backref
    #
    # the first arg in the relationship method is the class name
    # of the model we want to reference with this relationship
    movies = db.relationship('Movie', backref='user', cascade='all, delete')


    def __repr__(self):
        """Show Info about pet"""
        u = self
        return f"<User id={u.id} username={u.username} img_url={u.img_url}>"


    @classmethod
    def signup(cls, username, password, email, img_url=None):
        """Signup a user with a hashed password and return the user."""

        # hash our users password with bcrypt
        hashed = bcrypt.generate_password_hash(password)
        hashed_pwd = hashed.decode("utf8")

        # create our user object with the newly hashed password and
        # the data passed from app.py/signup
        user = User(
                username=username,
                password=hashed_pwd,
                email=email,
                img_url=img_url
            )

        db.session.add(user)

        return user   


    @classmethod
    def authenticate(cls, username, password):
        """Validate that user exists and password is correct."""

        # return user if valid, else return false
        u = User.query.filter_by(username=username).first()

        if u and bcrypt.check_password_hash(u.password, password):
            return u
        else:
            return False


    def hash_password(password):
        # hash our users password with bcrypt
        hashed = bcrypt.generate_password_hash(password)
        hashed_pwd = hashed.decode("utf8")
        return hashed_pwd



class Movie(db.Model):
    __tablename__ = "movies"

    imdb_id = db.Column(db.String(10),
                        primary_key=True)
    user_id = db.Column(db.Integer,
                        db.ForeignKey('users.id'),
                        primary_key=True)
    title = db.Column(db.Text,
                        nullable=False)
    year = db.Column(db.String(4),
                        nullable=False)
    actors = db.Column(db.Text,
                        nullable=True)
    platform = db.Column(db.Text,
                        nullable=True)
    imdb_img = db.Column(db.Text,
                        nullable=False)
    favorite = db.Column(db.Boolean,
                        default=False,
                        nullable=False)
    date_viewed = db.Column(db.Date,
                        nullable=True)
    date_added = db.Column(db.Date,
                        default=datetime.now(),
                        nullable=False)


    # define our relationship for users to movies, and backref
    #
    # the first arg in the relationship method is the class name
    # of the model we want to reference with this relationship
    # user = db.relationship('User')


    def __repr__(self):
        """Show Info about movie"""
       
        m = self
       
        return f"<Movie imdb_id={m.imdb_id} user_id={m.user_id} title={m.title} year={m.year} favorite={m.favorite} platform={m.platform}>"