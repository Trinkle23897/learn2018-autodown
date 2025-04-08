# 清华大学新版网络学堂课程自动下载脚本

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
pip3 install -r requirements.txt --user -U
```

## Usage

`learn-stdio.py` 中显示的参数和下面是一样的。

### 下载选项

下载当前学期课程（默认）

```bash
./learn_async.py
```

下载所有学期课程

```bash
./learn_async.py --all
```

下载指定学期课程

```bash
./learn_async.py --semester 2018-2019-1 2018-2019-3
```

下载指定课程

```bash
./learn_async.py --course 计算机网络安全技术 计算机组成原理
```

跳过某几个课程下载

```bash
./learn_async.py --ignore 数据结构 "实验室科研探究(1)"
```

移除所有文件夹下完全相同的文件

```bash
./learn_async.py --clear --all
```

指定下载路径

```bash
./learn_async.py --dist your_download_path
```

启用多进程下载

```bash
./learn_async.py --multi
```

启用多进程下载，并指定进程数（如果不指定则默认使用所有 CPU 核心数）

```bash
./learn_async.py --multi --processes 4
```

以上参数均可组合使用，比如我想并发的更新大二的课程到`./download`目录，但是不想下载数据结构、实验室科研探究、中国近现代史纲要（课程文件太大了）：

```bash
./learn_async.py --semester 2017-2018-1 2017-2018-2 2017-2018-3 --ignore 数据结构 "实验室科研探究(2)" 中国近现代史纲要 --multi --dist ./download
```

**如果想跳过正在下载的某个文件，按 Ctrl+C 即可。**

### 登录选项（learn-stdio 中禁用）

懒得每次输入 info 账号密码？创建文件`.pass`，写入 info 账号和密码之后可以自动登录，或者是：

```bash
./learn_async.py --_pass your_info_file
```

其中文件格式为

```bash
info账号
info密码
```

使用 Cookie 登录而不是输入 info 密码：

```bash
./learn_async.py --cookie your_cookie_filename
```

其中 cookie 文件格式可参考 `example_cookie.txt`。

## Common Issues

- 卡在 login：网络原因，看看 pulse-secure 关了没，重跑试试看
- `500 : Internal Server Error`：请拉取最新版的脚本。网络学堂自 2020/2/22 开启强制 https。
- `info_xxx.csv`在 Mac 下打开是乱码：别用 office，用 mac 自带的软件吧 :)
