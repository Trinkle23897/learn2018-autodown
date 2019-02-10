#!/usr/bin/env python2
# -*- coding: utf-8 -*-

__author__ = "Trinkle23897"
__copyright__ = "Copyright (C) 2019 Trinkle23897"
__license__ = "MIT"
__email__ = "463003665@qq.com"

import os, sys, getpass, requests
from time import sleep
from selenium import webdriver
from bs4 import BeautifulSoup as bs
from selenium.webdriver.chrome.options import Options

root_uri = 'http://learn2018.tsinghua.edu.cn'
time_sleep = 0.05
time_out = 5

def wait_for_load(cond, driver): # wait for loading course info
    cnt = time_out / time_sleep # max try
    while cond(driver) and cnt > 0:
        sleep(time_sleep)
        cnt -= 1

def load_course_cond(driver): # avoid null
    return len(bs(driver.page_source, 'html.parser').findAll(class_='title stu')) == 0

def load_notice_cond(driver): # avoid '条数据'.count == 1
    return bs(driver.page_source, 'html.parser').text.count(u'条数据') < 2

def load_notice_ele_cond(driver): # avoid single '\n'
    return len(bs(driver.page_source, 'html.parser').find(id='ggnr').text) < 2

def load_course_file_cond(driver): # avoid no element in tabbox
    return bs(driver.page_source, 'html.parser').find(id='tabbox').text.count(u'电子教案') == 0

def load_course_file_ele_cond(driver): # avoid no element in tabbox
    return len(bs(driver.page_source, 'html.parser').find(class_='playli').findAll('li')) == 0 and u'此类别没有课程文件' not in bs(driver.page_source, 'html.parser').text

def load_hw_cond(driver):
    hw_html = bs(driver.page_source, 'html.parser')
    return len(hw_html.find(id='wtj').findAll('tr')) <= 2 and u'表中数据为空' not in hw_html.text

def download(pwd, url, cookie, name):
    r = requests.get(url, cookies=cookie, stream=True)
    filename = r.headers['Content-Disposition'].split('filename="')[-1].split('"')[0]
    if filename in os.listdir(pwd):
        return
    print('Download %s' % name)
    open(os.path.join(pwd, filename), 'wb').write(r.content)

if __name__ == "__main__":
    ignore = open('.ignore').read().split() if os.path.exists('.ignore') else []
    chrome_options = Options()
    chrome_options.add_argument("--headless") # comment for looking its behavior
    driver = webdriver.Chrome(chrome_options=chrome_options)
    print('Login ...')
    driver.get("http://learn.tsinghua.edu.cn/f/login")
    driver.find_element_by_name("i_user").send_keys(str(raw_input('Username: ')))
    driver.find_element_by_name("i_pass").send_keys(str(getpass.getpass('Password: ')))
    driver.find_element_by_id("loginButtonId").click()
    wait_for_load(load_course_cond, driver)
    print('\rLogin successfully!')
    # remember cookie for downloading files
    cookie = {}
    for c in driver.get_cookies():
        cookie[c[u'name'].encode('utf-8')] = c[u'value'].encode('utf-8')
    print(cookie)
    exit()
    root = bs(driver.page_source, 'html.parser')
    for course in root.findAll(class_='title stu')[:2]:
        if course.text in ignore:
            print('Skip ' + course.text)
            continue
        print('Sync ' + course.text)
        if not os.path.exists(course.text):
            os.mkdir(course.text)
        os.chdir(course.text)
        driver.get(root_uri + course.attrs['href'])

        # 公告
        if not os.path.exists('公告'):
            os.mkdir('公告')
        os.chdir('公告')
        driver.find_element_by_id("wlxt_kcgg_wlkc_ggb").click()
        wait_for_load(load_notice_cond, driver)
        all_notice = bs(driver.page_source, 'html.parser').find(id='table').findAll('a')
        for notice in all_notice:
            if os.path.exists(notice.attrs['title'].replace(u'/', u'、') + u'.txt'):
                continue
            driver.get(root_uri + notice.attrs['href'])
            wait_for_load(load_notice_ele_cond, driver)
            text = bs(driver.page_source, 'html.parser').find(id='ggnr').text
            open(notice.attrs['title'].replace(u'/', u'、') + u'.txt', 'w').write(text.encode('utf-8'))
        os.chdir('..') # leave 公告
        
        # 文件
        if not os.path.exists('文件'):
            os.mkdir('文件')
        os.chdir('文件')
        driver.find_element_by_id("wlxt_kj_wlkc_kjxxb").click()
        wait_for_load(load_course_file_cond, driver)
        all_tab = bs(driver.page_source, 'html.parser').find(id='tabbox').findAll('li')
        # print(all_tab)
        for tab in all_tab:
            driver.find_element_by_xpath('//li[@kjflid="%s"]' % tab.attrs['kjflid']).click()
            wait_for_load(load_course_file_cond, driver)
            wait_for_load(load_course_file_ele_cond, driver)
            all_file = bs(driver.page_source, 'html.parser').find(class_='playli').findAll('li')
            for file in all_file:
                download(os.getcwd(), root_uri + '/b/wlxt/kj/wlkc_kjxxb/student/downloadFile?sfgk=0&wjid=%s' % file.attrs['wjid'], cookie, file.attrs['kjbt'])
        os.chdir('..') # leave 文件
        
        # 作业 
        if not os.path.exists('作业'):
            os.mkdir('作业')
        os.chdir('作业')
        driver.find_element_by_id("wlxt_kczy_zy").click()
        wait_for_load(load_hw_cond, driver)
        hw_html = bs(driver.page_source, 'html.parser')
        for hw_list in [hw_html.find(id='wtj'), hw_html.find(id='yjwg'), hw_html.find(id='ypg')]:
            # print(hw_list)
            if u'表中数据为空' in hw_list.text:
                continue
            for hw in hw_list.findAll('tr')[1:]:
                driver.get(root_uri + hw.td.next_sibling.a.attrs['href'])
                html = bs(driver.page_source, 'html.parser')
                title = html.find(class_='detail').find(class_='right').text.strip()
                if not os.path.exists(title):
                    os.mkdir(title)
                os.chdir(title)
                disc = html.find(class_='detail').find(class_='c55').text.strip()
                open('作业说明.txt', 'w').write(disc.encode('utf-8'))
                file_list = html.findAll(class_='ftitle')
                for f in file_list:
                    download(os.getcwd(), root_uri + f.a.attrs['href'].split('downloadUrl=')[-1], cookie, f.text.replace('\n', ''))
                os.chdir('..') # leave sub_hw

        os.chdir('..') # leave 作业
        os.chdir('..') # leave course
