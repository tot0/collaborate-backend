from __future__ import (
    print_function,
    absolute_import,
)

import json
from flask import Flask

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

if __name__ == '__main__':
    app.run()
