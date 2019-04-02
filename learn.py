#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = "Trinkle23897"
__copyright__ = "Copyright (C) 2019 Trinkle23897"
__license__ = "MIT"
__email__ = "463003665@qq.com"

import os, sys, json, html, time, cgi, email, urllib, getpass, http.cookiejar
from tqdm import tqdm
from bs4 import BeautifulSoup as bs

url = 'http://learn.tsinghua.edu.cn'
user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36'
headers = {'User-Agent': user_agent, 'Connection': 'keep-alive'}
cookie = http.cookiejar.MozillaCookieJar()
handler = urllib.request.HTTPCookieProcessor(cookie)
opener = urllib.request.build_opener(handler)
urllib.request.install_opener(opener)

def open_page(uri, values={}):
    post_data = urllib.parse.urlencode(values).encode()
    request = urllib.request.Request(uri if uri.startswith('http') else url + uri, post_data, headers)
    try:
        response = opener.open(request)
        return response
    except urllib.error.URLError as e:
        print(e.code, ':', e.reason)

def get_page(uri, values={}):
    data = open_page(uri, values)
    if data:
        return data.read().decode()

def get_json(uri, values={}):
    return json.loads(get_page(uri, values))

def login(username, password):
    login_uri = 'https://id.tsinghua.edu.cn/do/off/ui/auth/login/post/bb5df85216504820be7bba2b0ae1535b/0?/login.do'
    values = {'i_user': username, 'i_pass': password, 'atOnce': 'true'}
    info = get_page(login_uri, values)
    successful = 'SUCCESS' in info
    print('User %s login successfully' % (username) if successful else 'User %s login failed!' % (username))
    if successful:
        get_page(get_page(info.split('replace("')[-1].split('");\n')[0]).split('location="')[1].split('";\r\n')[0])
    return successful

def get_courses(typepage=1):
    if typepage == 1:
        query_list = [get_json('/b/kc/zhjw_v_code_xnxq/getCurrentAndNextSemester')['result']['xnxq']]
    elif typepage == 0:
        query_list = [x for x in get_json('/b/wlxt/kc/v_wlkc_xs_xktjb_coassb/queryxnxq') if x != None]
        query_list.sort()
    else:
        print('Unknown typepage number %s' % typepage)
        return []
    courses = []
    for q in query_list:
        courses += get_json('/b/wlxt/kc/v_wlkc_xs_xkb_kcb_extend/student/loadCourseBySemesterId/%s' % q)['resultList']
    return courses

class TqdmUpTo(tqdm):
    def update_to(self, b=1, bsize=1, tsize=None):
        if tsize is not None: self.total = tsize
        self.update(b * bsize - self.n)

def escape(s):
    return html.unescape(s).replace(os.path.sep, '、').replace(':', '_').replace(' ', '').replace('\t', '')

def download(uri, name=None, title=None):
    if name is None:
        for f in os.listdir('.'):
            if f.startswith(title): # already download, not use filesize anymore
                return
        try:
            h = opener.open(urllib.request.Request(url+uri,urllib.parse.urlencode({}).encode(),headers)).headers.as_string()
            head = email.header.decode_header(h)
            if len(head) == 1:
                b, encoding = head[0]
                name = b.split('filename="')[-1].split('"')[0]
            else: # 使用文件标题作为文件名
                if head[-1][0][:3] == b'Con':
                    ext = '.' + head[-2][0].split(b'.')[-1].split(b'"')[0].decode()
                else:
                    ext = '.' + head[-1][0].split(b'.')[-1].split(b'"')[0].decode()
                name = title + ext
        except:
            print('Could not download %s due to parse filename' % title)
            return
    filename = escape(name)
    if os.path.exists(filename) or 'Connection_close' in filename:
        return
    try:
        with TqdmUpTo(ncols=150, unit='B', unit_scale=True, miniters=1, desc=filename) as t:
            urllib.request.urlretrieve(url+uri, filename=filename, reporthook=t.update_to, data=None)
    except:
        print('Could not download %s due to networking' % filename)
        return

def sync_notify(c):
    pre = os.path.join(c['kcm'], '公告')
    if not os.path.exists(pre): os.makedirs(pre)
    all = get_json('/b/wlxt/kcgg/wlkc_ggb/student/pageListXs', {'aoData': [{"name": "iDisplayLength", "value": "1000"}, {"name": "wlkcid", "value": c['wlkcid']}]})['object']['aaData']
    for n in all:
        if n['ggnrStr'] == None:
            n['ggnrStr'] = ''
        path = os.path.join(pre, escape(n['bt']) + '.txt')
        open(path, 'w').write(bs(html.unescape(n['ggnrStr']), 'html.parser').text)

def sync_file(c):
    now = os.getcwd()
    pre = os.path.join(c['kcm'], '课件')
    if not os.path.exists(pre): os.makedirs(pre)
    tabs = get_json('/b/wlxt/kj/wlkc_kjflb/student/pageList?wlkcid=%s' % c['wlkcid'])['object']['rows'] # query tab
    for t in tabs:
        files = get_json('/b/wlxt/kj/wlkc_kjxxb/student/kjxxb/%s/%s' % (t['wlkcid'], t['kjflid']))['object']
        for f in files:
            os.chdir(pre)
            download('/b/wlxt/kj/wlkc_kjxxb/student/downloadFile?sfgk=0&wjid=%s' % f[7], title=f[1])
            os.chdir(now)

def sync_hw(c):
    now = os.getcwd()
    pre = os.path.join(c['kcm'], '作业')
    if not os.path.exists(pre): os.makedirs(pre)
    data = {'aoData': [{"name": "iDisplayLength", "value": "1000"}, {"name": "wlkcid", "value": c['wlkcid']}]}
    hws = get_json('/b/wlxt/kczy/zy/student/zyListWj', data)['object']['aaData'] + get_json('/b/wlxt/kczy/zy/student/zyListYjwg', data)['object']['aaData'] + get_json('/b/wlxt/kczy/zy/student/zyListYpg', data)['object']['aaData']
    for hw in hws:
        path = os.path.join(pre, escape(hw['bt']))
        if not os.path.exists(path): os.makedirs(path)
        open(os.path.join(path, 'info.txt'), 'w').write('%s\n状态：%s\n开始时间：%s\n截止时间：%s\n上传时间：%s\n批阅状态：%s\n批阅时间：%s\n批阅内容：%s\n成绩：%s\n批阅者：%s %s\n' \
            % (hw['bt'], hw['zt'], hw['kssjStr'], hw['jzsjStr'], hw['scsjStr'], hw['pyzt'], hw['pysjStr'], hw['pynr'], hw['cj'], hw['gzzh'], hw['jsm']))
        page = bs(get_page('/f/wlxt/kczy/zy/student/viewCj?wlkcid=%s&zyid=%s&xszyid=%s' % (hw['wlkcid'], hw['zyid'], hw['xszyid'])), 'html.parser')
        files = page.findAll(class_='wdhere')
        for f in files:
            os.chdir(path) # to avoid filename too long
            download('/b/wlxt/kczy/zy/student/downloadFile/%s/%s' % (hw['wlkcid'], f.findAll('a')[-1].attrs['onclick'].split("ZyFile('")[-1][:-2]), name=f.findAll('a')[0].text)
            os.chdir(now)

if __name__ == '__main__':
    ignore = open('.ignore').read().split() if os.path.exists('.ignore') else []
    if os.path.exists('.pass'):
        username, password = open('.pass').read().split()
    else:
        username = input('username: ')
        password = getpass.getpass('password: ')
    if login(username, password):
        typepage = 1 if '.py' in sys.argv[-1] else 0 
        courses = get_courses(typepage)
        if sys.argv[-1] != '0' and typepage == 0:
            courses = [c for c in courses if c['kcm'] == sys.argv[-1]]
        for c in courses:
            c['kcm'] = escape(c['kcm'])
            if c['kcm'] in ignore:
                print('Skip ' + c['kcm'])
            else:
                print('Sync ' + c['kcm'])
                if not os.path.exists(c['kcm']): os.makedirs(c['kcm'])
                sync_notify(c)
                sync_file(c)
                sync_hw(c)
