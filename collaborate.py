from __future__ import (
    print_function,
    absolute_import,
)

from datetime import timedelta
import json
from flask import (
    Flask,
    Response,
    abort,
    current_app,
    jsonify,
    make_response,
    request
)
from functools import wraps, update_wrapper
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
def needs_auth(f):
    @wraps(f)
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

        return f(user, *args, **kwargs)

    return decorator


# thanks to http://flask.pocoo.org/snippets/56/
def crossdomain(origin=None, methods=None, headers=None,
                max_age=21600, attach_to_all=True,
                automatic_options=True):
    if methods is not None:
        methods = ', '.join(sorted(x.upper() for x in methods))
    if headers is not None and not isinstance(headers, basestring):  # noqa
        headers = ', '.join(x.upper() for x in headers)
    if not isinstance(origin, basestring):  # noqa
        origin = ', '.join(origin)
    if isinstance(max_age, timedelta):
        max_age = max_age.total_seconds()

    def get_methods():
        if methods is not None:
            return methods

        options_resp = current_app.make_default_options_response()
        return options_resp.headers['allow']

    def decorator(f):
        def wrapped_function(*args, **kwargs):
            if automatic_options and request.method == 'OPTIONS':
                resp = current_app.make_default_options_response()
            else:
                resp = make_response(f(*args, **kwargs))
            if not attach_to_all and request.method != 'OPTIONS':
                return resp

            h = resp.headers

            h['Access-Control-Allow-Origin'] = origin
            h['Access-Control-Allow-Methods'] = get_methods()
            h['Access-Control-Max-Age'] = str(max_age)
            if headers is not None:
                h['Access-Control-Allow-Headers'] = headers
            return resp

        f.provide_automatic_options = False
        return update_wrapper(wrapped_function, f)
    return decorator


@app.route("/get_gentrified", methods=['GET'])
@crossdomain(origin='*')
def get_gentrified():
    return jsonify(memes="spicy")


@app.route("/offerings/<offering_id>/ratings", methods=['POST'])
@needs_auth
@crossdomain(origin='*')
def post_rating(user, offering_id):
    try:
        print(request.data)
        rating_json = json.loads(request.data)
    except:
        return jsonify(error="invalid json")
    if not rating_json:
        return jsonify(error="no rating given")

    offering = Offering.query.filter_by(id=offering_id).first()
    if offering is None:
        return jsonify(error="offering not found")

    rating_json['user_id'] = user.id
    new_rating = Rating.from_json(rating_json)
    db.session.add(new_rating)
    db.session.commit()
    return jsonify()


@app.route("/offerings/<offering_id>", methods=['GET'])
@crossdomain(origin='*')
def get_offering_info(offering_id):
    offering = Offering.query.filter_by(id=offering_id).first()
    if offering is None:
        return jsonify(error="offering not found")
    offering_json = offering.to_JSON()
    offering_json['ratings'] = [rating.to_JSON(include_offering=False)
                                for rating in offering.ratings]
    return jsonify(**offering_json)


@app.route("/courses/<course_id>", methods=['GET'])
@crossdomain(origin='*')
def get_course_info(course_id):
    course = Course.query.filter_by(id=course_id).first()
    if course is None:
        return jsonify(error="course not found")
    course_json = course.to_JSON()
    course_json['offerings'] = [offering.to_JSON(include_course=False) for offering in course.offerings]
    course_json['ratings'] = course.get_aggregate_ratings()
    return jsonify(**course_json)


@app.route('/courses', methods=['GET'])
@crossdomain(origin='*')
def search_courses():
    search_query = '%' + request.args.get('q', '') + '%'
    courses = set(Course.query.filter(or_(Course.title.like(search_query),
                                          Course.code.like(search_query))).limit(10).all())
    lecturers = Lecturer.query.filter(Lecturer.name.like(search_query)).limit(5).all()
    courses.update(offering.course for lecturer in lecturers for offering in lecturer.offerings)

    resp = Response(json.dumps(list(courses), default=lambda o: o.to_JSON()))
    resp.headers['Content-Type'] = 'application/json'
    return resp


@app.route("/verify_token", methods=['GET'])
@crossdomain(origin='*')
@needs_auth
def verify_token(user):
    return "well meme'd, {}".format(user.name)

if __name__ == '__main__':
    app.run(host='0.0.0.0')
