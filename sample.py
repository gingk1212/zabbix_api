#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import time
import datetime
import getpass
from zabbix_api import ZabbixApi
from optparse import OptionParser


# General function
def fail(c=""):
    print "[Fail] %s" % c
    sys.exit(1)


def parse():
    parser = OptionParser()
    parser.add_option(
            '-d', type='string', help='Zabbix server (must)', dest='zabbix')
    parser.add_option(
            '-m', type='string', help='Method (must)', dest='method')
    parser.add_option(
            '--file', type='string',
            help='Input json file name (option)', dest='file')
    parser.add_option(
            '--host', type='string', help='Host name (option)', dest='host')
    parser.add_option(
            '--mapid', type='string', help='Map id (option)', dest='mapid')
    parser.add_option(
            '--gid', type='int', help='Host group id (option)', dest='gid')
    parser.add_option(
            '--key', type='string', help='Item key (option)', dest='key')
    parser.add_option(
            '--itemid', type='int', help='Item ID (option)', dest='itemid')
    parser.add_option(
            '--time_from', type='string',
            help='History time from (%Y/%m/%d %H:%M:%S) (option)',
            dest='time_from')
    (options, args) = parser.parse_args()
    if options.zabbix is None or options.method is None:
        parser.print_help()
        fail("invalid argument")
    return options


if __name__ == '__main__':
    options = parse()
    password = getpass.getpass()

    # target zabbix FIXME
    if options.zabbix == 'hoge':
        zabbix = 'xxx.xxx.xxx.xxx'
        user = 'user'
        protocol = 'http or https'
    else:
        fail('no such zabbix server')

    # create instance
    api = ZabbixApi(zabbix, user, password, protocol)

    # Special function or Input file
    if options.file is None:
        if options.method == 'host_get_search':
            if options.host is None:
                fail(
                        'if execute {0}, --host option is needed'
                        .format(options.method))
            else:
                api.host_get_search(options.host)
        elif options.method == 'host_get_gid':
            if options.gid is None:
                fail(
                        'if execute {0}, --gid option is needed'
                        .format(options.method))
            else:
                api.host_get_gid(options.gid)
        elif options.method == 'maintenance_create':
            if options.host is None:
                fail(
                        'if execute {0}, --host option is needed'
                        .format(options.method))
            else:
                api.maintenance_create(options.host)
        elif options.method == 'map_create':
            if options.gid is None:
                fail(
                        'if execute {0}, --gid option is needed'
                        .format(options.method))
            else:
                api.map_create(options.gid)
        elif options.method == 'map_delete':
            if options.mapid is None:
                fail(
                        'if execute {0}, --mapid option is needed'
                        .format(options.method))
            else:
                api.map_delete(options.mapid)
        elif options.method == 'map_update':
            if options.mapid is None or options.host is None:
                fail(
                        'if execute {0}, --mapid and --host option is needed'
                        .format(options.method))
            else:
                api.map_update(options.mapid, options.host)
        elif options.method == 'item_get_search':
            if options.host is None or options.key is None:
                fail(
                        'if execute {0}, --host and --key option is needed'
                        .format(options.method))
            else:
                api.item_get_search(options.host, options.key)
        elif options.method == 'history_get':
            if options.itemid is None or options.time_from is None:
                fail(
                        'if execute {0}, --itemid and --time_from option is needed'
                        .format(options.method))
            else:
                dt = datetime.datetime.strptime(options.time_from, '%Y/%m/%d %H:%M:%S')
                epoch = time.mktime(dt.timetuple())
                api.history_get(options.itemid, epoch)
        else:
            fail('no such function')
    else:
        api.get_byfile(options.file, options.method)
