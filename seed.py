# run using 
#   $ python seed.py

from models import db, User, Movie
from app import app

db.create_all()


##### USER #####

u1 = User(username='test', password='password', email='test@test.com', img_url='https://source.unsplash.com/random/300×300')
u2 = User(username='test2', password='password2', email='test@test.com', img_url='https://source.unsplash.com/random/300×300')

db.session.add(u1)
db.session.add(u2)

db.session.commit()
