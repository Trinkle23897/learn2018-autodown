# 清华大学新版网络学堂课程自动下载脚本

## News

支持windows双击运行了！[详情点击](https://github.com/Trinkle23897/learn2018-autodown/releases)

## Dependency

python>=3.5, bs4, tqdm, requests

```bash
pip3 install -r requirements.txt --user -U
```

## Usage

`learn-stdio.py` 中显示的参数和下面是一样的。

下载当前学期课程（默认）
```bash
./learn.py
```
下载所有学期课程
```bash
./learn.py --all
```
下载指定学期课程
```bash
./learn.py --semester 2018-2019-1 2018-2019-3
```
下载指定课程
```bash
./learn.py --course 计算机网络安全技术 计算机组成原理
```
跳过某几个课程下载
```bash
./learn.py --ignore 数据结构 "实验室科研探究(1)"
```
移除所有文件夹下完全相同的文件
```bash
./learn.py --clear --all
```
以上参数均可组合使用，比如我想更新大二的课程，但是不想下载数据结构、实验室科研探究、中国近现代史纲要（课程文件太大了）：

```bash
./learn.py --semester 2017-2018-1 2017-2018-2 2017-2018-3 --ignore 数据结构 "实验室科研探究(2)" 中国近现代史纲要
```

懒得每次输入info账号密码？创建文件`.pass`，写入info账号和密码之后可以自动登录。

如果想跳过正在下载的某个文件，按Ctrl+C即可。

## Features

0. 下载所有课程公告
1. 下载所有课件
2. 下载所有作业文件及其批阅情况
3. 下载所有课程讨论
4. 下载课程信息
5. 增量更新
6. 可选下载课程
7. 下载助教课程

## Common Issues

- 卡在login：网络原因，看看pulse-secure关了没，重跑试试看
- `500 : Internal Server Error`：请拉取最新版的脚本。网络学堂自2020/2/22开启强制https。
