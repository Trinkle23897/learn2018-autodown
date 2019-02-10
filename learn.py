#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = "Trinkle23897"
__copyright__ = "Copyright (C) 2019 Trinkle23897"
__license__ = "MIT"
__email__ = "463003665@qq.com"

import os, sys, json, html, http, time, urllib, getpass, requests
from contextlib import closing
from bs4 import BeautifulSoup as bs

url = 'http://learn2018.tsinghua.edu.cn'
user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36'
headers = {'User-Agent': user_agent, 'Connection': 'keep-alive'}
cookie = http.cookiejar.MozillaCookieJar()
handler = urllib.request.HTTPCookieProcessor(cookie)
opener = urllib.request.build_opener(handler)
chunk_size = 1024
maxlen = 0

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
    get_page('/f/loginAccountSave', {'loginAccount': username})
    login_uri = 'https://id.tsinghua.edu.cn/do/off/ui/auth/login/post/bb5df85216504820be7bba2b0ae1535b/0?/login.do'
    values = {'i_user': username, 'i_pass': password, 'atOnce': 'true'}
    info = get_page(login_uri, values)
    successful = 'SUCCESS' in info
    print('Login successfully' if successful else 'Login failed!')
    if successful:
        get_page(get_page(info.split('replace("')[-1].split('");\n')[0]).split('location="')[1].split('";\r\n')[0])
    return successful

def get_courses(typepage=1):
    if typepage == 1:
        query_list = [get_json('/b/kc/zhjw_v_code_xnxq/getCurrentAndNextSemester')['result']['xnxq']]
    elif typepage == 0:
        query_list = get_json('/b/wlxt/kc/v_wlkc_xs_xktjb_coassb/queryxnxq')
        query_list.sort()
    else:
        print('Unknown typepage number %s' % typepage)
        return []
    courses = []
    for q in query_list:
        courses += get_json('/b/wlxt/kc/v_wlkc_xs_xkb_kcb_extend/student/loadCourseBySemesterId/%s' % q)['resultList']
    return courses

class ProgressBar():
    def __init__(self, title, total, bt):
        self.title, self.total, self.count, self.bt = title, total, 0, bt
    def refresh(self, count, nt):
        global maxlen
        self.count += count
        s = "%3.2f%%   %3.2f MB / %3.2f MB   %3.2f KB/s %s" % (100*self.count/self.total, self.count/1048576, self.total/1048576, self.count/1024/(nt-self.bt), self.title)
        print(s, end='\r')
        maxlen = max(maxlen, len(s))

def download(uri, pre, name=None):
    with closing(requests.get(url + uri, cookies=cookie, stream=True)) as r:
        try:
            filename = r.headers['Content-Disposition'].split('filename="')[-1].split('"')[0]
            filename = os.path.join(pre, html.unescape(bytearray([ord(i) for i in filename]).decode()).replace('/', '、'))
        except:
            return
        name = filename if name is None else html.unescape(name)
        try:
            filesize = int(r.headers['Content-Length'])
        except:
            filesize = 0
        if not os.path.exists(filename) or filesize != os.stat(filename).st_size and filesize > 0:
            print('Download %s %s' % (name, ' '*(maxlen - len(name))))
            if filesize > 0: progress = ProgressBar(filename, filesize, time.time())
            with open(filename, "wb") as file:
                for data in r.iter_content(chunk_size=chunk_size):
                    length = file.write(data)
                    if filesize > 0: progress.refresh(length, time.time())

def sync_notify(c):
    pre = os.path.join(c['kcm'], '公告')
    if not os.path.exists(pre): os.makedirs(pre)
    all = get_json('/b/wlxt/kcgg/wlkc_ggb/student/pageListXs', {'aoData': [{"name": "iDisplayLength", "value": "1000"}, {"name": "wlkcid", "value": c['wlkcid']}]})['object']['aaData']
    for n in all:
        path = os.path.join(pre, html.unescape(n['bt']).replace('/', '、') + '.txt')
        open(path, 'w').write(bs(html.unescape(n['ggnrStr']), 'html.parser').text)

def sync_file(c):
    pre = os.path.join(c['kcm'], '课件')
    if not os.path.exists(pre): os.makedirs(pre)
    tabs = get_json('/b/wlxt/kj/wlkc_kjflb/student/pageList?wlkcid=%s' % c['wlkcid'])['object']['rows'] # query tab
    for t in tabs:
        files = get_json('/b/wlxt/kj/wlkc_kjxxb/student/kjxxb/%s/%s' % (t['wlkcid'], t['kjflid']))['object']
        for f in files:
            download('/b/wlxt/kj/wlkc_kjxxb/student/downloadFile?sfgk=0&wjid=%s' % f[7], pre, f[1])

def sync_hw(c):
    pre = os.path.join(c['kcm'], '作业')
    if not os.path.exists(pre): os.makedirs(pre)
    data = {'aoData': [{"name": "iDisplayLength", "value": "1000"}, {"name": "wlkcid", "value": c['wlkcid']}]}
    hws = get_json('/b/wlxt/kczy/zy/student/zyListWj', data)['object']['aaData'] + get_json('/b/wlxt/kczy/zy/student/zyListYjwg', data)['object']['aaData'] + get_json('/b/wlxt/kczy/zy/student/zyListYpg', data)['object']['aaData']
    for hw in hws:
        path = os.path.join(pre, html.unescape(hw['bt']).replace('/', '、'))
        if not os.path.exists(path): os.makedirs(path)
        open(os.path.join(path, 'info.txt'), 'w').write('%s\n状态：%s\n开始时间：%s\n截止时间：%s\n上传时间：%s\n批阅状态：%s\n批阅时间：%s\n批阅内容：%s\n成绩：%s\n批阅者：%s %s\n' \
            % (hw['bt'], hw['zt'], hw['kssjStr'], hw['jzsjStr'], hw['scsjStr'], hw['pyzt'], hw['pysjStr'], hw['pynr'], hw['cj'], hw['gzzh'], hw['jsm']))
        page = bs(get_page('/f/wlxt/kczy/zy/student/viewCj?wlkcid=%s&zyid=%s&xszyid=%s' % (hw['wlkcid'], hw['zyid'], hw['xszyid'])), 'html.parser')
        files = page.findAll(class_='wdhere')
        for f in files:
            download('/b/wlxt/kczy/zy/student/downloadFile/%s/%s' % (hw['wlkcid'], f.findAll('a')[-1].attrs['onclick'].split("ZyFile('")[-1][:-2]), path)

if __name__ == '__main__':
    ignore = open('.ignore').read().split() if os.path.exists('.ignore') else []
    if os.path.exists('.pass'):
        username, password = open('.pass').read().split()
    else:
        username = input('username: ')
        password = getpass.getpass('password: ')
    if login(username, password):
        typepage = 1 if '.py' in sys.argv[-1] else int(sys.argv[-1])
        courses = get_courses(typepage)
        for c in courses:
            if c['kcm'] in ignore:
                print('Skip ' + c['kcm'] + ' '*maxlen)
            else:
                print('Sync ' + c['kcm'] + ' '*maxlen)
                if not os.path.exists(c['kcm']): os.makedirs(c['kcm'])
                sync_notify(c)
                sync_file(c)
                sync_hw(c)
