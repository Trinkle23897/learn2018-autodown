#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os, csv, json, html, urllib, getpass, base64, hashlib, argparse, platform, subprocess
from tqdm import tqdm
import urllib.request, http.cookiejar
from bs4 import BeautifulSoup as bs
import multiprocessing as mp
from functools import partial
import uuid
import re
import time
import asyncio

import ssl

from gmssl import sm2

ssl._create_default_https_context = ssl._create_unverified_context
global dist_path, url, user_agent, headers, cookie, opener, err404, fingerprint_data
dist_path = url = user_agent = headers = cookie = opener = err404 = fingerprint_data = (
    None
)


def build_url(uri):
    return uri if uri.startswith("http") else url + uri


def encrypt_password_sm2(password, public_key):
    try:
        # 清华SSO使用的公钥格式处理：统一为十六进制字符串，gmssl 期望 hex 字符串
        if isinstance(public_key, (bytes, bytearray)):
            public_key = public_key.decode("utf-8", errors="ignore")
        public_key = str(public_key).strip()

        # 计算并打印 x/y 坐标（如果可用）
        public_key_hex = public_key
        if public_key_hex.startswith("04") and len(public_key_hex) == 130:
            x_hex = public_key_hex[2:66]
            y_hex = public_key_hex[66:130]
            print(f"公钥X坐标: {x_hex[:20]}...")
            print(f"公钥Y坐标: {y_hex[:20]}...")
        elif len(public_key_hex) == 128:
            x_hex = public_key_hex[:64]
            y_hex = public_key_hex[64:]
            print(f"公钥X坐标: {x_hex[:20]}...")
            print(f"公钥Y坐标: {y_hex[:20]}...")
            public_key_hex = "04" + public_key_hex

        # SM2加密 - 使用C1C3C2模式以匹配浏览器实现
        sm2_crypt = sm2.CryptSM2(
            public_key=public_key_hex, private_key=None, mode=1
        )  # mode=1 for C1C3C2
        encrypted = sm2_crypt.encrypt(password.encode("utf-8"))

        # 转换为16进制字符串（大写，匹配浏览器格式）
        encrypted_hex = encrypted.hex().upper()

        print(f"密码加密成功，长度: {len(encrypted_hex)}")
        return encrypted_hex

    except Exception as e:
        print(f"SM2加密失败: {e}")
        print("将使用明文密码")
        return password


def extract_public_key_from_page(login_page_html):
    soup = bs(login_page_html, "html.parser")

    # 查找包含公钥的元素
    public_key_element = soup.find("div", {"id": "sm2publicKey"})
    if public_key_element:
        public_key = public_key_element.get_text().strip()
        print(f"找到SM2公钥: {public_key[:20]}...")
        return public_key

    # 如果没找到，使用默认公钥
    default_key = "04d0c9e1ae89279fe05b435d63e3eba437bf510e09da5f71558974a19dc596724227f08dc2fc6e74bbb9d8b468d4dd5205e9b6793a3bbc48df3fdf219b3ea140e3"
    print("未找到公钥，使用默认公钥")
    return default_key


def build_global(args):
    global dist_path, url, user_agent, headers, cookie, opener, err404
    dist_path = args.dist
    url = "https://learn.tsinghua.edu.cn"
    user_agent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"

    # 更完整的浏览器头部，模拟真实浏览器行为
    headers = {
        "User-Agent": user_agent,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "same-origin",
        "Sec-Fetch-User": "?1",
        "Cache-Control": "max-age=0",
    }
    handlers = []

    # 添加SSL上下文配置
    context = ssl.create_default_context()
    context.options |= 0x4  # OP_LEGACY_SERVER_CONNECT
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE
    handlers.append(urllib.request.HTTPSHandler(context=context))

    if args.http_proxy:
        handlers.append(urllib.request.ProxyHandler({"http": args.http_proxy}))
    if args.https_proxy:
        handlers.append(urllib.request.ProxyHandler({"https": args.https_proxy}))
    # 如果cookie已经存在（例如从浏览器登录），则保留它
    if cookie is None:
        cookie = http.cookiejar.MozillaCookieJar()
    handlers.append(urllib.request.HTTPCookieProcessor(cookie))
    opener = urllib.request.build_opener(*handlers)
    urllib.request.install_opener(opener)
    err404 = '\r\n\r\n\r\n<script type="text/javascript">\r\n\tlocation.href="/";\r\n</script>'


def get_xsrf_token():
    cookie_obj = (
        cookie._cookies.get("learn.tsinghua.edu.cn", dict())
        .get("/", dict())
        .get("XSRF-TOKEN", None)
    )
    return cookie_obj.value if cookie_obj else None


def open_page(uri, values={}):
    post_data = urllib.parse.urlencode(values).encode() if values else None
    request = urllib.request.Request(
        uri if uri.startswith("http") else url + uri, post_data, headers
    )
    try:
        response = opener.open(request)
        return response
    except urllib.error.URLError as e:
        if hasattr(e, "code"):
            print(uri, e.code, ":", e.reason)
        else:
            print(uri, ":", e.reason)


from requests import Session


def get_page(uri, values={}, session=None):
    if session:
        # 使用新的session方式
        try:
            url_full = uri if uri.startswith("http") else url + uri
            if values:
                # 使用与原始代码完全相同的编码方式
                import urllib.parse

                encoded_data = urllib.parse.urlencode(values)
                response = session.post(
                    url_full,
                    data=encoded_data,
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                )
            else:
                response = session.get(url_full)
            response.raise_for_status()
            return response.text
        except Exception as e:
            print(f"Session请求失败 {uri}: {e}")
            return None
    else:
        # 使用传统的opener方式（向后兼容）
        data = open_page(uri, values)
        if data:
            try:
                # 首先尝试UTF-8解码
                return data.read().decode("utf-8")
            except UnicodeDecodeError:
                # 如果失败，尝试GBK解码
                try:
                    data.seek(0)  # 重置文件指针
                    return data.read().decode("gbk")
                except:
                    # 最后尝试latin1
                    data.seek(0)
                    return data.read().decode("latin1")


def get_json(uri, values={}, session: Session = None):
    if session:
        # 使用新的session方式
        try:
            url_full = uri if uri.startswith("http") else url + uri

            # Session已经在headers中包含了XSRF-TOKEN，不需要手动添加
            if values:
                # 使用与原始代码完全相同的编码方式
                import urllib.parse

                encoded_data = urllib.parse.urlencode(values)

                # 发送编码后的数据
                response = session.post(
                    url_full,
                    data=encoded_data,
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                )
            else:
                response = session.get(url_full)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Session JSON请求失败 {uri}: {e}")
            return {}
    else:
        # 使用传统的opener方式（向后兼容）
        xsrf_token = get_xsrf_token()
        if xsrf_token:
            if "?" not in uri:
                uri = uri + f"?_csrf={xsrf_token}"
            else:
                uri = uri + f"&_csrf={xsrf_token}"
        try:
            page = get_page(uri, values)  # 传统方式不传session参数
            result = json.loads(page)
            return result
        except:
            return {}


def escape(s):
    return (
        html.unescape(s)
        .replace(os.path.sep, "、")
        .replace(":", "_")
        .replace(" ", "_")
        .replace("\t", "")
        .replace("?", ".")
        .replace("/", "_")
        .replace("'", "_")
        .replace("<", "")
        .replace(">", "")
        .replace("#", "")
        .replace(";", "")
        .replace("*", "_")
        .replace('"', "_")
        .replace("'", "_")
        .replace("|", "")
    )


def parse_login_form(login_page_html):
    soup = bs(login_page_html, "html.parser")
    form_data = {}

    # 查找登录表单
    form = soup.find("form", {"id": "theform"}) or soup.find("form")
    if not form:
        print("未找到登录表单")
        return None

    # 提取所有input字段
    inputs = form.find_all("input")
    for inp in inputs:
        name = inp.get("name")
        value = inp.get("value", "")
        input_type = inp.get("type", "text")

        if name and input_type not in ["submit", "button"]:
            form_data[name] = value
            print(f"找到表单字段: {name} = {value}")

    return form_data


def get_courses(session, args):
    now = session.get(
        build_url("/b/kc/zhjw_v_code_xnxq/getCurrentAndNextSemester")
    ).json()["result"]["xnxq"]
    # print("now: ", now)
    if args.all or args.course or args.semester:
        query_list = [
            x
            for x in session.get(
                build_url("/b/wlxt/kc/v_wlkc_xs_xktjb_coassb/queryxnxq")
            ).json()
            if x is not None
        ]
        query_list.sort()
        if args.semester:
            query_list_ = [q for q in query_list if q in args.semester]
            if len(query_list_) == 0:
                # print("Invalid semester, choices: ", query_list)
                return []
            query_list = query_list_
    else:
        query_list = [now]
    # print("query_list: ", query_list)
    courses = []
    for q in query_list:
        c_stu = session.get(
            build_url(
                "/b/wlxt/kc/v_wlkc_xs_xkb_kcb_extend/student/loadCourseBySemesterId/"
            )
            + q
            + "/zh/"
        ).json()["resultList"]

        # print("c_stu: ", c_stu)

        c_ta = session.get(
            build_url("/b/kc/v_wlkc_kcb/queryAsorCoCourseList/%s/0" % q)
        ).json()["resultList"]

        # print("c_ta: ", c_ta)

        current_courses = []
        for c in c_stu:
            c["jslx"] = "3"
            current_courses.append(c)
        for c in c_ta:
            c["jslx"] = "0"
            current_courses.append(c)
        courses += current_courses
    escape_c = []

    def escape_course_fn(c):
        return (
            escape(c)
            .replace(" ", "")
            .replace("_", "")
            .replace("（", "(")
            .replace("）", ")")
        )

    for c in courses:
        c["kcm"] = escape_course_fn(c["kcm"])
        escape_c.append(c)
    courses = escape_c
    if args.course:
        args.course = [escape_course_fn(c) for c in args.course]
        courses = [c for c in courses if c["kcm"] in args.course]
    if args.ignore:
        args.ignore = [escape_course_fn(c) for c in args.ignore]
        courses = [c for c in courses if c["kcm"] not in args.ignore]
    return courses


class TqdmUpTo(tqdm):
    def update_to(self, b=1, bsize=1, tsize=None):
        if tsize is not None:
            self.total = tsize
        self.update(b * bsize - self.n)


def download(uri, name, target_dir=None, session=None):
    filename = escape(name)

    # 使用绝对路径
    if target_dir:
        filename = os.path.join(target_dir, filename)

    if (
        os.path.exists(filename)
        and os.path.getsize(filename)
        or "Connection__close" in filename
    ):
        return

    try:
        if session:
            # 使用新的session方式
            download_url = uri if uri.startswith("http") else url + uri
            response = session.get(download_url, stream=True)
            response.raise_for_status()

            total_size = int(response.headers.get("content-length", 0))

            with TqdmUpTo(
                ascii=True,
                dynamic_ncols=True,
                unit="B",
                unit_scale=True,
                miniters=1,
                desc=filename,
                total=total_size,
            ) as t:
                with open(filename, "wb") as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            t.update(len(chunk))
        else:
            # 使用传统的urllib方式（向后兼容）
            with TqdmUpTo(
                ascii=True,
                dynamic_ncols=True,
                unit="B",
                unit_scale=True,
                miniters=1,
                desc=filename,
            ) as t:
                urllib.request.urlretrieve(
                    url + uri, filename=filename, reporthook=t.update_to, data=None
                )
    except Exception as e:
        print(
            f"Could not download file {filename} ... removing broken file. Error: {str(e)}"
        )
        if os.path.exists(filename):
            os.remove(filename)
        return


def build_notify(s):
    tp = (
        bs(base64.b64decode(s["ggnr"]).decode("utf-8"), "html.parser").text
        if s["ggnr"]
        else ""
    )
    st = "题目: %s\n发布人: %s\n发布时间: %s\n\n内容: %s\n" % (
        s["bt"],
        s["fbr"],
        s["fbsjStr"],
        tp,
    )
    return st


def makedirs_safe(directory):
    try:
        if not os.path.exists(directory):
            os.makedirs(directory)
    except FileExistsError:
        pass


def sync_notify(session, c):
    global dist_path
    pre = os.path.join(dist_path, c["kcm"], "公告")
    makedirs_safe(pre)
    try:
        data = {"aoData": [{"name": "wlkcid", "value": c["wlkcid"]}]}
        if c["_type"] == "student":
            notify = get_json(
                "/b/wlxt/kcgg/wlkc_ggb/student/pageListXs", data, session=session
            )["object"]["aaData"]
        else:
            notify = get_json(
                "/b/wlxt/kcgg/wlkc_ggb/teacher/pageList", data, session=session
            )["object"]["aaData"]
    except:
        return
    for n in notify:
        makedirs_safe(os.path.join(pre, escape(n["bt"])))
        path = os.path.join(
            os.path.join(pre, escape(n["bt"])), escape(n["bt"]) + ".txt"
        )
        open(path, "w", encoding="utf-8").write(build_notify(n))

        if n.get("fjmc") is not None:
            html = get_page(
                "/f/wlxt/kcgg/wlkc_ggb/%s/beforeViewXs?wlkcid=%s&id=%s"
                % (c["_type"], n["wlkcid"], n["ggid"]),
                session=session,
            )
            soup = bs(html, "html.parser")

            link = soup.find("a", class_="ml-10")

            now = os.getcwd()
            os.chdir(os.path.join(pre, escape(n["bt"])))
            name = n["fjmc"]
            download(link["href"], name=name, session=session)
            os.chdir(now)


def sync_file(session, c):
    global dist_path
    now = os.getcwd()
    pre = os.path.join(dist_path, c["kcm"], "课件")
    makedirs_safe(pre)

    if c["_type"] == "student":
        files = get_json(
            "/b/wlxt/kj/wlkc_kjxxb/student/kjxxbByWlkcidAndSizeForStudent?wlkcid=%s&size=0"
            % c["wlkcid"],
            session=session,
        )["object"]
    else:
        try:
            files = get_json(
                "/b/wlxt/kj/v_kjxxb_wjwjb/teacher/queryByWlkcid?wlkcid=%s&size=0"
                % c["wlkcid"],
                session=session,
            )["object"]["resultsList"]
        except:  # None
            return

    try:
        if session:
            # 使用session方式，不需要手动添加CSRF token
            page_content = get_page(
                f'/b/wlxt/kj/wlkc_kjflb/{c["_type"]}/pageList?wlkcid={c["wlkcid"]}',
                session=session,
            )
        else:
            # 使用传统方式，需要手动添加CSRF token
            page_content = get_page(
                f'/b/wlxt/kj/wlkc_kjflb/{c["_type"]}/pageList?_csrf={get_xsrf_token()}&wlkcid={c["wlkcid"]}'
            )
        rows = json.loads(page_content)["object"]["rows"]
    except:  # None
        return

    os.chdir(pre)
    for r in rows:
        if c["_type"] == "student":
            row_files = get_json(
                f'/b/wlxt/kj/wlkc_kjxxb/{c["_type"]}/kjxxb/{c["wlkcid"]}/{r["kjflid"]}',
                session=session,
            )["object"]
        else:
            data = {
                "aoData": [
                    {"name": "wlkcid", "value": c["wlkcid"]},
                    {"name": "kjflid", "value": r["kjflid"]},
                    {"name": "iDisplayStart", "value": 0},
                    {"name": "iDisplayLength", "value": "-1"},
                ]
            }
            row_files = get_json(
                "/b/wlxt/kj/v_kjxxb_wjwjb/teacher/pageList", data, session=session
            )["object"]["aaData"]
        makedirs_safe(escape(r["bt"]))
        rnow = os.getcwd()
        os.chdir(escape(r["bt"]))
        for rf in row_files:
            wjlx = None
            if c["_type"] == "student":
                flag = False
                for f in files:
                    if rf[7] == f["wjid"]:
                        flag = True
                        wjlx = f["wjlx"]
                        break
                wjid = rf[7]
                name = rf[1]
            else:
                flag = True
                wjlx = rf["wjlx"]
                wjid = rf["wjid"]
                name = rf["bt"]
            if flag:
                if wjlx:
                    name += "." + wjlx
                download(
                    f'/b/wlxt/kj/wlkc_kjxxb/{c["_type"]}/downloadFile?sfgk=0&wjid={wjid}',
                    name=name,
                    session=session,
                )
            else:
                print(f"文件{rf[1]}出错")
        os.chdir(rnow)

    os.chdir(now)


def sync_info(session, c):
    global dist_path
    pre = os.path.join(dist_path, c["kcm"], "课程信息.txt")

    if c["_type"] == "student":
        html = get_page(
            "/f/wlxt/kc/v_kcxx_jskcxx/student/beforeXskcxx?wlkcid=%s&sfgk=-1"
            % c["wlkcid"],
            session=session,
        )
    else:
        html = get_page(
            "/f/wlxt/kc/v_kcxx_jskcxx/teacher/beforeJskcxx?wlkcid=%s&sfgk=-1"
            % c["wlkcid"],
            session=session,
        )
    open(pre, "w").write(
        "\n".join(bs(html, "html.parser").find(class_="course-w").text.split())
    )


def append_hw_csv(fname, stu):
    try:
        f = [i for i in csv.reader(open(fname)) if i]
    except:
        f = [["学号", "姓名", "院系", "班级", "上交时间", "状态", "成绩", "批阅老师"]]
    info_str = [
        stu["xh"],
        stu["xm"],
        stu["dwmc"],
        stu["bm"],
        stu["scsjStr"],
        stu["zt"],
        stu["cj"],
        stu["jsm"],
    ]
    xhs = [i[0] for i in f]
    if stu["xh"] in xhs:
        i = xhs.index(stu["xh"])
        f[i] = info_str
    else:
        f.append(info_str)
    csv.writer(open(fname, "w")).writerows(f)


def sync_hw(session, c):
    global dist_path
    now = os.getcwd()
    pre = os.path.join(dist_path, c["kcm"], "作业")
    if not os.path.exists(pre):
        os.makedirs(pre)
    data = {"aoData": [{"name": "wlkcid", "value": c["wlkcid"]}]}
    if c["_type"] == "student":
        hws = []
        for hwtype in ["zyListWj", "zyListYjwg", "zyListYpg"]:
            try:
                hws += get_json(
                    "/b/wlxt/kczy/zy/student/%s" % hwtype, data, session=session
                )["object"]["aaData"]
            except:
                continue
    else:
        hws = get_json("/b/wlxt/kczy/zy/teacher/pageList", data, session=session)[
            "object"
        ]["aaData"]
    for hw in hws:
        path = os.path.join(pre, escape(hw["bt"]))
        if not os.path.exists(path):
            os.makedirs(path)

        # 获取作业详情页面并保存为Markdown
        try:
            if c["_type"] == "student":
                # 构建作业详情页面URL
                detail_url = (
                    "/f/wlxt/kczy/zy/student/viewZy?wlkcid=%s&sfgq=0&zyid=%s&xszyid=%s"
                    % (hw["wlkcid"], hw["zyid"], hw.get("xszyid", ""))
                )
            else:
                # 教师端的URL可能不同，先使用学生端的逻辑
                detail_url = (
                    "/f/wlxt/kczy/zy/teacher/viewZy?wlkcid=%s&sfgq=0&zyid=%s"
                    % (hw["wlkcid"], hw["zyid"])
                )

            # 获取作业详情页面HTML
            detail_html = get_page(detail_url, session=session)
            if detail_html:
                # 解析作业详情
                homework_info = parse_homework_detail(detail_html)

                # 生成Markdown内容
                markdown_content = build_homework_markdown(homework_info)

                # 保存作业说明为Markdown文件
                markdown_path = os.path.join(path, "作业说明.md")
                with open(markdown_path, "w", encoding="utf-8") as f:
                    f.write(markdown_content)

                print(f"已保存作业说明: {hw['bt']}")
        except Exception as e:
            print(f"获取作业详情失败 {hw['bt']}: {e}")

        if c["_type"] == "student":
            append_hw_csv(os.path.join(path, "info_%s.csv" % c["wlkcid"]), hw)
            page = bs(
                get_page(
                    "/f/wlxt/kczy/zy/student/viewCj?wlkcid=%s&zyid=%s&xszyid=%s"
                    % (hw["wlkcid"], hw["zyid"], hw["xszyid"]),
                    session=session,
                ),
                "html.parser",
            )
            files = page.find_all(class_="fujian")
            for i, f in enumerate(files):
                if len(f.find_all("a")) == 0:
                    continue
                os.chdir(path)  # to avoid filename too long
                name = f.find_all("a")[0].text
                if i >= 2 and not name.startswith(hw["xh"]):
                    name = hw["xh"] + "_" + name
                download(
                    "/b/wlxt/kczy/zy/%s/downloadFile/%s/%s"
                    % (
                        c["_type"],
                        hw["wlkcid"],
                        f.find_all("a")[-1].attrs["onclick"].split("ZyFile('")[-1][:-2],
                    ),
                    name=name,
                    session=session,
                )
                os.chdir(now)
        else:
            print(hw["bt"])
            data = {
                "aoData": [
                    {"name": "wlkcid", "value": c["wlkcid"]},
                    {"name": "zyid", "value": hw["zyid"]},
                ]
            }
            stus = get_json(
                "/b/wlxt/kczy/xszy/teacher/getDoneInfo", data, session=session
            )["object"]["aaData"]
            for stu in stus:
                append_hw_csv(os.path.join(path, "info_%s.csv" % c["wlkcid"]), stu)
                page = bs(
                    get_page(
                        "/f/wlxt/kczy/xszy/teacher/beforePiYue?wlkcid=%s&xszyid=%s"
                        % (stu["wlkcid"], stu["xszyid"]),
                        session=session,
                    ),
                    "html.parser",
                )
                files = page.find_all(class_="wdhere")
                os.chdir(path)  # to avoid filename too long
                for f in files:
                    if f.text == "\n":
                        continue
                    try:
                        id = f.find_all("span")[0].attrs["onclick"].split("'")[1]
                        name = f.find_all("span")[0].text
                    except:
                        try:
                            id = f.find_all("a")[-1].attrs["onclick"].split("'")[1]
                            name = f.find_all("a")[0].text
                        except:  # another error
                            continue
                    if not name.startswith(stu["xh"]):
                        name = stu["xh"] + "_" + name
                    download(
                        "/b/wlxt/kczy/xszy/teacher/downloadFile/%s/%s"
                        % (stu["wlkcid"], id),
                        name=name,
                        session=session,
                    )
                os.chdir(now)
            stus = get_json(
                "/b/wlxt/kczy/xszy/teacher/getUndoInfo", data, session=session
            )["object"]["aaData"]
            for stu in stus:
                append_hw_csv(os.path.join(path, "info_%s.csv" % c["wlkcid"]), stu)

            """
            get html from url like 
            https://learn.tsinghua.edu.cn/f/wlxt/kczy/zy/student/viewZy?wlkcid=2025-2026-1150244476&sfgq=0&zyid=26ef84e7994c976201994fe0c4190109&xszyid=26ef84e8994c97b70199500923131cfb
            """


def parse_homework_detail(html_content):
    soup = bs(html_content, "html.parser")

    # 提取作业信息的各个字段
    homework_info = {}

    # 查找所有的list项
    list_items = soup.find_all("div", class_="list")

    for item in list_items:
        left_div = item.find("div", class_="left")
        right_div = item.find("div", class_="right")

        if left_div and right_div:
            key = left_div.get_text(strip=True)

            # 根据不同的字段类型提取内容
            if key == "作业标题":
                homework_info["title"] = right_div.get_text(strip=True)
            elif key == "作业说明":
                # 提取作业说明的详细内容
                content_div = right_div.find("div", class_="c55")
                if content_div:
                    # 保留段落结构
                    paragraphs = content_div.find_all("p")
                    if paragraphs:
                        homework_info["description"] = "\n\n".join(
                            [
                                p.get_text(strip=True)
                                for p in paragraphs
                                if p.get_text(strip=True)
                            ]
                        )
                    else:
                        homework_info["description"] = content_div.get_text(strip=True)
                else:
                    homework_info["description"] = right_div.get_text(strip=True)
            elif key == "答案说明":
                content_div = right_div.find("div", class_="c55")
                if content_div:
                    paragraphs = content_div.find_all("p")
                    if paragraphs:
                        homework_info["answer_description"] = "\n\n".join(
                            [
                                p.get_text(strip=True)
                                for p in paragraphs
                                if p.get_text(strip=True)
                            ]
                        )
                    else:
                        homework_info["answer_description"] = content_div.get_text(
                            strip=True
                        )
                else:
                    homework_info["answer_description"] = right_div.get_text(strip=True)
            elif key == "发布对象":
                homework_info["target_audience"] = right_div.get_text(strip=True)
            elif key == "完成方式":
                homework_info["completion_method"] = right_div.get_text(strip=True)
            elif key == "截止日期(GMT+8)":
                homework_info["deadline"] = right_div.get_text(strip=True)
            elif key == "补交截止时间":
                homework_info["makeup_deadline"] = right_div.get_text(strip=True)

    # 提取作业附件和答案附件
    fujian_items = soup.find_all("div", class_="fujian")
    for fujian in fujian_items:
        left_div = fujian.find("div", class_="left")
        right_div = fujian.find("div", class_="right")

        if left_div and right_div:
            key = left_div.get_text(strip=True)

            # 查找附件链接
            links = right_div.find_all("a")
            if links:
                attachment_list = []
                for link in links:
                    attachment_list.append(
                        {
                            "name": link.get_text(strip=True),
                            "href": link.get("href", ""),
                        }
                    )

                if key == "作业附件":
                    homework_info["attachments"] = attachment_list
                elif key == "答案附件":
                    homework_info["answer_attachments"] = attachment_list
            else:
                if key == "作业附件":
                    homework_info["attachments"] = []
                elif key == "答案附件":
                    homework_info["answer_attachments"] = []

    return homework_info


def build_homework_markdown(homework_info):
    markdown_content = []

    # 作业标题
    if homework_info.get("title"):
        markdown_content.append(f"# {homework_info['title']}\n")

    # 作业说明
    if homework_info.get("description"):
        markdown_content.append("## 作业说明\n")
        markdown_content.append(f"{homework_info['description']}\n")

    # 作业附件
    if homework_info.get("attachments"):
        markdown_content.append("## 作业附件\n")
        for attachment in homework_info["attachments"]:
            if attachment["name"]:
                markdown_content.append(
                    f"- [{attachment['name']}]({attachment['href']})\n"
                )
        markdown_content.append("")

    # 答案说明
    if (
        homework_info.get("answer_description")
        and homework_info["answer_description"].strip()
    ):
        markdown_content.append("## 答案说明\n")
        markdown_content.append(f"{homework_info['answer_description']}\n")

    # 答案附件
    if homework_info.get("answer_attachments"):
        markdown_content.append("## 答案附件\n")
        for attachment in homework_info["answer_attachments"]:
            if attachment["name"]:
                markdown_content.append(
                    f"- [{attachment['name']}]({attachment['href']})\n"
                )
        markdown_content.append("")

    # 其他信息
    markdown_content.append("## 作业信息\n")

    if homework_info.get("target_audience"):
        markdown_content.append(f"**发布对象**: {homework_info['target_audience']}\n")

    if homework_info.get("completion_method"):
        markdown_content.append(f"**完成方式**: {homework_info['completion_method']}\n")

    if homework_info.get("deadline"):
        markdown_content.append(f"**截止日期**: {homework_info['deadline']}\n")

    if (
        homework_info.get("makeup_deadline")
        and homework_info["makeup_deadline"].strip()
    ):
        markdown_content.append(
            f"**补交截止时间**: {homework_info['makeup_deadline']}\n"
        )

    return "\n".join(markdown_content)


def build_discuss(s):
    return "课程：%s\n内容：%s\n学号：%s\n姓名：%s\n发布时间:%s\n最后回复：%s\n回复时间：%s\n" % (
        s["kcm"],
        s["bt"],
        s["fbr"],
        s["fbrxm"],
        s["fbsj"],
        s["zhhfrxm"],
        s["zhhfsj"],
    )


def sync_discuss(session, c):
    global dist_path
    pre = os.path.join(dist_path, c["kcm"], "讨论")
    if not os.path.exists(pre):
        os.makedirs(pre)
    try:
        disc = get_json(
            "/b/wlxt/bbs/bbs_tltb/%s/kctlList?wlkcid=%s" % (c["_type"], c["wlkcid"]),
            session=session,
        )["object"]["resultsList"]
    except:
        return
    for d in disc:
        filename = os.path.join(pre, escape(d["bt"]) + ".txt")
        if os.path.exists(filename):
            continue
        try:
            html = get_page(
                "/f/wlxt/bbs/bbs_tltb/%s/viewTlById?wlkcid=%s&id=%s&tabbh=2&bqid=%s"
                % (c["_type"], d["wlkcid"], d["id"], d["bqid"]),
                session=session,
            )
            open(filename, "w").write(
                build_discuss(d) + bs(html, "html.parser").find(class_="detail").text
            )
        except:
            pass


def gethash(fname):
    if platform.system() == "Linux":
        return subprocess.check_output(["md5sum", fname]).decode().split()[0]
    hash_md5 = hashlib.md5()
    with open(fname, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def dfs_clean(d):
    subdirs = [
        os.path.join(d, i) for i in os.listdir(d) if os.path.isdir(os.path.join(d, i))
    ]
    for i in subdirs:
        dfs_clean(i)
    files = [
        os.path.join(d, i) for i in os.listdir(d) if os.path.isfile(os.path.join(d, i))
    ]
    info = {}
    for f in files:
        if os.path.getsize(f):
            info[f] = {
                "size": os.path.getsize(f),
                "time": os.path.getmtime(f),
                "hash": "",
                "rm": 0,
            }
    info = list(
        {
            k: v for k, v in sorted(info.items(), key=lambda item: item[1]["size"])
        }.items()
    )
    for i in range(len(info)):
        for j in range(i):
            if info[i][1]["size"] == info[j][1]["size"]:
                if info[i][1]["hash"] == "":
                    info[i][1]["hash"] = gethash(info[i][0])
                if info[j][1]["hash"] == "":
                    info[j][1]["hash"] = gethash(info[j][0])
                if info[i][1]["hash"] == info[j][1]["hash"]:
                    if info[i][1]["time"] < info[j][1]["time"]:
                        info[i][1]["rm"] = 1
                    elif info[i][1]["time"] > info[j][1]["time"]:
                        info[j][1]["rm"] = 1
                    elif len(info[i][0]) < len(info[j][0]):
                        info[i][1]["rm"] = 1
                    elif len(info[i][0]) > len(info[j][0]):
                        info[j][1]["rm"] = 1
    rm = [i[0] for i in info if i[1]["rm"] or i[1]["size"] == 0]
    if rm:
        print("rmlist:", rm)
        for f in rm:
            os.remove(f)


def clear(args):
    courses = [i for i in os.listdir(".") if os.path.isdir(i) and not i.startswith(".")]
    if args.all:
        pass
    else:
        if args.course:
            courses = [i for i in courses if i in args.course]
        if args.ignore:
            courses = [i for i in courses if i not in args.ignore]
    courses.sort()
    for i, c in enumerate(courses):
        print("Checking #%d %s" % (i + 1, c))
        for subdir in ["课件", "作业"]:
            d = os.path.join(c, subdir)
            if os.path.exists(d):
                dfs_clean(d)


def process_course(c, args):
    # 处理单个课程的函数，用于多进程
    build_global(args)
    from browser_login import BrowserLoginManager

    blm = BrowserLoginManager()
    ok = blm.load_session_info("session.json", verify=False)

    if ok:
        session = blm.get_session()
    else:
        print("❌ 未能创建新会话")
        return

    c["_type"] = {"0": "teacher", "3": "student"}[c["jslx"]]
    print("Sync " + c["xnxq"] + " " + c["kcm"])

    if not os.path.exists(os.path.join(dist_path, c["kcm"])):
        os.makedirs(os.path.join(dist_path, c["kcm"]))
    sync_discuss(session, c)
    sync_notify(session, c)
    sync_file(session, c)
    sync_hw(session, c)

    return c["kcm"]


async def main(args):
    global dist_path, cookie
    build_global(args)
    assert (
        (dist_path is not None)
        and (url is not None)
        and (user_agent is not None)
        and (headers is not None)
        and (cookie is not None)
        and (opener is not None)
        and (err404 is not None)
    )
    if args.clear:
        clear(args)
        exit()
    args.login = False
    if args.cookie:
        cookie.load(args.cookie, ignore_discard=True, ignore_expires=True)
        args.login = get_page("/b/wlxt/kc/v_wlkc_xs_xktjb_coassb/queryxnxq") != err404
        print("login successfully" if args.login else "login failed!")
    else:
        username = args.username if args.username else None

        from browser_login import BrowserLoginManager

        try:
            login_manager = BrowserLoginManager(username)

            # 执行交互式登录
            login_success = await login_manager.interactive_login()

            if (
                login_success
                and hasattr(login_manager, "session")
                and login_manager.session
            ):
                print("✅ 浏览器登录成功！")
                login_manager.save_session_info("session.json")
                session = login_manager.get_session()
                if session:
                    print("✅ 浏览器会话有效！")
                else:
                    print("❌ 浏览器会话无效！")
                args.login = True
            else:
                print("❌ 浏览器登录失败")
                args.login = False

        except Exception as e:
            print(f"❌ 浏览器登录过程中出错: {e}")
            args.login = False

    if args.login:
        courses = get_courses(session, args)

        if args.multi:
            # 如果未指定进程数，则使用CPU核数
            if not args.processes:
                args.processes = mp.cpu_count()
            print(f"启动多进程下载，进程数：{args.processes}")
            pool = mp.Pool(processes=args.processes)
            process_func = partial(process_course, args=args)
            for _ in tqdm(
                pool.imap_unordered(process_func, courses),
                total=len(courses),
                desc="处理课程",
            ):
                pass

            pool.close()
            pool.join()
        else:
            # 原始单进程处理
            for c in courses:
                c["_type"] = {"0": "teacher", "3": "student"}[c["jslx"]]
                print("Sync " + c["xnxq"] + " " + c["kcm"])
                if not os.path.exists(os.path.join(dist_path, c["kcm"])):
                    os.makedirs(os.path.join(dist_path, c["kcm"]))
                sync_info(session, c)
                sync_discuss(session, c)
                sync_notify(session, c)
                sync_file(session, c)
                sync_hw(session, c)


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--all", action="store_true")
    parser.add_argument(
        "--clear", action="store_true", help="remove the duplicate course file"
    )
    parser.add_argument("--semester", nargs="+", type=str, default=[])
    parser.add_argument("--ignore", nargs="+", type=str, default=[])
    parser.add_argument("--course", nargs="+", type=str, default=[])
    parser.add_argument("-p", "--_pass", type=str, default=".pass")
    parser.add_argument(
        "-c", "--cookie", type=str, default="", help="Netscape HTTP Cookie File"
    )
    parser.add_argument("-d", "--dist", type=str, default="", help="download path")
    parser.add_argument("--http_proxy", type=str, default="", help="http proxy")
    parser.add_argument("--https_proxy", type=str, default="", help="https proxy")
    parser.add_argument("--username", type=str, default="", help="username")
    parser.add_argument("--password", type=str, default="", help="password")
    parser.add_argument("--multi", action="store_true", help="multi-process")
    parser.add_argument("--processes", type=int, help="concurrent processes")
    parser.add_argument(
        "--reset-fingerprint",
        action="store_true",
        help="reset saved fingerprint data for fresh login",
    )
    args = parser.parse_args()
    return args


if __name__ == "__main__":
    asyncio.run(main(get_args()))
