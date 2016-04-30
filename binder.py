#!/usr/bin/env python2.7

import codecs
import os
import re

from config import *

from flask_sqlalchemy import SQLAlchemy
from collaborate import app
from models import *

from bs4 import BeautifulSoup

# woo regular expressions
NAME_RE = re.compile(r'<title>UNSW Handbook Course - (.*?) - [A-Z]{4}[0-9]{4}</title>', re.DOTALL)
DESC_RE = re.compile(r'<!-- Start Course Description -->(.*?)<!-- End Course description -->', re.DOTALL | re.IGNORECASE)

# destroy the database
if os.path.exists(DATABASE_FILENAME):
    print('Delete the database first!')
    exit(1)

from dbhelper import create_db
create_db()

db = SQLAlchemy()
with app.app_context():
    print 'Loading timetable'

    existing_courses = set()
    existing_lecturers = set()

    for year in xrange(CURRENT_YEAR, MIN_YEAR-1, -1):
        print '-'*50
        print 'YEAR:', year
        tt_directory = '%s/%d' % (TIMETABLE_DIR, year)
        hb_directory = '%s/%d' % (COURSES_DIR, year)
        filenames = os.listdir(tt_directory)
        for filename in filenames:
            course = filename.rstrip('.html')

            # read handbook entry
            f = codecs.open('%s/%s' % (hb_directory, filename), encoding='utf-8')
            data = f.read()
            f.close()

            # strip &nbsp;'s and <strong> tags
            data = data.replace('&nbsp;', ' ')
            data = data.replace('<strong>', '')
            data = data.replace('</strong>', '')

            # find name
            match = re.search(NAME_RE, data)
            if match:
                course_name = match.group(1).strip().replace('\n', '')
            else:
                course_name = None
                print "Couldn't find name"
                print 'Fatal error!'
                quit()

            # find description
            match = re.search(DESC_RE, data)
            if match:
                desc = match.group(1).strip()
            else:
                desc = None
                print "Couldn't find description"

            # add to db
            if course not in existing_courses:
                course_obj = Course(code=course, title=course_name)
                db.session.add(course_obj)
                db.session.commit()

                existing_courses.add(course)
            else:
                course_obj = Course.query.filter_by(code=course).first()

            print '  %s %s' % (course, course_name)

            # now, read timetable
            f = open('%s/%s' % (tt_directory, filename))
            data = f.read()
            f.close()

            soup = BeautifulSoup(data)

            # find staff contacts
            for session, needle in enumerate(['SUMMER TERM', 'SEMESTER ONE', 'SEMESTER TWO']):
                element = soup.find('a', string=needle)
                if element:
                    lecturer = list(element.parent.parent.next_sibling.next_sibling.children)[5].text

                    # remove duplicate spaces
                    lecturer = re.sub(r' +', ' ', lecturer)

                    print '    %s: %s' % (needle, lecturer)

                    if lecturer not in existing_lecturers:
                        lecturer_obj = Lecturer(name=lecturer)
                        db.session.add(lecturer_obj)
                        db.session.commit()
                    else:
                        lecturer_obj = Lecturer.query.filter_by(name=lecturer).first()

                    offering_obj = Offering(course_id=course_obj.id,
                                            description=desc,
                                            lecturer_id=lecturer_obj.id,
                                            year=year,
                                            semester=session)
                    db.session.add(offering_obj)
                    db.session.commit()

