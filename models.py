from __future__ import (
    print_function,
    absolute_import,
)

from sqlalchemy.sql import func

from dbhelper import db


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True)
    fb_id = db.Column(db.String(80), unique=True)
    pic = db.Column(db.String(250), unique=True)

    # backref attributes:
    # ratings

    def __init__(self, name, fb_id, pic):
        self.name = name
        self.fb_id = fb_id
        self.pic = pic

    def __repr__(self):
        return '<User %r>' % self.name

    def to_JSON(self):
        return {
            'id': self.id,
            'name': self.name,
            'pic': self.pic
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
            'title': self.title,
            'ratings': self.get_aggregate_ratings()
        }

    def get_aggregate_ratings(self):
        sems = ['sem_0', 'sem_1', 'sem_2', 'overall']

        ratings = {sem: {'num_ratings': 0.0} for sem in sems}
        sem_ratings_sums = {sem: {'sum_ratings': 0.0, 'num_recommendations': 0.0} for sem in sems}
        for offering in self.offerings:
            rating = db.session.query(func.sum(Rating.overall_satisfaction),
                                      func.count(Rating.id))\
                .filter(Rating.offering_id == offering.id).one()
            num_recommendations = db.session.query(func.count(Rating.id))\
                .filter(Rating.offering_id == offering.id, Rating.recommended == True).one()[0]  # noqa
            rating_sum, rating_count = rating
            if rating_sum is None:
                continue

            for i in xrange(3):
                if offering.semester == i:
                    sem = 'sem_%d' % i
                    ratings[sem]['num_ratings'] += rating_count
                    sem_ratings_sums[sem]['sum_ratings'] += rating_sum
                    sem_ratings_sums[sem]['num_recommendations'] += num_recommendations

                    ratings['overall']['num_ratings'] += rating_count
                    sem_ratings_sums['overall']['sum_ratings'] += rating_sum
                    sem_ratings_sums['overall']['num_recommendations'] += num_recommendations
                    break

        for sem in sems:
            if ratings[sem]['num_ratings']:
                ratings[sem]['avg_rating'] = int(sem_ratings_sums[sem]['sum_ratings'] / ratings[sem]['num_ratings'])
                ratings[sem]['percent_recommended'] = (
                    sem_ratings_sums[sem]['num_recommendations'] / ratings[sem]['num_ratings']) * 100
            else:
                ratings[sem]['avg_rating'] = 0
                ratings[sem]['percent_recommended'] = 0
        return ratings


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
            'semester': self.semester,
            'aggregated_ratings': self.get_aggregate_ratings()
        }

        if include_course:
            offering_json['course'] = self.course.to_JSON()

        return offering_json

    def get_aggregate_ratings(self, detailed=False):
        num_ratings = db.session.query(func.count(Rating.id))\
            .filter(Rating.offering_id == self.id).one()[0]
        if not num_ratings:
            ratings_json = {
                'num_ratings': 0,
                'overall_satisfaction_avg': 0,
                'percent_recommended': 0
            }
            if detailed:
                ratings_json.update({
                    'interesting_avg': 0,
                    'challenging_avg': 0,
                    'time_consuming_avg': 0,
                    'useful_avg': 0,
                    'lecture_quality_avg': 0,
                    'assessment_enjoyable_avg': 0,
                    'assessment_challenging_avg': 0,
                    'assessment_relevant_avg': 0,
                    'percent_lecture_videos': 0,
                    'percent_lecture_attendance': 0,
                    'percent_tutorial_attendance': 0
                })
            return ratings_json

        overall_satisfaction_avg = int(db.session.query(func.avg(Rating.overall_satisfaction))
                                       .filter(Rating.offering_id == self.id).one()[0])

        percent_recommended = db.session.query(func.count(Rating.id))\
            .filter(Rating.offering_id == self.id, Rating.recommended == True).one()[0] * 100.0 / num_ratings  # noqa

        ratings_json = {
            'num_ratings': num_ratings,
            'overall_satisfaction_avg': overall_satisfaction_avg,
            'percent_recommended': percent_recommended
        }

        if detailed:
            (interesting_avg,
             challenging_avg,
             time_consuming_avg,
             useful_avg,
             lecture_quality_avg,
             assessment_enjoyable_avg,
             assessment_challenging_avg,
             assessment_relevant_avg) = db.session.query(func.avg(Rating.interesting),
                                                         func.avg(Rating.challenging),
                                                         func.avg(Rating.time_consuming),
                                                         func.avg(Rating.useful),
                                                         func.avg(Rating.lecture_quality),
                                                         func.avg(Rating.assessment_enjoyable),
                                                         func.avg(Rating.assessment_challenging),
                                                         func.avg(Rating.assessment_relevant))\
                .filter(Rating.offering_id == self.id).one()

            percent_lecture_videos = db.session.query(func.count(Rating.id))\
                .filter(Rating.offering_id == self.id, Rating.lecture_videos == True).one()[0] * 100.0 / num_ratings  # noqa
            percent_lecture_attendance = db.session.query(func.count(Rating.id))\
                .filter(Rating.offering_id == self.id, Rating.lecture_attendance == True).one()[0] * 100.0 / num_ratings  # noqa
            percent_tutorial_attendance = db.session.query(func.count(Rating.id))\
                .filter(Rating.offering_id == self.id, Rating.tutorial_attendance == True).one()[0] * 100.0 / num_ratings  # noqa

            ratings_json.update({
                'interesting_avg': int(interesting_avg),
                'challenging_avg': int(challenging_avg),
                'time_consuming_avg': int(time_consuming_avg),
                'useful_avg': int(useful_avg),
                'lecture_quality_avg': int(lecture_quality_avg),
                'assessment_enjoyable_avg': int(assessment_enjoyable_avg),
                'assessment_challenging_avg': int(assessment_challenging_avg),
                'assessment_relevant_avg': int(assessment_relevant_avg),
                'percent_lecture_videos': int(percent_lecture_videos),
                'percent_lecture_attendance': int(percent_lecture_attendance),
                'percent_tutorial_attendance': int(percent_tutorial_attendance)
            })

        return ratings_json


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
