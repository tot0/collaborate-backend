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

    def get_aggregate_ratings(semester):
        pass


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
    recommended = db.Column(db.Boolean)
    interesting = db.Column(db.Integer)
    challenging = db.Column(db.Integer)
    time_consuming = db.Column(db.Integer)
    useful = db.Column(db.Integer)

    lecture_quality = db.Column(db.Integer)
    lecture_videos = db.Column(db.Boolean)
    lecture_attendance = db.Column(db.Boolean)

    tutorial_attendance = db.Column(db.Boolean)

    assessment_enjoyable = db.Column(db.Integer)
    assessment_challenging = db.Column(db.Integer)
    assessment_relevant = db.Column(db.Integer)

    comment = db.Column(db.Text)

    def __init__(self, user_id, offering_id, overall_satisfaction, recommended,
                 interesting, challenging, time_consuming, useful,
                 lecture_quality, lecture_videos, lecture_attendance,
                 tutorial_attendance,
                 assessment_enjoyable, assessment_challenging, assessment_relevant,
                 comment):
        self.user_id = user_id
        self.offering_id = offering_id

        self.overall_satisfaction = overall_satisfaction
        self.recommended = recommended
        self.interesting = interesting
        self.challenging = challenging
        self.time_consuming = time_consuming
        self.useful = useful

        self.lecture_quality = lecture_quality
        self.lecture_videos = lecture_videos
        self.lecture_attendance = lecture_attendance

        self.tutorial_attendance = tutorial_attendance

        self.assessment_enjoyable = assessment_enjoyable
        self.assessment_challenging = assessment_challenging
        self.assessment_relevant = assessment_relevant

        self.comment = comment

    @classmethod
    def from_json(cls, json):
        return cls(json['user_id'],
                   json['offering_id'],
                   json['overall_satisfaction'],
                   json['recommended'],
                   json['interesting'],
                   json['challenging'],
                   json['time_consuming'],
                   json['useful'],
                   json['lecture_quality'],
                   json['lecture_videos'],
                   json['lecture_attendance'],
                   json['tutorial_attendance'],
                   json['assessment_enjoyable'],
                   json['assessment_challenging'],
                   json['assessment_relevant'],
                   json['comment'])

    def __repr__(self):
        return '<Rating from %r for %r>' % (self.user, self.offering)

    def to_JSON(self, include_offering=True):
        rating_json = {
            'id': self.id,
            'user': self.user.to_JSON(),
            'overall_satisfaction': self.overall_satisfaction,
            'recommended': self.recommended,
            'interesting': self.interesting,
            'challenging': self.challenging,
            'time_consuming': self.time_consuming,
            'useful': self.useful,
            'lecture_quality': self.lecture_quality,
            'lecture_videos': self.lecture_videos,
            'lecture_attendance': self.lecture_attendance,
            'tutorial_attendance': self.tutorial_attendance,
            'assessment_enjoyable': self.assessment_enjoyable,
            'assessment_challenging': self.assessment_challenging,
            'assessment_relevant': self.assessment_relevant,
            'comment': self.comment
        }
        if include_offering:
            rating_json['offering'] = self.offering.to_JSON()

        return rating_json
