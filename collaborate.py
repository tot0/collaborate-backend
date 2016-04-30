from __future__ import (
    print_function,
    absolute_import,
)

import json
from flask import Flask, abort, request
import requests

from dbhelper import db
from models import (
    User,
    Course,
    Offering,
    Lecturer,
    Rating,
)

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///collaborate.db'
app.config['DEBUG'] = True
db.init_app(app)


# decorator for checking access token
def needs_auth(old_func):
    def new_func(*args, **kwargs):
        try:
            token = request.headers.get('X-Access-Token')
            if not token:
                abort(401)

            r = requests.get('https://graph.facebook.com/me?access_token=%s' % token)
            j = r.json()

            name = j['name']
            fb_id = j['id']
        except:
            abort(401)

        # check if user object already exists
        user = User.query.filter_by(fb_id=fb_id).first()
        if not user:
            # create the user
            user = User(name=name, fb_id=fb_id)
        user.name = name

        db.session.add(user)
        db.session.commit()

        return old_func(user, *args, **kwargs)

    return new_func


@app.route("/get_gentrified")
def get_gentrified():
    return json.dumps({
        "memes": "spicy"
    })


@app.route("/courses/<course_code>")
def get_course_info(course_code):
    course = Course.query.filter_by(code=course_code.upper()).first()
    if course is None:
        return '{}'
    return json.dumps(course, default=lambda o: o.to_JSON())


@app.route("/test_db")
def test_db():
    admin = User('admin')
    dome = User('dome')
    db.session.add(admin)
    db.session.add(dome)
    db.session.commit()
    users = User.query.all()

    wobcke = Lecturer('Wayne Wobcke')
    db.session.add(wobcke)
    db.session.commit()
    lecturers = Lecturer.query.all()

    comp2911 = Course('COMP2911', 'Engineering Design in Computing', 'memes', wobcke)
    db.session.add(comp2911)
    db.session.commit()
    courses = Course.query.all()

    comp2911y2016s2 = Offering(comp2911, 2016, 2)
    db.session.add(comp2911y2016s2)
    db.session.commit()
    offerings = Offering.query.all()

    rating = Rating(dome, comp2911y2016s2, 1)
    db.session.add(rating)
    db.session.commit()
    ratings = Rating.query.all()

    le_return = json.dumps({
        'users': [user.name for user in users],
        'lecturers': [lec.name for lec in lecturers],
        'courses': [[course.code, course.title, course.description, course.lecturer.name] for course in courses],
        'offerings': [[offering.course.code, offering.year, offering.semester] for offering in offerings],
        'ratings': [[rating.user.name, rating.offering.course.code, rating.overall_satisfaction] for rating in ratings]
    })

    '''db.session.delete(admin)
    db.session.delete(dome)
    db.session.delete(wobcke)
    db.session.delete(comp2911)
    db.session.delete(comp2911y2016s2)
    db.session.delete(rating)
    db.session.commit()'''

    return le_return


@app.route("/verify_token")
@needs_auth
def verify_token(user):
    return "well meme'd, {}".format(user.name)

if __name__ == '__main__':
    app.run()
