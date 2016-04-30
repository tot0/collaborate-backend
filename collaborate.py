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


@app.route("/test_db")
def test_db():
    admin = User('admin')
    dome = User('dome')
    db.session.add(admin)
    db.session.add(dome)
    db.session.commit()
    users = User.query.all()
    db.session.delete(admin)
    db.session.delete(dome)
    db.session.commit()
    return json.dumps([user.username for user in users])


@app.route("/verify_token")
@needs_auth
def verify_token(user):
    return "well meme'd, {}".format(user.name)

if __name__ == '__main__':
    app.run()
