sso_login_url = "https://id.tsinghua.edu.cn/do/off/ui/auth/login/form/bb5df85216504820be7bba2b0ae1535b/0"
wlxt_url = "https://learn.tsinghua.edu.cn/f/wlxt/index/course/student/"
learn_base_url = "https://learn.tsinghua.edu.cn"
success_indicators = [
    "learn.tsinghua.edu.cn",
    "myCourse",
    "semesterCourseList",
    "退出登录",
    "注销",
]
# Note: if errors occur due to imcompatible os (like windows), you can change the following user-agent to "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
default_headers = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Referer": "https://learn.tsinghua.edu.cn/",
}
test_urls = [
    "https://learn.tsinghua.edu.cn/f/wlxt/index/course/student/",
    "https://learn.tsinghua.edu.cn/b/kc/zhjw_v_code_xnxq/getCurrentAndNextSemester",
    "https://learn.tsinghua.edu.cn/b/wlxt/kc/v_wlkc_xs_xktjb_coassb/queryxnxq",
]
