#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# vim: set fenc=utf-8 ai ts=4 sw=4 sts=4 et:

import re
import sys
import subprocess
import os.path
from copy import deepcopy
from configparser import ConfigParser

DEFAULT_CONFIG = {
    '7zip': '7z',
    'mx': 5,
    'exclude': list(),
}

CONFIG_VARIABLES = (
    'backupdir',
    'backupdir2',
    '7zip',
    'name',
    'mx',
    'full_alert',
)

CONFIG_LIST_VARIABLES = (
    'include',
    'exclude'
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

    if 'include' not in config:
        raise KeyError("Missing include")

    for i in config['include']:
        if i[0] == '!' and not os.path.exists(i):
            raise IOError("File or directory does not exist", i)

    config['mx'] = int(config['mx'])
    if config['mx'] < 0 or config['mx'] > 9:
        raise ValueError("mx config must be between 0 and 9")

    return config


def main(argv):
    config = read_config(argv[1])

    print(config)


if __name__ == '__main__':
    if len(sys.argv) != 2:
        sys.stderr.write("Usage: {} <config file>\n".format(sys.argv[0]))
    else:
        main(sys.argv)

