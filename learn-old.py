#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os, re, sys, bs4
import urllib
import getpass
import http.cookiejar
from bs4 import BeautifulSoup as bs

url = 'https://learn.tsinghua.edu.cn/'
user_agent = r'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/44.0.2403.157 Safari/537.36'
headers = { 'User-Agent': user_agent, 'Connection': 'keep-alive' }

cookie = http.cookiejar.MozillaCookieJar()
handler = urllib.request.HTTPCookieProcessor(cookie)
opener = urllib.request.build_opener(handler)

def open_page(uri, values = {}):
	post_data = urllib.parse.urlencode(values).encode()
	request = urllib.request.Request(url + uri, post_data, headers)
	try:
		response = opener.open(request)
		return response
	except urllib.error.URLError as e:
		print(e.code, ':', e.reason)

def get_page(uri, values = {}):
	data = open_page(uri, values)
	if data:
		return data.read().decode()

def login(username, password):
	login_uri = 'MultiLanguage/lesson/teacher/loginteacher.jsp'
	values = { 'userid': username, 'userpass': password, 'submit1': '登陆' }
	successful = get_page(login_uri, values).find('loginteacher_action.jsp') != -1
	print('Login successfully' if successful else 'Login failed!')
	return successful

def get_courses(typepage = 1):
	soup = bs(get_page('MultiLanguage/lesson/student/MyCourse.jsp?language=cn&typepage=' + str(typepage)), 'html.parser')
	ids = soup.findAll(href=re.compile("course_id="))
	courses = []
	for link in ids:
		href = link.get('href').split('course_id=')[-1]
		name = link.text.strip()
		courses.append((href, name))
	return courses

def sync_file(path_prefix, course_id):
	if not os.path.exists(path_prefix):
		os.makedirs(path_prefix)
	soup = bs(get_page('MultiLanguage/lesson/student/download.jsp?course_id=' + str(course_id)), 'html.parser')
	for comment in soup(text=lambda text: isinstance(text, bs4.Comment)):
		link = bs(comment, 'html.parser').a
		name = link.text
		uri = comment.next.next.a.get('href')
		filename = link.get('onclick').split('getfilelink=')[-1].split('&id')[0]
		file_path = os.path.join(path_prefix, filename)
		if not os.path.exists(file_path):
			print('Download ', name)
			open(file_path, 'wb').write(open_page(uri).read())

def sync_hw(path_prefix, course_id):
	if not os.path.exists(path_prefix):
		os.makedirs(path_prefix)
	root = bs(get_page('MultiLanguage/lesson/student/hom_wk_brw.jsp?course_id=' + str(course_id)), 'html.parser')
	for ele in root.findAll('a'):
		hw_path = os.path.join(path_prefix, ele.text)
		if not os.path.exists(hw_path):
			os.makedirs(hw_path)
		soup = bs(get_page('MultiLanguage/lesson/student/' + ele.get('href')), 'html.parser')
		for link in soup.findAll('a'):
			name = 'upload-'+link.text if link.parent.previous.previous.strip() == '上交作业附件' else link.text
			uri = link.get('href')
			file_path = os.path.join(hw_path, name)
			if not os.path.exists(file_path):
				print('Download ', name)
				open(file_path, 'wb').write(open_page(uri).read())

if __name__ == '__main__':
	ignore = open('.ignore').read().split() if os.path.exists('.ignore') else []
	username = input('username: ')
	password = getpass.getpass('password: ')
	if login(username, password):
		typepage = 1 if '.py' in sys.argv[-1] else int(sys.argv[-1])
		courses = get_courses(typepage)
		for course_id, name in courses:
			if name in ignore:
				print('Skip ' + name)
			else:
				print('Sync '+ name)
				sync_file(name, course_id)
			sync_hw(name, course_id)
