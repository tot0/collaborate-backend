from __future__ import (
    print_function,
    absolute_import,
)

import json
from flask import Flask, abort, request
from sqlalchemy.sql.expression import or_
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
    def decorator(*args, **kwargs):
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

    return decorator


@app.route("/get_gentrified", methods=['GET'])
def get_gentrified():
    return json.dumps({
        "memes": "spicy"
    })


@needs_auth
@app.route("/offerings/<offering_id>/ratings", methods=['POST'])
def post_rating(user, offering_id):
    try:
        rating_json = json.loads(request.args.get('rating', ''))
    except:
        return '{"error":"invalid json"}'
    if not rating_json:
        return '{"error":"no rating given"}'

    offering = Offering.query.filter_by(id=offering_id).first()
    if offering is None:
        return '{"error":"offering not found"}'

    new_rating = Rating.from_json(rating_json)
    new_rating['user_id'] = user.id
    db.session.add(new_rating)
    db.session.commit()
    return '{}'


@app.route("/offerings/<offering_id>", methods=['GET'])
def get_offering_info(offering_id):
    offering = Offering.query.filter_by(id=offering_id).first()
    if offering is None:
        return '{"error":"offering not found"}'
    offering_json = offering.to_JSON()
    offering_json['ratings'] = [rating.to_JSON(include_offering=False)
                                for rating in offering.ratings]
    return json.dumps(offering_json)


@app.route("/courses/<course_id>", methods=['GET'])
def get_course_info(course_id):
    course = Course.query.filter_by(id=course_id).first()
    if course is None:
        return '{"error":"course not found"}'
    course_json = course.to_JSON()
    course_json['offerings'] = [offering.to_JSON(include_course=False) for offering in course.offerings]
    return json.dumps(course_json)


@app.route('/courses', methods=['GET'])
def search_courses():
    search_query = '%' + request.args.get('q', '') + '%'
    courses = set(Course.query.filter(or_(Course.title.like(search_query),
                                          Course.code.like(search_query))).limit(10).all())
    lecturers = Lecturer.query.filter(Lecturer.name.like(search_query)).limit(5).all()
    courses.update(offering.course for lecturer in lecturers for offering in lecturer.offerings)
    return json.dumps(list(courses), default=lambda o: o.to_JSON())


@app.route("/test_db", methods=['GET'])
def test_db():
    admin = User('admin', 1234)
    dome = User('dome', 2134)
    db.session.add(admin)
    db.session.add(dome)
    db.session.commit()
    users = User.query.all()

    wobcke = Lecturer('Wayne Wobcke')
    db.session.add(wobcke)
    db.session.commit()
    lecturers = Lecturer.query.all()

    comp2911 = Course('COMP2911', 'Engineering Design in Computing')
    db.session.add(comp2911)
    db.session.commit()
    courses = Course.query.all()

    comp2911y2016s2 = Offering(comp2911.id, 'memes', wobcke.id, 2016, 2)
    db.session.add(comp2911y2016s2)
    db.session.commit()
    offerings = Offering.query.all()

    rating = Rating(dome.id, comp2911y2016s2.id, 1, 'this is the worst course I\'ve ever done')
    db.session.add(rating)
    db.session.commit()
    ratings = Rating.query.all()

    le_return = json.dumps({
        'users': [user.name for user in users],
        'lecturers': [lec.name for lec in lecturers],
        'courses': [[course.code, course.title, ] for course in courses],
        'offerings': [[offering.course.code, offering.description, offering.lecturer.name, offering.year, offering.semester] for offering in offerings],
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


@needs_auth
@app.route("/verify_token", methods=['GET'])
def verify_token(user):
    return "well meme'd, {}".format(user.name)

if __name__ == '__main__':
    app.run(host='0.0.0.0')
