from __future__ import (
    print_function,
    absolute_import,
)

from dbhelper import db


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True)

    # backref attributes:
    # ratings

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

    # backref attributes:
    # offerings

    def __init__(self, code, title, description, lecturer):
        self.code = code
        self.title = title
        self.description = description
        self.lecturer = lecturer

    def __repr__(self):
        return '<Course %r>' % self.code


class Offering(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    year = db.Column(db.Integer)
    session = db.Column(db.Integer)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'))
    course = db.relationship('Course', backref=db.backref('offerings', lazy='dynamic'))

    # backref attributes:
    # ratings

    def __init__(self, year, session, course):
        self.year = year
        self.session = session
        self.course = course

    def __repr__(self):
        return '<Offering %r %r %r>' % (self.course.code, self.year, self.session)


class Lecturer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80))

    # backref attributes:
    # courses

    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return '<Lecturer %r>' % self.name


class Rating(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user = db.relationship('User', backref=db.backref('ratings', lazy='dynamic'))
    offering_id = db.Column(db.Integer, db.ForeignKey('offering.id'))
    offering = db.relationship('Offering', backref=db.backref('ratings', lazy='dynamic'))
    overall_satisfaction = db.Column(db.Integer)

    def __init__(self, user, offering, overall_satisfaction):
        self.user = user
        self.offering = offering
        self.overall_satisfaction = overall_satisfaction

    def __repr__(self):
        return '<Rating from %r for %r>' % (self.user, self.offering)
