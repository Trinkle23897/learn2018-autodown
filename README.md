# 清华大学新版网络学堂课程自动下载脚本

## 🌟 最新功能：浏览器交互式登录

现已支持**浏览器交互式登录**，解决双因素认证登录问题！

```bash
# 使用浏览器登录
python learn_async.py --multi

# 查看快速使用指南
cat QUICK_START.md
```

## Features

0. 跨平台支持：Windows/Mac/Linux 支持双击运行（[详情点击](https://github.com/Trinkle23897/learn2018-autodown/releases)）
1. 下载所有课程公告
2. 下载所有课件
3. 下载所有作业文件及其批阅情况
4. 下载所有课程讨论
5. 下载课程信息
6. 增量更新
7. 可选下载课程
8. 随时按 Ctrl+C 跳过某个文件的下载
9. 下载助教课程
10. 可使用 cookie 登录
11. 多刷刷有利于后台成绩提高，比如以下第三条记录是我的：

![](hint.jpg)

## Dependency

python>=3.5, bs4, tqdm, requests

```bash
pip3 install -r requirements.txt
```

## Usage

#### **⚠️ 重要更新：本脚本已更新支持清华大学网络学堂新的 SSO 双因素认证登录方式（v2.0），以下内容为旧版本，大概率无法正常使用！请移步至 [QUICK START](./QUICK_START.md) 以获取最新使用方法**

---

### 快速开始

```bash
python learn_async.py --username 你的用户名 --password 你的密码
```

程序会自动处理新的登录认证流程，包括设备指纹生成和保存。

### 测试登录功能

```bash
python test_login.py --username 你的用户名 --password 你的密码
```

### 重置设备指纹（如果登录出现问题）

```bash
python learn_async.py --username 你的用户名 --password 你的密码 --reset-fingerprint
```

### CLI 下载

```bash
python learn-stdio.py
```

### 原始脚本下载选项

下载当前学期课程（默认）

```bash
python learn_async.py
```

下载所有学期课程

```bash
python learn_async.py --all
```

下载指定学期课程

```bash
python learn_async.py --semester 2018-2019-1 2018-2019-3
```

下载指定课程

```bash
python learn_async.py --course 计算机网络安全技术 计算机组成原理
```

跳过某几个课程下载

```bash
python learn_async.py --ignore 数据结构 "实验室科研探究(1)"
```

移除所有文件夹下完全相同的文件

```bash
python learn_async.py --clear --all
```

指定下载路径

```bash
python learn_async.py --dist your_download_path
```

启用多进程下载

```bash
python learn_async.py --multi
```

启用多进程下载，并指定进程数（如果不指定则默认使用所有 CPU 核心数）

```bash
python learn_async.py --multi --processes 4
```

以上参数均可组合使用，比如我想并发的更新大二的课程到`./download`目录，但是不想下载数据结构、实验室科研探究、中国近现代史纲要（课程文件太大了）：

```bash
python learn_async.py --semester 2017-2018-1 2017-2018-2 2017-2018-3 --ignore 数据结构 "实验室科研探究(2)" 中国近现代史纲要 --multi --dist ./download
```

**如果想跳过正在下载的某个文件，按 Ctrl+C 即可。**

### 登录选项（learn-stdio 中禁用）

懒得每次输入 info 账号密码？创建文件`.pass`，写入 info 账号和密码之后可以自动登录，或者是：

```bash
python learn_async.py --_pass your_info_file
```

其中文件格式为

```bash
info账号
info密码
```

使用 Cookie 登录而不是输入 info 密码：

```bash
python learn_async.py --cookie your_cookie_filename
```

其中 cookie 文件格式可参考 `example_cookie.txt`。

## Common Issues

### v2.0 新版本问题

- **登录失败**：尝试使用 `--reset-fingerprint` 参数重新生成设备指纹
- **双因素认证问题**：首次使用可能需要在浏览器中完成设备信任，程序会自动处理大部分情况
- **设备指纹相关**：指纹数据保存在 `.fingerprint_{用户名}.json` 文件中，如有问题可手动删除

### 通用问题

- 卡在 login：网络原因，看看 pulse-secure 关了没，重跑试试看
- `500 : Internal Server Error`：请拉取最新版的脚本。网络学堂自 2020/2/22 开启强制 https。
- `info_xxx.csv`在 Mac 下打开是乱码：别用 office，用 mac 自带的软件吧 :)
