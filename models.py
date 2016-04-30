from __future__ import (
    print_function,
    absolute_import,
)

from dbhelper import db


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True)
    fb_id = db.Column(db.String(80), unique=True)

    # backref attributes:
    # ratings

    def __init__(self, name, fb_id):
        self.name = name
        self.fb_id = fb_id

    def __repr__(self):
        return '<User %r>' % self.name

    def to_JSON(self):
        return {
            'id': self.id,
            'name': self.name
        }


class Course(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(8), unique=True)
    title = db.Column(db.String(100))

    # backref attributes:
    # offerings

    def __init__(self, code, title):
        self.code = code
        self.title = title

    def __repr__(self):
        return '<Course %r>' % self.code

    def to_JSON(self):
        return {
            'id': self.id,
            'code': self.code,
            'title': self.title
        }


class Offering(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'))
    course = db.relationship('Course', backref=db.backref('offerings', lazy='dynamic'))
    description = db.Column(db.Text)
    lecturer_id = db.Column(db.Integer, db.ForeignKey('lecturer.id'))
    lecturer = db.relationship('Lecturer', backref=db.backref('offerings', lazy='dynamic'))
    year = db.Column(db.Integer)
    semester = db.Column(db.Integer)

    # backref attributes:
    # ratings

    def __init__(self, course_id, description, lecturer_id, year, semester):
        self.course_id = course_id
        self.description = description
        self.lecturer_id = lecturer_id
        self.year = year
        self.semester = semester

    def __repr__(self):
        return '<Offering %r %r %r>' % (self.course.code, self.year, self.semester)

    def to_JSON(self, include_course=True):
        offering_json = {
            'id': self.id,
            'description': self.description,
            'lecturer': self.lecturer.to_JSON(),
            'year': self.year,
            'semester': self.semester
        }

        if include_course:
            offering_json['course'] = self.course.to_JSON()

        return offering_json


class Lecturer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80))

    # backref attributes:
    # offerings

    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return '<Lecturer %r>' % self.name

    def to_JSON(self):
        return {
            'id': self.id,
            'name': self.name
        }


class Rating(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user = db.relationship('User', backref=db.backref('ratings', lazy='dynamic'))
    offering_id = db.Column(db.Integer, db.ForeignKey('offering.id'))
    offering = db.relationship('Offering', backref=db.backref('ratings', lazy='dynamic'))
    overall_satisfaction = db.Column(db.Integer)
    comment = db.Column(db.Text)

    def __init__(self, user_id, offering_id, overall_satisfaction, comment):
        self.user_id = user_id
        self.offering_id = offering_id
        self.overall_satisfaction = overall_satisfaction
        self.comment = comment

    @classmethod
    def from_json(cls, json):
        return cls(json['user_id'],
                   json['offering_id'],
                   json['overall_satisfaction'],
                   json['comment'])

    def __repr__(self):
        return '<Rating from %r for %r>' % (self.user, self.offering)

    def to_JSON(self, include_offering=True):
        rating_json = {
            'id': self.id,
            'user': self.user.to_JSON(),
            'overall_satisfaction': self.overall_satisfaction,
            'comment': self.comment
        }
        if include_offering:
            rating_json['offering'] = self.offering.to_JSON()

        return rating_json
