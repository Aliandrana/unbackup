#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# vim: set fenc=utf-8 ai ts=4 sw=4 sts=4 et:

import re
import sys
import datetime
import subprocess
import os.path
from copy import deepcopy
try:
    from configparser import ConfigParser
except ImportError:
    from ConfigParser import ConfigParser

DEFAULT_CONFIG = {
    '7zip': '7z',
    'mx': 5,
    'exclude': list(),
    'exclude-recursive': list(),
}

CONFIG_VARIABLES = (
    'backupdir',
    'backupdir2',
    '7zip',
    'name',
    'mx',
)

CONFIG_LIST_VARIABLES = (
    'backup',
    'exclude',
    'exclude-recursive',
)

def read_config(filename):
    ret = deepcopy(DEFAULT_CONFIG)

    current_group = ''

    with open(filename, 'r') as fp:
        for line in fp:
            line = line.strip()

            # ignore comments
            line = re.sub(r'\s*#.*$', '', line)

            if not line:
                continue

            m = re.match(r'^\s*(.+?)\s*=\s*(.+)\s*$', line)
            if m:
                k = m.group(1)
                if k not in CONFIG_VARIABLES:
                    raise KeyError("Unknown key in config", k)

                ret[k] = m.group(2)

            else:
                m = re.match(r'^\s*\[\s*(.+?)\s*\]\s*$', line)
                if m:
                    k = m.group(1)
                    if k not in CONFIG_LIST_VARIABLES:
                        raise KeyError("Unknown list type", k)
                    
                    current_group = k

                    if current_group not in ret:
                        ret[current_group] = list()
                else:
                        ret[current_group].append(line)

    return verify_config(ret)



def verify_config(config):
    if 'backupdir' not in config:
        raise KeyError("Missing backupdir")

    if 'backup' not in config:
        raise KeyError("Missing backup section")

    for i in config['backup']:
        if i[0] == '!' and not os.path.exists(i):
            raise IOError("File or directory does not exist", i)

    config['mx'] = int(config['mx'])
    if config['mx'] < 0 or config['mx'] > 9:
        raise ValueError("mx config must be between 0 and 9")

    return config



def timestamp():
    return datetime.datetime.now().strftime("%Y%m%d%H%M")



def get_backup_directory(config):
    if os.path.isdir(config['backupdir']):
        return config['backupdir']

    if 'backupdir2' in config and os.path.isdir(config['backupdir2']):
       return config['backupdir2']

    raise IOError("Cannot find backup directory")



def most_recent_full_backup(config):
    bd = get_backup_directory(config)

    regex = re.compile(r'^' + re.escape(config['name'] + '-') + r'\d{12}\.7z$')

    filename = None

    fnlist = os.listdir(bd)
    fnlist.sort()

    for fn in fnlist:
        if regex.match(fn):
            filename = os.path.join(bd, fn)

    if not filename:
        raise IOError("Cannot find a full backup", bd)

    return filename



def full_backup(config):
    backup_dir = get_backup_directory(config)
    backup_file = os.path.join(backup_dir, config['name'] + '-' + timestamp() + '.7z')

    pargs = [
        config['7zip'],
        'a', backup_file,
        '-t7z', '-mx' + str(config['mx']),
    ]

    for i in config['exclude']:
        pargs.append('-x!' + i)

    for i in config['exclude-recursive']:
        pargs.append('-xr!' + i)

    for i in config['backup']:
        pargs.append(i)

    r = subprocess.call(pargs, shell=False)

    if r > 1:
        raise Exception("Error with 7zip")

    return backup_file



def diff_backup(config):
    full_bfn = most_recent_full_backup(config)

    backup_dir = get_backup_directory(config)
    backup_file = full_bfn[0:-3] + '-diff-' + timestamp() + '.7z'

    pargs = [
        config['7zip'],
        'u', full_bfn,
        '-t7z', '-mx' + str(config['mx']),
    ]

    for i in config['exclude']:
        pargs.append('-x!' + i)

    for i in config['exclude-recursive']:
        pargs.append('-xr!' + i)

    for i in config['backup']:
        pargs.append(i)

    # ::KUDOS Javier - https://superuser.com/a/948380::
    pargs.append('-u-')                             # Don't update the full backup
    pargs.append('-up0q3r2x2y2z0w2!' + backup_file) # only write files that changed

    r = subprocess.call(pargs, shell=False)

    if r > 1:
        raise Exception("Error with 7zip")

    return backup_file



def main(argv):
    if len(sys.argv) < 2 or len(sys.argv) > 3:
        sys.stderr.write("Usage: {} <config file> [full|diff]\n".format(sys.argv[0]))
        sys.exit(2) 

    config = read_config(argv[1])

    if len(argv) < 3:
        diff_backup(config)
    else:
        if argv[2] == 'full':
            full_backup(config)
        elif argv[2] == 'diff':
            diff_backup(config)
        else:
            raise ValueError("Excepected full or diff")



if __name__ == '__main__':
        main(sys.argv)

