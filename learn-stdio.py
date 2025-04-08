#!/usr/bin/env python3

import time, argparse
from learn_async import main
import os


def get(help, choices=None, default=None):
    while True:
        i = input(help)
        if i:
            if choices and i not in choices:
                pass
            else:
                if default == []:
                    i = i.split()
                return i
        else:
            return default


def get_args():
    parser = argparse.ArgumentParser()
    args = parser.parse_args()
    print("按回车选择默认选项 ...")
    args.all = get(
        "同步所有学期的所有课程 [y/N]：", choices=["Y", "N", "y", "n"], default=None
    )
    if args.all in ["n", "N"]:
        args.all = None
    args.clear = get("清空相同文件 [y/N]：", choices=["Y", "N", "y", "n"], default=None)
    if args.clear in ["n", "N"]:
        args.clear = None
    args.semester = get("学期：", default=[])
    args.course = get("指定课程：", default=[])
    args.ignore = get("忽略课程：", default=[])
    args.dist = get("下载路径(默认当前目录)：", default="")
    if len(args.dist) != 0:
        if not os.path.exists(args.dist):
            multi = get(
                f"路径{args.dist}不存在，是否创建? [Y/n]",
                choices=["Y", "N", "y", "n"],
                default="Y",
            )
            if multi in ["y", "Y"]:
                os.makedirs(args.dist)
            else:
                exit()
    multi = get("是否启用多进程?[y/N]", choices=["Y", "N", "y", "n"], default="N")
    if multi in ["y", "Y"]:
        args.multi = True
        args.processes = get("进程数(默认使用所有CPU核心数):", default=None)
    else:
        args.multi = False
    args._pass = ".pass"
    args.cookie = ""
    args.http_proxy = ""
    args.https_proxy = ""
    args.username = ""
    args.password = ""
    return args


if __name__ == "__main__":
    t = time.time()
    main(get_args())
    t = time.time() - t
    print("耗时: %02d:%02d:%02.0f" % (t // 3600, (t % 3600) // 60, t % 60))
    input("请按任意键退出")
