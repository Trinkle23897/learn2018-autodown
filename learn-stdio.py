#!/usr/bin/env python3

import argparse
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
    print('Press "Enter" for default option ...')
    args.all = get('Sync all course [y/N]: ', choices=['Y', 'N', 'y', 'n'], default=None)
    if args.all in ['n', 'N']:
        args.all = None
    args.clear = get('Remove the duplicate course file [y/N]: ', choices=['Y', 'N', 'y', 'n'], default=None)
    if args.clear in ['n', 'N']:
        args.clear = None
    args.semester = get('Semesters: ', default=[])
    args.course = get('Specify courses: ', default=[])
    args.ignore = get('Ignore courses: ', default=[])
    return args

if __name__ == '__main__':
    main(get_args())