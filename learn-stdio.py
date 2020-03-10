#!/usr/bin/env python3

import time, argparse
from learn import main

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
    print('按回车选择默认选项 ...')
    args.all = get('同步所有学期的所有课程 [y/N]：', choices=['Y', 'N', 'y', 'n'], default=None)
    if args.all in ['n', 'N']:
        args.all = None
    args.clear = get('清空相同文件 [y/N]：', choices=['Y', 'N', 'y', 'n'], default=None)
    if args.clear in ['n', 'N']:
        args.clear = None
    args.semester = get('学期：', default=[])
    args.course = get('指定课程：', default=[])
    args.ignore = get('忽略课程：', default=[])
    args._pass = '.pass'
    args.cookie = ''
    return args

if __name__ == '__main__':
    t = time.time()
    main(get_args())
    t = time.time() - t
    print('耗时: %02d:%02d:%02.0f' % (t // 3600, (t % 3600) // 60, t % 60))
    input('请按任意键退出')
