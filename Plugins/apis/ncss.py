# NCSS Challenge API library

import json
import os.path
import re
import sys
import urllib
import urllib2

class NCSS(object):
    def __init__(self, cookie, course):
        self.cookie = cookie
        self.course = course

    def do_request(self, name, **args):
        try:
            params = {
                'course': self.course
            }
            params.update(args)
            request = urllib2.Request('http://challenge.ncss.edu.au/api/%s' % name, urllib.urlencode(params))
            request.add_header('Cookie', 'sessionid=%s;' % self.cookie)
            response = json.loads(urllib2.urlopen(request).read())
            if response['success']:
                return response
        except:
            pass
        return None

    def get_forum(self, forum_id):
        response = self.do_request('forums/threads/', forum=forum_id)
        if response:
            try:
                forum_name = response['forum']['name']
                threads = response['threads']
                return forum_name, threads
            except:
                pass
        return None

    def get_students(self):
        response = self.do_request('leader_board/')
        if response:
            try:
                all_students = dict()
                winners = []
                groups = response['groups']

                for group in groups:
                    students = group['students']
                    for student in students:
                        name = student['Name'] + ' (Year %d)' % student['Year']
                        all_students[name] = student['Score']

                return all_students
            except:
                pass
        return None

    def get_forum_list(self):
        response = self.do_request('forums/')
        ids = list()
        if response:
            try:
                forums = response['general'] + response['questions']
                for forum in forums:
                    ids.append(forum['id'])
            except:
                pass
        return ids

def generate_forum_delta(old, new):
    # now, check how many of these have been updated
    # compile a dictionary of old posts, based on a unique ID of TITLE|TIMESTAMP|AUTHOR
    generate_id = lambda post: post['title'] + '|' + post['timestamp'] + '|' + post['author']

    old_posts = dict()
    add_titles = list()
    update_titles = list()

    for post in old:
        unique_id = generate_id(post)
        old_posts[unique_id] = post

    # now go through the new posts, and check for changes
    for post in new:
        unique_id = generate_id(post)
        if unique_id not in old_posts:
            add_titles.append(post['title'])
        else:
            old_nposts = old_posts[unique_id]['nposts']
            new_nposts = post['nposts']
            if new_nposts > old_nposts:
                update_titles.append(post['title'])

    return (add_titles, update_titles)

ADDED = 1
CHANGED = 2
REMOVED = 3
def generate_students_delta(old, new):
    delta = dict()

    for name in new:
        if name not in old:
            delta[name] = (new[name], ADDED)
        elif old[name] != new[name]:
            delta[name] = (new[name], CHANGED)
    for name in old:
        if name not in new:
            delta[name] = (old[name], REMOVED)

    return delta
