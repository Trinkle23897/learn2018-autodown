# 清华大学新版网络学堂课程自动下载脚本

## Dependency

python3, bs4, tqdm, requests

```bash
pip3 install bs4 tqdm requests --user
```

## Usage

```bash
# 下载当前学期课程
./learn.py
# 下载所有学期课程
./learn.py 0
# 下载指定课程
./learn.py 计算机网络安全技术
```

如果不想下载某门课程（比如实验室科研探究），可以在同级目录下新建文件`.ignore`，并添加该课程完整名字，比如：

```bash
➜  wjy git:(master) ✗ cat .ignore 
计算机组成原理
计算机网络安全技术
```

## Features

0. 下载所有课程公告
1. 下载所有课件
2. 下载所有作业文件及其批阅情况
3. 增量更新
4. 可选下载课程

## Common Issues

1. `json.decoder.JSONDecodeError`: 目前看起来是网络不稳定导致，可以重跑试试看

2. 卡在login：还是网络原因，看看pulse-secure关了没（最好是要在校园网环境下，因为我是在所有ubuntu下测过，包括实验室服务器，可是我本地自己在校外环境测试也没问题呀qwq……）
