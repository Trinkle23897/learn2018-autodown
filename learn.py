#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = "Trinkle23897"
__copyright__ = "Copyright (C) 2019 Trinkle23897"
__license__ = "MIT"
__email__ = "463003665@qq.com"

import os, csv, sys, json, html, time, email, urllib, getpass, base64, hashlib, argparse, platform, subprocess
from tqdm import tqdm
import urllib.request, http.cookiejar
from bs4 import BeautifulSoup as bs

url = 'https://learn.tsinghua.edu.cn'
user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.130 Safari/537.36'
headers = {'User-Agent': user_agent, 'Connection': 'keep-alive'}
cookie = http.cookiejar.MozillaCookieJar()
handler = urllib.request.HTTPCookieProcessor(cookie)
opener = urllib.request.build_opener(handler)
urllib.request.install_opener(opener)

def open_page(uri, values={}):
    post_data = urllib.parse.urlencode(values).encode() if values else None
    request = urllib.request.Request(uri if uri.startswith('http') else url + uri, post_data, headers)
    try:
        response = opener.open(request)
        return response
    except urllib.error.URLError as e:
        print(uri, e.code, ':', e.reason)

def get_page(uri, values={}):
    data = open_page(uri, values)
    if data:
        return data.read().decode()

def get_json(uri, values={}):
    while True:
        try:
            page = get_page(uri, values)
            result = json.loads(page)
            return result
        except json.JSONDecodeError:
            print('JSON Decode Error, reconnecting... %s' % page, end='\r')

def escape(s):
    return html.unescape(s).replace(os.path.sep, '、').replace(':', '_').replace(' ', '_').replace('\t', '').replace('?','.').replace('/','_').replace('\'','_').replace('<','').replace('>','').replace('#','').replace(';','').replace('*','_').replace("\"",'_').replace("\'",'_').replace('|','')

def login(username, password):
    login_uri = 'https://id.tsinghua.edu.cn/do/off/ui/auth/login/post/bb5df85216504820be7bba2b0ae1535b/0?/login.do'
    values = {'i_user': username, 'i_pass': password, 'atOnce': 'true'}
    info = get_page(login_uri, values)
    successful = 'SUCCESS' in info
    print('User %s login successfully' % (username) if successful else 'User %s login failed!' % (username))
    if successful:
        get_page(get_page(info.split('replace("')[-1].split('");\n')[0]).split('location="')[1].split('";\r\n')[0])
    return successful

def get_courses(args):
    try:
        now = get_json('/b/kc/zhjw_v_code_xnxq/getCurrentAndNextSemester')['result']['xnxq']
        if args.all or args.course or args.semester:
            query_list = [x for x in get_json('/b/wlxt/kc/v_wlkc_xs_xktjb_coassb/queryxnxq') if x != None]
            query_list.sort()
            if args.semester:
                query_list_ = [q for q in query_list if q in args.semester]
                if len(query_list_) == 0:
                    print('Invalid semester, choices: ', query_list)
                    return []
                query_list = query_list_
        else:
            current = True
            query_list = [now]
    except:
        print('您被退学了！')
        return []
    courses = []
    for q in query_list:
        try:
            courses += get_json('/b/wlxt/kc/v_wlkc_xs_xktjb_coassb/pageList', {'aoData': [
                {"name": "xnxq", "value": q},
                {"name": "jslx", "value": "3"} # students
            ]})['object']['aaData']
            courses += get_json('/b/wlxt/kc/v_wlkc_xs_xktjb_coassb/pageList', {'aoData': [
                {"name": "xnxq", "value": q},
                {"name": "jslx", "value": "0"} # TA
            ]})['object']['aaData']
        except:
            continue
    if now in query_list: # a bug in wlxt
        try:
            c_stu, c_ta = [], []
            c_stu = get_json('/b/wlxt/kc/v_wlkc_xs_xkb_kcb_extend/student/loadCourseBySemesterId/' + query_list[-1])['resultList']
            c_ta = get_json('/b/kc/v_wlkc_kcb/queryAsorCoCourseList/%s/0' % query_list[-1])['resultList']
        except:
            pass
        finally:
            current_courses = []
            for c in c_stu:
                c['jslx'] = '3'
                current_courses.append(c)
            for c in c_ta:
                c['jslx'] = '0'
                current_courses.append(c)
            wlkcids = [c['wlkcid'] for c in courses]
            current_courses = [c for c in current_courses if c['wlkcid'] not in wlkcids]
            courses += current_courses
    escape_c = []
    for c in courses:
        c['kcm'] = escape(c['kcm']).replace(' ', '').replace('_', '').replace('（', '(').replace('）', ')')
        escape_c.append(c)
    courses = escape_c
    if args.course:
        courses = [c for c in courses if c['kcm'] in args.course]
    if args.ignore:
        courses = [c for c in courses if c['kcm'] not in args.ignore]
    return courses

class TqdmUpTo(tqdm):
    def update_to(self, b=1, bsize=1, tsize=None):
        if tsize is not None: self.total = tsize
        self.update(b * bsize - self.n)

def download(uri, name):
    filename = escape(name)
    if os.path.exists(filename) and os.path.getsize(filename) or 'Connection__close' in filename:
        return
    try:
        with TqdmUpTo(ascii=True, dynamic_ncols=True, unit='B', unit_scale=True, miniters=1, desc=filename) as t:
            urllib.request.urlretrieve(url+uri, filename=filename, reporthook=t.update_to, data=None)
    except:
        print('Could not download %s due to networking ... removing broken file' % filename)
        if os.path.exists(filename):
            os.remove(filename)
        return

def build_notify(s):
    tp = bs(base64.b64decode(s['ggnr']).decode('utf-8'), 'html.parser').text if s['ggnr'] else ''
    st = '题目: %s\n发布人: %s\n发布时间: %s\n内容: %s\n' % (s['bt'], s['fbr'], s['fbsjStr'], tp)
    return st

def sync_notify(c):
    pre = os.path.join(c['kcm'], '公告')
    if not os.path.exists(pre): os.makedirs(pre)
    try:
        data = {'aoData': [{"name": "wlkcid", "value": c['wlkcid']}]}
        if c['_type'] == 'student':
            notify = get_json('/b/wlxt/kcgg/wlkc_ggb/student/pageListXs', data)['object']['aaData']
        else:
            notify = get_json('/b/wlxt/kcgg/wlkc_ggb/teacher/pageList', data)['object']['aaData']
    except:
        return
    for n in notify:
        path = os.path.join(pre, escape(n['bt']) +'.txt')
        open(path, 'w').write(build_notify(n))

def sync_file(c):
    now = os.getcwd()
    pre = os.path.join(c['kcm'], '课件')
    if not os.path.exists(pre): os.makedirs(pre)
    if c['_type'] == 'student':
        files = get_json('/b/wlxt/kj/wlkc_kjxxb/student/kjxxbByWlkcidAndSizeForStudent?wlkcid=%s&size=0' % c['wlkcid'])['object']
    else:
        files = get_json('/b/wlxt/kj/v_kjxxb_wjwjb/teacher/queryByWlkcid?wlkcid=%s&size=0' % c['wlkcid'])['object']['resultsList']
    for f in files:
        os.chdir(pre)
        name = f['bt']+'.'+f['wjlx'] if f['wjlx'] else f['bt']
        download('/b/wlxt/kj/wlkc_kjxxb/%s/downloadFile?sfgk=0&wjid=%s' % (c['_type'], f['wjid']), name=name)
        os.chdir(now)

def sync_info(c):
    pre = os.path.join(c['kcm'], '课程信息.txt')
    try:
        if c['_type'] == 'student':
            html = get_page('/f/wlxt/kc/v_kcxx_jskcxx/student/beforeXskcxx?wlkcid=%s&sfgk=-1' % c['wlkcid'])
        else:
            html = get_page('/f/wlxt/kc/v_kcxx_jskcxx/teacher/beforeJskcxx?wlkcid=%s&sfgk=-1' % c['wlkcid'])
        open(pre, 'w').write('\n'.join(bs(html, 'html.parser').find(class_='course-w').text.split()))
    except:
        return

def append_hw_csv(fname, stu):
    try:
        f = [i for i in csv.reader(open(fname)) if i]
    except:
        f = [['学号', '姓名', '院系', '班级', '上交时间', '状态', '成绩', '批阅老师']]
    info_str = [stu['xh'], stu['xm'], stu['dwmc'], stu['bm'], stu['scsjStr'], stu['zt'], stu['cj'], stu['jsm']]
    xhs = [i[0] for i in f]
    if stu['xh'] in xhs:
        i = xhs.index(stu['xh'])
        f[i] = info_str
    else:
        f.append(info_str)
    csv.writer(open(fname, 'w')).writerows(f)

def sync_hw(c):
    now = os.getcwd()
    pre = os.path.join(c['kcm'], '作业')
    if not os.path.exists(pre): os.makedirs(pre)
    data = {'aoData': [{"name": "wlkcid", "value": c['wlkcid']}]}
    if c['_type'] == 'student':
        hws = []
        for hwtype in ['zyListWj', 'zyListYjwg', 'zyListYpg']:
            try:
                hws += get_json('/b/wlxt/kczy/zy/student/%s' % hwtype, data)['object']['aaData']
            except:
                continue
    else:
        hws = get_json('/b/wlxt/kczy/zy/teacher/pageList', data)['object']['aaData']
    for hw in hws:
        path = os.path.join(pre, escape(hw['bt']))
        if not os.path.exists(path): os.makedirs(path)
        if c['_type'] == 'student':
            append_hw_csv(os.path.join(path, 'info_%s.csv' % c['wlkcid']), hw)
            page = bs(get_page('/f/wlxt/kczy/zy/student/viewCj?wlkcid=%s&zyid=%s&xszyid=%s' % (hw['wlkcid'], hw['zyid'], hw['xszyid'])), 'html.parser')
            files = page.findAll(class_='wdhere')
            for f in files:
                os.chdir(path) # to avoid filename too long
                download('/b/wlxt/kczy/zy/%s/downloadFile/%s/%s' % (c['_type'], hw['wlkcid'], f.findAll('a')[-1].attrs['onclick'].split("ZyFile('")[-1][:-2]), name=hw['xh']+'_'+f.findAll('a')[0].text)
                os.chdir(now)
        else:
            print(hw['bt'])
            data = {'aoData': [{"name": "wlkcid", "value": c['wlkcid']}, {"name": "zyid", "value": hw['zyid']}]}
            stus = get_json('/b/wlxt/kczy/xszy/teacher/getDoneInfo', data)['object']['aaData']
            for stu in stus:
                append_hw_csv(os.path.join(path, 'info_%s.csv' % c['wlkcid']), stu)
                page = bs(get_page('/f/wlxt/kczy/xszy/teacher/beforePiYue?wlkcid=%s&xszyid=%s' % (stu['wlkcid'], stu['xszyid'])), 'html.parser')
                files = page.findAll(class_='wdhere')
                for f in files:
                    if f.text == '\n':
                        continue
                    os.chdir(path) # to avoid filename too long
                    try:
                        id = f.findAll('span')[0].attrs['onclick'].split("'")[1]
                        name = f.findAll('span')[0].text
                    except:
                        id = f.findAll('a')[-1].attrs['onclick'].split("'")[1]
                        name = f.findAll('a')[0].text
                    download('/b/wlxt/kczy/xszy/teacher/downloadFile/%s/%s' % (stu['wlkcid'], id), name=stu['xh']+'_'+name)
                    os.chdir(now)
            stus = get_json('/b/wlxt/kczy/xszy/teacher/getUndoInfo', data)['object']['aaData']
            for stu in stus:
                append_hw_csv(os.path.join(path, 'info_%s.csv' % c['wlkcid']), stu)

def build_discuss(s):
    disc = '课程：%s\n内容：%s\n学号：%s\n姓名：%s\n发布时间:%s\n最后回复：%s\n回复时间：%s\n' % (s['kcm'], s['bt'], s['fbr'], s['fbrxm'], s['fbsj'], s['zhhfrxm'], s['zhhfsj'])
    return disc

def sync_discuss(c):
    pre = os.path.join(c['kcm'], '讨论')
    if not os.path.exists(pre): os.makedirs(pre)
    try:
        disc = get_json('/b/wlxt/bbs/bbs_tltb/%s/kctlList?wlkcid=%s' % (c['_type'], c['wlkcid']))['object']['resultsList']
    except:
        return
    for d in disc:
        filename = os.path.join(pre, escape(d['bt']) + '.txt')
        if os.path.exists(filename):
            continue
        try:
            html = get_page('/f/wlxt/bbs/bbs_tltb/%s/viewTlById?wlkcid=%s&id=%s&tabbh=2&bqid=%s' % (c['_type'], d['wlkcid'], d['id'], d['bqid']))
            open(filename, 'w').write(build_discuss(d) + bs(html, 'html.parser').find(class_='detail').text)
        except:
            pass

def gethash(fname):
    if platform.system() == 'Linux':
        return subprocess.check_output(['md5sum', fname]).decode().split()[0]
    hash_md5 = hashlib.md5()
    with open(fname, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def dfs_clean(d):
    subdirs = [os.path.join(d, i) for i in os.listdir(d) if os.path.isdir(os.path.join(d, i))]
    for i in subdirs:
        dfs_clean(i)
    files = [os.path.join(d, i) for i in os.listdir(d) if os.path.isfile(os.path.join(d, i))]
    info = {}
    for f in files:
        if os.path.getsize(f):
            info[f] = {'size': os.path.getsize(f), 'time': os.path.getmtime(f), 'hash': '', 'rm': 0}
    info = list({k: v for k, v in sorted(info.items(), key=lambda item: item[1]['size'])}.items())
    for i in range(len(info)):
        for j in range(i):
            if info[i][1]['size'] == info[j][1]['size']:
                if info[i][1]['hash'] == '':
                    info[i][1]['hash'] = gethash(info[i][0])
                if info[j][1]['hash'] == '':
                    info[j][1]['hash'] = gethash(info[j][0])
                if info[i][1]['hash'] == info[j][1]['hash']:
                    if info[i][1]['time'] < info[j][1]['time']:
                        info[i][1]['rm'] = 1
                    elif info[i][1]['time'] > info[j][1]['time']:
                        info[j][1]['rm'] = 1
                    elif len(info[i][0]) < len(info[j][0]):
                        info[i][1]['rm'] = 1
                    elif len(info[i][0]) > len(info[j][0]):
                        info[j][1]['rm'] = 1
    rm = [i[0] for i in info if i[1]['rm']]
    if rm:
        print('rmlist:', rm)
        for f in rm:
            os.remove(f)

def clear(args):
    courses = [i for i in os.listdir('.') if os.path.isdir(i) and not i.startswith('.')]
    if args.all:
        pass
    else:
        if args.course:
            courses = [i for i in courses if i in args.course]
        if args.ignore:
            courses = [i for i in courses if i not in args.ignore]
    courses.sort()
    for i, c in enumerate(courses):
        print('Sync #%d %s ...' % (i + 1, c))
        for subdir in ['课件', '作业']:
            d = os.path.join(c, subdir)
            if os.path.exists(d): dfs_clean(d)

def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--all", action='store_true')
    parser.add_argument("--clear", action='store_true', help='remove the duplicate course file')
    parser.add_argument("--semester", nargs='+', type=str, default=[])
    parser.add_argument("--ignore", nargs='+', type=str, default=[])
    parser.add_argument("--course", nargs='+', type=str, default=[])
    parser.add_argument('-p', "--_pass", type=str, default='.pass')
    args = parser.parse_args()
    return args

def main(args):
    if args.clear:
        clear(args)
        exit()
    if os.path.exists(args._pass):
        username, password = open(args._pass).read().split()
    else:
        username = input('请输入INFO账号：')
        password = getpass.getpass('请输入INFO密码：')
    if login(username, password):
        courses = get_courses(args)
        for c in courses:
            c['_type'] = {'0': 'teacher', '3': 'student'}[c['jslx']]
            print('Sync ' + c['xnxq'] + ' ' + c['kcm'])
            if not os.path.exists(c['kcm']): os.makedirs(c['kcm'])
            sync_info(c)
            sync_discuss(c)
            sync_notify(c)
            sync_file(c)
            sync_hw(c)

if __name__ == '__main__':
    main(get_args())
