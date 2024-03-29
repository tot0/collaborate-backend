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
import urllib

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

            r = requests.get('https://graph.facebook.com/me?access_token=%s' % urllib.quote(token))
            j = r.json()
            name = j['name']
            fb_id = j['id']

            r = requests.get('https://graph.facebook.com/me/picture?redirect=false&access_token=%s' %
                             urllib.quote(token))
            j = r.json()
            pic = j['data']['url']
        except:
            abort(401)

        # check if user object already exists
        user = User.query.filter_by(fb_id=fb_id).first()
        if not user:
            # create the user
            user = User(name=name, fb_id=fb_id, pic=pic)
        user.name = name
        user.pic = pic

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

            #if headers is not None:
            #    h['Access-Control-Allow-Headers'] = headers
            h['Access-Control-Allow-Headers'] = 'X-Access-Token, Content-Type'
            return resp

        f.provide_automatic_options = False
        return update_wrapper(wrapped_function, f)
    return decorator


@app.route("/offerings/<offering_id>/ratings", methods=['POST', 'OPTIONS'])
@crossdomain(origin='*')
@needs_auth
def post_rating(user, offering_id):
    try:
        rating_json = json.loads(request.data)
    except:
        return jsonify(error="invalid json")
    if not rating_json:
        return jsonify(error="no rating given")

    offering = Offering.query.filter_by(id=offering_id).first()
    if offering is None:
        return jsonify(error="offering not found")

    existing_rating = Rating.query.filter_by(user_id=user.id,
                                             offering_id=offering_id).first()
    if existing_rating is not None:
        return jsonify(error="rating already exists")

    rating_json['user_id'] = user.id
    rating_json['offering_id'] = offering_id
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
    offering_json['aggregated_ratings'] = offering.get_aggregate_ratings(detailed=True)
    return jsonify(**offering_json)


@app.route("/courses/<course_id>", methods=['GET'])
@crossdomain(origin='*')
def get_course_info(course_id):
    course = Course.query.filter_by(id=course_id).first()
    if course is None:
        return jsonify(error="course not found")
    course_json = course.to_JSON()
    course_json['offerings'] = [offering.to_JSON(include_course=False) for offering in course.offerings]
    return jsonify(**course_json)


@app.route('/courses', methods=['GET'])
@crossdomain(origin='*')
def search_courses():
    search_query = '%' + request.args.get('q', '') + '%'
    courses = set(Course.query.filter(or_(Course.title.like(search_query),
                                          Course.code.like(search_query))).all())
    lecturers = Lecturer.query.filter(Lecturer.name.like(search_query)).all()
    courses.update(offering.course for lecturer in lecturers for offering in lecturer.offerings)

    resp = Response(json.dumps(list(courses), default=lambda o: o.to_JSON()))
    resp.headers['Content-Type'] = 'application/json'
    return resp


@app.route("/ratings/recent", methods=['GET'])
@crossdomain(origin='*')
def recent_ratings():
    try:
        count = int(request.args.get('count', 5))
    except:
        return jsonify(error="count needs to be a positive number")
    if count < 0:
        return jsonify(error="count needs to be a positive number")

    ratings = Rating.query.order_by(Rating.id.desc()).limit(count).all()
    resp = Response(json.dumps(ratings, default=lambda o: o.to_JSON()))
    resp.headers['Content-Type'] = 'application/json'
    return resp

# test endpoints, please ignore


@app.route("/get_gentrified", methods=['GET'])
@crossdomain(origin='*')
def get_gentrified():
    return jsonify(memes="spicy")


@app.route("/verify_token", methods=['GET'])
@crossdomain(origin='*')
@needs_auth
def verify_token(user):
    return "well meme'd, {}".format(user.name)

if __name__ == '__main__':
    app.run()
