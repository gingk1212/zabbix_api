#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
import json
import re
import urllib2
import datetime


class ZabbixApi(object):
    def __init__(self, host, user, password, protocol, fail=None):
        """Return Zabbix API instance

        :param host: Zabbix サーバの IP アドレス
        :param user: Zabbix API のアクセスユーザ
        :param password: Zabbix API のアクセスユーザパスワード
        :param logger: Logger
        :return:
        """
        # Setting for fail
        if fail is None:
            self.fail = self.fail_and_exit
        else:
            self.fail = fail

        # Setting for Zabbix API
        self.request_id = 1
        self.host = host
        self.protocol = protocol
        token = self.request(
                'user.login', {'user': user, 'password': password})
        if "result" not in token:
            self.fail('wrong password')
        self.auth_token = token['result']

    def request(self, method, params, auth_token=None):
        """Send request to Zabbix API

        :param method: Zabbix API のメソッド名
        :param params: Zabbix API のメソッドの引数
        :param auth_token: Zabbix API の認証トークン
        :return: JSON-RPC2.0 形式の応答
        """
        if hasattr(self, 'auth_token'):
            auth_token = self.auth_token
        headers = {"Content-Type": "application/json-rpc"}
        uri = "{0}://{1}/zabbix/api_jsonrpc.php"\
            .format(self.protocol, self.host)
        data = json.dumps({'jsonrpc': '2.0',
                           'method': method,
                           'params': params,
                           'auth': auth_token,
                           'id': self.request_id})
        request = urllib2.Request(uri, data, headers)
        self.request_id += 1
        try:
            response = json.loads(urllib2.urlopen(request).read())
        except urllib2.HTTPError as e:
            self.fail(e.read())
        except urllib2.URLError as e:
            self.fail(e.reason)

        self.api_check(response)
        return response

    def fail_and_exit(self, c=''):
        """Behavior when fail occurs

        :param response: API response
        :return:
        """
        print '[Fail] %s' % c
        sys.exit(1)

    def api_check(self, response):
        """Check api response

        :param response: API response
        :return:
        """
        if 'error' in response or len(response['result']) == 0:
            format = json.dumps(response, indent=4, ensure_ascii=False)
            print format
            self.fail("api error")

    def get_byfile(self, file, method):
        """Processing by input file

        :param file:
        :param method:
        :return:
        """
        # file check
        if not os.path.isfile(file):
            self.fail('file is not exists')

        # param and method
        f = open(file, 'r')
        param = json.load(f)
        f.close()

        # api request
        response = self.request(method, param)

        # output
        response_format = json.dumps(
                response['result'], indent=4, ensure_ascii=False)
        print response_format

    def host_get_search(self, host):
        """Get a host information

        :param host: Host
        :return:
        """
        method = 'host.get'
        param = {
            "output": ["host"],
            "selectInventory": ["model", "serialno_a"],
            "selectGroups": "extend",
            "search": {
                "host": host
            }
        }

        # api request
        response = self.request(method, param)

        # output
        response_format = json.dumps(
                response['result'], indent=4, ensure_ascii=False)
        print response_format

    def host_get_gid(self, gid):
        """Get hosts information in some group

        :param gid: Group ID
        :return:
        """
        method = 'host.get'
        param = {
            "output": ["host"],
            "sortfield": "host",
            "groupids": gid
        }

        # api request
        response = self.request(method, param)

        # output
        response_format = json.dumps(
                response['result'], indent=4, ensure_ascii=False)
        print response_format

    def maintenance_create(self, host):
        """Create maintenance for 5 hours about some groups

        :param host: Host
        :return:
        """
        # get host name and host group
        method = 'host.get'
        param = {
            "output": "extend",
            "selectGroups": "extend",
            "search": {
                "host": host
            }
        }
        response = self.request(method, param)

        # user check
        groupid = []
        for result in response['result']:
            print '[{0}]'.format(result['host'])
            for group in result['groups']:
                g_name = group['name'].encode('utf-8')
                if group['groupid'] in groupid:
                    continue
                else:
                    flag = raw_input(
                            '{0} really maintenance? (y/n): '.format(g_name))
                    if flag == 'y':
                        print 'add!'
                        groupid.append(group['groupid'])
                    else:
                        print 'not add!'

        # set param
        if len(groupid) == 0:
            self.fail('no hostgroup to maintenance')
        name = raw_input('maintenance name: ')
        if name == '':
            self.fail('you have to register a name')
        method = 'maintenance.create'
        param = {
            "name": name,
            "groupids": groupid,
            "timeperiods": [
                {
                    "timeperiod_type": 0,
                    "period": 18000
                }
            ]
        }

        # api request
        response = self.request(method, param)

        # output
        response_format = json.dumps(
                response['result'], indent=4, ensure_ascii=False)
        print response_format

    def map_create(self, gid):
        """Create map for one group

        :param gid: Group ID
        :return:
        """
        # get host
        method = 'host.get'
        param = {"output": ["host"], "groupids": gid}
        hosts = self.request(method, param)

        # set method and param
        name = raw_input('map name: ')
        if name == '':
            self.fail('you have to register a name')
        method = 'map.create'
        param = {
            "name": name,
            "width": 1200,
            "height": 1200,
            "label_type": 0,
            "label_location": 0,
            "highlight": 0,
            "expandproblem": 0,
            "expand_macros": 1,
            "grid_size": 40,
            "selements": [],
            "links": [],
            "urls": []
        }
        sid = 0
        x = 36
        y = 51
        for h in hosts["result"]:
            # host
            param["selements"].append(
                {
                    "elementid": h["hostid"],
                    "selementid": sid,
                    "elementtype": "0",     # host
                    "label": "{HOST.NAME}",
                    "iconid_off": "95",     # Rackmountable_1U_server_3D_(128)
                    "x": x,
                    "y": y
                }
            )
            sid += 1
            x += 160
            if x > 1000:
                x = 36
                y += 80

            # interface
            int_sid = sid
            int_method = 'item.get'
            int_param = {
                "output": ["name"],
                "hostids": h["hostid"],
                "search": {
                    "name": "ifOperStatus"
                }
            }
            interface = self.request(int_method, int_param)
            if len(interface["result"]) == 0:
                pass
            else:
                for i in interface["result"]:
                    int_name = re.split('\[|\]', i['name'])[1]
                    int_name = int_name.replace('FastEthernet', 'Fa')
                    int_name = int_name.replace('GigabitEthernet', 'Gi')
                    int_name = int_name.replace('Port-channel', 'Po')
                    param["selements"].append(
                        {
                            "elementid": int_sid,
                            "selementid": int_sid,
                            "elementtype": "4",     # image
                            "label": int_name,
                            "iconid_off": "62",     # Network_adapter_(24)
                            "x": x,
                            "y": y
                        }
                    )

                    # create link
                    param["links"].append(
                        {
                            "selementid1": sid - 1,
                            "selementid2": int_sid,
                            "color": "00CC00"
                        }
                    )
                    int_sid += 1
                    x += 160
                    if x > 1000:
                        x = 36
                        y += 80
                sid = int_sid

        # api request
        response = self.request(method, param)

        # output
        response_format = json.dumps(
                response['result'], indent=4, ensure_ascii=False)
        print response_format

    def map_delete(self, mapid):
        """Delete a map by mapid

        :param mapid: Map ID
        :return:
        """
        # get map name
        param = {"output": ["name"], "sysmapids": mapid}
        method = 'map.get'
        response = self.request(method, param)
        map_name = response['result'][0]['name'].encode('utf-8')

        # map delete
        flag = raw_input('Delete map [{0}] OK? (y/n): '.format(map_name))
        if flag == 'y':
            param = [mapid]
            method = 'map.delete'
            response = self.request(method, param)

            # output
            response_format = json.dumps(
                    response['result'], indent=4, ensure_ascii=False)
            print response_format
        else:
            self.fail('user cancel')

    def map_update(self, mapid, host, netNum=4):
        """Add a host with network adaptor to map

        :param mapid: Map ID
        :param host: Host name
        :param netNum: Number of network adaptors
        :return:
        """
        # get map's information
        param = {
            "output": ["name", "height"],
            "selectSelements": "extend",
            "selectLinks": "extend",
            "sysmapids": mapid
        }
        method = 'map.get'
        response = self.request(method, param)
        if len(response['result']) == 1:
            map_name = response['result'][0]['name'].encode('utf-8')
            map_height = int(response['result'][0]['height'])
            map_selements = response['result'][0]['selements']
            map_links = response['result'][0]['links']
        else:
            self.fail('number of map is not 1')

        # get host's elementid
        param = {"output": ["hostid"], "search": {"host": host}}
        method = 'host.get'
        response = self.request(method, param)
        if len(response['result']) == 1:
            elementid = response['result'][0]['hostid']
        else:
            self.fail('number of host is not 1')

        # map update
        flag = raw_input('Update map [{0}] OK? (y/n): '.format(map_name))
        if flag == 'y':
            method = 'map.update'
            param = {
                'sysmapid': mapid,
                'selements': map_selements,
                'links': map_links
            }

            # add host
            param["selements"].append(
                {
                    "selementid": "0",
                    "elementid": elementid,
                    "elementtype": "0",     # host
                    "label": "{HOST.NAME}",
                    "iconid_off": "95",     # Rackmountable_1U_server_3D_(128)
                    "x": '20',
                    "y": map_height - 100
                }
            )
            # add network adaptors
            selementid = 1
            for i in range(netNum):
                param["selements"].append(
                    {
                        "elementid": "0",
                        "selementid": selementid,
                        "elementtype": "4",     # image
                        "label": "ethernet",
                        "iconid_off": "62",     # Network_adapter_(24)
                        "x": 200,
                        "y": map_height - 100
                    }
                )
                # create link
                param["links"].append(
                    {
                        "selementid1": "0",
                        "selementid2": selementid,
                        "color": "00CC00"
                    }
                )
                selementid += 1

            # api request
            response = self.request(method, param)

            # output
            response_format = json.dumps(
                    response['result'], indent=4, ensure_ascii=False)
            print response_format
        else:
            self.fail('user cancel')

    def item_get_search(self, host, key):
        """Get a item information

        :param host: Host
        :param key: Item key
        :return:
        """
        method = "item.get"
        param = {
            "output": ["itemid", "key_", "name"],
            "host": host,
            "search": {
                "key_": key
            }
        }

        # api request
        response = self.request(method, param)

        # output
        response_format = json.dumps(
                response['result'], indent=4, ensure_ascii=False)
        print response_format

    def history_get(self, itemid, time_from):
        """Get a item history

        :param itemid: Item ID
        :param time_from: Return only values that have been received after or at the given time.
        :return:
        """
        method = "history.get"
        param = {
            "output": "extend",
            "itemids": itemid,
            "time_from": time_from
        }

        # api request
        response = self.request(method, param)

        # output
        for result in response['result']:
            epoch = float(result['clock'])
            result['clock'] = datetime.datetime.fromtimestamp(epoch).strftime('%Y/%m/%d %H:%M:%S')
            print result['clock'] + ',' + result['value']
