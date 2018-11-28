# download-learn
清华大学旧版网络学堂课程文件自动下载脚本



## Dependency

python3, bs4

```bash
sudo pip3 install bs4
```



## Usage

```bash
./learn.py [type_number]
```

默认是1，为当前学期课程。0是全部，2是除当前之外的课程，其他没试过

如果不想下载某门课程（比如实验室科研探究），可以在同级目录下新建文件`.ignore`，并添加该课程完整名字，比如：

```bash
➜  wjy git:(master) ✗ cat .ignore 
数据结构(2)(2017-2018秋季学期)
实验室科研探究（4）(90)(2016-2017秋季学期)
实验室科研探究（3）(90)(2016-2017春季学期)
```



## Features

1. 下载所有课件
2. 下载所有作业文件
3. 增量更新
4. 可选下载课程