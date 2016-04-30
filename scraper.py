#!/usr/bin/env python2.7

import urllib2
import re
import sys
import os

from config import *

UG = 'undergraduate'
PG = 'postgraduate'
LEVELS = [UG, PG]

TT_TO_HB_LEVEL = {
    'Undergraduate': UG,
    'Postgraduate': PG
}

def scrape_all(year):
    url = 'http://www.timetable.unsw.edu.au/%d/COMPKENS.html' % year
    print '  Reading course codes for %d' % year
    data = urllib2.urlopen(url).read()

    sections = re.split(r'<a name="([A-Z]{4})"></a>', data)
    for section in sections:
        # try and find out what section this is...
        m = re.search(r'<td class="classSearchMinorHeading" colspan="2"> ([a-zA-Z]+) </td>', section)
        if m:
            tt_level = m.group(1)

            if tt_level in TT_TO_HB_LEVEL:
                level = TT_TO_HB_LEVEL[tt_level]

                # scrape shit with this level
                courses = re.findall(r'<a href="(COMP[0-9]{4})\.html">\1</a>', section)

                print '  Found %d %s courses' % (len(courses), level)

                for course in courses:
                    # timetable is guaranteed to be there (after all, course codes come from the timetable)
                    # but handbook isn't...
                    success = scrape_handbook(course, level, year)
                    if not success:
                        # don't get timetable if handbook fails
                        continue

                    scrape_timetable(course, year)

    print

def scrape_handbook(course, level, year):
    filename = '%s/%d/%s.html' % (COURSES_DIR, year, course)
    if os.path.exists(filename):
        #print 'Skipping handbook entry for %s (%s)' % (course, level)
        return True

    print '    Fetching handbook entry for %s (%s)' % (course, level)

    url = 'http://www.handbook.unsw.edu.au/%s/courses/%d/%s.html' % (level, year, course)
    try:
        data = urllib2.urlopen(url).read()
    except Exception as e:
        print '      FAILED:', e.message
        return False

    #print 'Writing to %s' % filename
    try:
        f = open(filename, 'w')
        f.write(data)
        f.close()
    except Exception as e:
        print '      FAILED:', e.message
        return False

    return True

def scrape_timetable(course, year):
    filename = '%s/%d/%s.html' % (TIMETABLE_DIR, year, course)
    if os.path.exists(filename):
        #print 'Skipping timetable for %s' % course
        return True

    url = 'http://www.timetable.unsw.edu.au/%d/%s.html' % (year, course)

    print '    Fetching timetable for %s' % course
    try:
        data = urllib2.urlopen(url).read()
    except Exception as e:
        print '      FAILED:', e.message
        return False

    #print 'Writing to %s' % filename
    try:
        f = open(filename, 'w')
        f.write(data)
        f.close()
    except Exception as e:
        print '      FAILED:', e.message
        return False

    return True

def create_dir(path):
    if not os.path.exists(path):
        os.mkdir(path)

if __name__ == '__main__':
    create_dir(COURSES_DIR)
    create_dir(TIMETABLE_DIR)

    for year in xrange(MIN_YEAR, CURRENT_YEAR+1):
        create_dir('%s/%d' % (COURSES_DIR, year))
        create_dir('%s/%d' % (TIMETABLE_DIR, year))

        print 'Scraping %d' % year
        scrape_all(year)
