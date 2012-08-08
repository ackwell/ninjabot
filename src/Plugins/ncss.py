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
	# firstly, check if any posts have been added/deleted
	count_add = len(new) - len(old)

	# now, check how many of these have been updated
	# compile a dictionary of old posts, based on a unique ID of TITLE|TIMESTAMP|AUTHOR
	generate_id = lambda post: post['title'] + '|' + post['timestamp'] + '|' + post['author']

	old_posts = dict()
	for post in old:
		unique_id = generate_id(post)
		old_posts[unique_id] = post['nposts']

	# now go through the new posts, and check for changes
	count_updates = 0
	for post in new:
		unique_id = generate_id(post)
		try:
			old_nposts = old_posts[unique_id] # this will throw a KeyError if it's a freshly added post
			new_nposts = post['nposts']
			if new_nposts > old_nposts:
				count_updates += 1
		except KeyError:
			pass

	return (count_add, count_updates)