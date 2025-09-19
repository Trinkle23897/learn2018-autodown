#!/usr/bin/env python3
import os
import json
import time
import uuid
import requests

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.common.exceptions import TimeoutException, WebDriverException

from data import (
    sso_login_url,
    wlxt_url,
    learn_base_url,
    success_indicators,
    default_headers,
    test_urls,
)


def generate_fingerprint():
    """生成用于双因素认证的指纹"""
    return str(uuid.uuid4()).replace("-", "")


def save_fingerprint_data(
    username, fingerprint, finger_gen_print="", finger_gen_print3=""
):
    """保存指纹数据到文件"""
    fingerprint_file = f".fingerprint_{username}.json"
    data = {
        "fingerPrint": fingerprint,
        "fingerGenPrint": finger_gen_print,
        "fingerGenPrint3": finger_gen_print3,
        "timestamp": time.time(),
    }
    with open(fingerprint_file, "w", encoding="utf-8") as f:
        json.dump(data, f)
    return data


def load_fingerprint_data(username):
    """从文件加载指纹数据"""
    fingerprint_file = f".fingerprint_{username}.json"
    if os.path.exists(fingerprint_file):
        try:
            with open(fingerprint_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                # 检查数据是否过期（7天）
                if time.time() - data.get("timestamp", 0) < 7 * 24 * 3600:
                    return data
        except:
            pass
    return None


BROWSER_LOGIN_AVAILABLE = True

cookie = None

# 声明全局变量
dist_path = url = user_agent = headers = opener = err404 = fingerprint_data = None


class BrowserLoginManager:
    """基于浏览器的登录管理器"""

    def __init__(self, username=None, headless=False, browser="chrome"):
        self.username = username
        self.headless = headless
        self.browser = browser.lower()
        self.driver = None
        self.session = None
        self.cookies = {}
        self.fingerprint_data = None

        self.sso_login_url = sso_login_url
        self.wlxt_url = wlxt_url
        self.learn_base_url = learn_base_url
        self.success_indicators = success_indicators

        try:
            if self.browser == "chrome":
                options = ChromeOptions()
                if self.headless:
                    options.add_argument("--headless")
                options.add_argument("--no-sandbox")
                options.add_argument("--disable-dev-shm-usage")
                options.add_argument("--disable-gpu")
                # Note: if errors occur due to imcompatible os (like windows), you can change the following user-agent to "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                options.add_argument(
                    "--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                )

                self.driver = webdriver.Chrome(options=options)

            elif self.browser == "firefox":
                options = FirefoxOptions()
                if self.headless:
                    options.add_argument("--headless")

                self.driver = webdriver.Firefox(options=options)

            else:
                raise ValueError(f"不支持的浏览器: {self.browser}")

            # 设置页面加载超时
            self.driver.set_page_load_timeout(30)
            self.driver.implicitly_wait(10)

            print(f"✅ {self.browser.title()} 浏览器已启动")
            # return True

        except WebDriverException as e:
            raise ValueError(f"启动浏览器失败: {e}")

    def load_or_generate_fingerprint(self):
        """加载或生成设备指纹"""
        try:
            # 尝试加载已保存的指纹
            if self.username:
                self.fingerprint_data = load_fingerprint_data(self.username)
                if self.fingerprint_data:
                    print(f"✅ 加载已保存的设备指纹")
                    return True
        except Exception as e:
            print(f"⚠️ 加载指纹失败: {e}")

        # 生成新指纹
        try:
            fingerprint = generate_fingerprint()

            self.fingerprint_data = {
                "fingerPrint": fingerprint,
                "fingerGenPrint": "gen1",
                "fingerGenPrint3": "gen3",
                "timestamp": time.time(),
            }

            if self.username:
                save_fingerprint_data(self.username, self.fingerprint_data)
                print(f"💾 新指纹已保存")

            return True

        except Exception as e:
            print(f"❌ 生成指纹失败: {e}")
            return False

    def wait_for_login_success(self, timeout=300):
        """等待用户完成登录"""
        print("⏳ 请在浏览器中完成登录...")
        print("💡 登录成功后程序会自动继续")

        start_time = time.time()
        last_url = ""

        while time.time() - start_time < timeout:
            try:
                current_url = self.driver.current_url
                page_source = self.driver.page_source

                # 检查URL变化
                if current_url != last_url:
                    print(f"🔄 页面跳转: {current_url}")
                    last_url = current_url

                # 检查是否登录成功
                if any(
                    indicator in current_url for indicator in self.success_indicators
                ) or any(
                    indicator in page_source for indicator in self.success_indicators
                ):
                    print("✅ 检测到登录成功！")

                    time.sleep(3)

                    return True

                # 检查是否在学堂页面
                if (
                    "learn.tsinghua.edu.cn" in current_url
                    and "login" not in current_url
                ):
                    print("✅ 已进入网络学堂页面！")
                    time.sleep(5)
                    return True

                time.sleep(2)

            except Exception as e:
                print(f"⚠️ 检查登录状态时出错: {e}")
                time.sleep(2)

        print("⏰ 等待登录超时")
        return False

    def extract_cookies(self):
        """提取浏览器cookies"""
        try:
            cookies = self.driver.get_cookies()
            self.cookies = {}

            for cookie in cookies:
                self.cookies[cookie["name"]] = cookie["value"]

            print(f"📝 提取到 {len(self.cookies)} 个cookies")

            # 打印cookies信息用于调试
            print("🔍 Cookies详情:")
            for name, value in self.cookies.items():
                print(f"  {name}: {value[:20]}...")

            return True

        except Exception as e:
            print(f"❌ 提取cookies失败: {e}")
            return False

    def create_session_with_cookies(self):
        """使用提取的cookies创建会话"""
        try:
            import requests

            self.session = requests.Session()

            # 从浏览器获取完整的cookies信息
            browser_cookies = self.driver.get_cookies()

            # 提取XSRF-TOKEN用于CSRF保护
            xsrf_token = None

            # 设置cookies（包含域名和路径信息）
            for cookie in browser_cookies:
                self.session.cookies.set(
                    name=cookie["name"],
                    value=cookie["value"],
                    domain=cookie.get("domain", ".tsinghua.edu.cn"),
                    path=cookie.get("path", "/"),
                    secure=cookie.get("secure", False),
                )

                # 记录XSRF-TOKEN
                if cookie["name"] == "XSRF-TOKEN":
                    xsrf_token = cookie["value"]

            headers = default_headers
            # 如果有XSRF-TOKEN，添加到请求头
            if xsrf_token:
                headers["X-XSRF-TOKEN"] = xsrf_token
                print(f"🔐 已设置XSRF-TOKEN: {xsrf_token[:20]}...")

            self.session.headers.update(headers)

            print("✅ 会话创建成功")
            return True

        except Exception as e:
            print(f"❌ 创建会话失败: {e}")
            return False

    def verify_session(self):
        """验证会话是否有效"""
        # 尝试多个不同的API端点
        success_count = 0

        for i, test_url in enumerate(test_urls, 1):
            try:
                print(f"🧪 测试API端点 {i}/{len(test_urls)}: {test_url}")
                response = self.session.get(test_url)

                print(f"🔍 响应状态码: {response.status_code}")
                print(f"🔍 响应URL: {response.url}")

                # 保存响应内容用于调试（无论成功失败）
                debug_filename = f"debug_response_{i}.html"
                with open(debug_filename, "w", encoding="utf-8") as f:
                    f.write(response.text)
                print(f"💾 响应内容已保存到 {debug_filename}")

                if response.status_code == 200:
                    # 检查响应内容
                    response_text_lower = response.text.lower()

                    print("🔍 响应内容检查:")
                    print(f"  包含'login': {'login' in response_text_lower}")
                    print(f"  包含'course': {'course' in response_text_lower}")
                    print(f"  包含'课程': {'课程' in response.text}")
                    print(f"  包含'学期': {'学期' in response.text}")
                    print(f"  响应长度: {len(response.text)} 字符")

                    # 检查是否是有效的登录后页面
                    is_valid_response = (
                        len(response.text) > 1000  # 有实质内容
                        and "login" not in response_text_lower  # 不是登录页面
                        and (
                            "course" in response_text_lower
                            or "课程" in response.text
                            or "学期" in response.text
                            or "semester" in response_text_lower
                            or "wlxt" in response_text_lower
                            or "jsessionid" in response_text_lower
                        )
                    )

                    if is_valid_response:
                        print("✅ 此端点验证成功")
                        success_count += 1
                    else:
                        print("⚠️ 此端点响应可能不正常")
                else:
                    print(f"❌ API端点 {i} 返回错误: {response.status_code}")
                    print(f"🔍 响应长度: {len(response.text)} 字符")

                print()  # 空行分隔

            except Exception as e:
                print(f"❌ 测试API端点 {i} 时出错: {e}")
                print()

        return True

    async def interactive_login(self, verify=False):
        """执行交互式登录"""
        print("🚀 启动基于浏览器的交互式登录...")

        # 加载或生成指纹
        if not self.load_or_generate_fingerprint():
            print("❌ 指纹处理失败")
            return False

        try:
            print(f"🌐 正在打开登录页面...")
            self.driver.get(self.sso_login_url)
            # self.driver.get(self.wlxt_url)

            # 如果有用户名，自动填入
            if self.username:
                try:
                    username_input = WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located((By.ID, "i_user"))
                    )
                    username_input.clear()
                    username_input.send_keys(self.username)
                    print(f"✅ 已自动填入用户名: {self.username}")
                except TimeoutException:
                    print("⚠️ 未找到用户名输入框")

            # 等待用户完成登录
            if not self.wait_for_login_success():
                return False

            # 提取cookies
            if not self.extract_cookies():
                return False

            # 创建会话
            if not self.create_session_with_cookies():
                return False

            # 验证会话
            if verify:
                if not self.verify_session():
                    return False

            print("🎉 交互式登录完成！")
            return True

        except Exception as e:
            print(f"❌ 登录过程中出错: {e}")
            return False

    def get_session(self):
        """获取登录会话"""
        return self.session

    def save_session_info(self, filepath=None):
        """保存会话信息到文件"""
        if not filepath:
            filepath = f"session_{self.username or 'anonymous'}_{int(time.time())}.json"

        try:
            session_info = {
                "username": self.username,
                "cookies": self.cookies,
                "fingerprint": self.fingerprint_data,
                "timestamp": time.time(),
            }

            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(session_info, f, indent=2, ensure_ascii=False)

            print(f"💾 会话信息已保存到: {filepath}")
            return True

        except Exception as e:
            print(f"❌ 保存会话信息失败: {e}")
            return False

    def load_session_info(self, filepath, verify=False):
        """从文件加载会话信息并重建可用的 requests 会话

        :param filepath: 会话信息 JSON 文件路径
        :param verify: 可选，是否在加载后执行一次简单校验
        :return: bool 是否加载成功
        """
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)

            self.username = data.get("username") or self.username
            self.cookies = data.get("cookies") or {}
            self.fingerprint_data = data.get("fingerprint") or self.fingerprint_data

            self.session = requests.Session()

            xsrf_token = self.cookies.get("XSRF-TOKEN") or self.cookies.get(
                "xsrf-token"
            )

            headers = default_headers

            if xsrf_token:
                headers["X-XSRF-TOKEN"] = xsrf_token

            self.session.headers.update(headers)

            domains = [
                ".tsinghua.edu.cn",
                "learn.tsinghua.edu.cn",
                "id.tsinghua.edu.cn",
            ]

            for name, value in (self.cookies or {}).items():
                if value is None:
                    continue
                for domain in domains:
                    self.session.cookies.set(
                        name=name,
                        value=value,
                        domain=domain,
                        path="/",
                        secure=False,
                    )

            if verify:
                return bool(self.verify_session())

            return True

        except Exception as e:
            print(f"❌ 加载会话信息失败: {e}")
            return False

    def close(self):
        """释放浏览器与网络会话等资源"""
        # 关闭浏览器驱动
        if self.driver:
            try:
                self.driver.quit()
            except Exception as e:
                print(f"⚠️ 关闭浏览器失败: {e}")
            finally:
                self.driver = None

        # 关闭 requests 会话
        if self.session:
            try:
                self.session.close()
            except Exception as e:
                print(f"⚠️ 关闭会话失败: {e}")
            finally:
                self.session = None

    def __del__(self):
        try:
            self.close()
        except Exception:
            pass
