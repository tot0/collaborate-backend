from __future__ import (
    print_function,
    absolute_import,
)

from dbhelper import db


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True)

    def __init__(self, username):
        self.username = username

    def __repr__(self):
        return '<User %r>' % self.username


class Course(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(8), unique=True)
    title = db.Column(db.String(100))
    description = db.Column(db.Text)
    lecturer_id = db.Column(db.Integer, db.ForeignKey('lecturer.id'))
    lecturer = db.relationship('Lecturer', backref=db.backref('courses', lazy='dynamic'))


class Offering(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    year = db.Column(db.Integer)
    session = db.Column(db.Integer)


class Lecturer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80))
