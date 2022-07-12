from __future__ import (absolute_import, division, print_function)

import base64
import json
import logging
from urllib import request, parse

from ansible.errors import AnsibleParserError
from ansible.module_utils.common.text.converters import to_text, to_native
from ansible.plugins.inventory import BaseInventoryPlugin

__metaclass__ = type

DOCUMENTATION = r'''
    name: cmdb_host_list
    version_added: "2.12"
    short_description: 解析远端CMDB主机信息
    description:
        - 解析远端CMDB的主机清单信息
    options:
        username:
            description: 用户名
            required: false
            type: str
        password:
            description: 密码
            required: false
            type: str
        url:
            description: 地址
            required: false
            type: str
'''

EXAMPLES = r'''
---
plugin: cmdb_host_list
username: admin
password: admin
    # 正常通过ansible-inventory查看主机清单信息
    ansible-inventory -i cmdb.yaml --list
    # 调试通过ansible-inventory查看主机清单信息
    ansible-inventory -vvv -i cmdb.yaml --list
'''


class InventoryModule(BaseInventoryPlugin):

    NAME = 'cmdb_host_list'  # used internally by Ansible, it should match the file name but not required

    def verify_file(self, path):
        # return true/false if this is possibly a valid file for this plugin to consume
        valid = True
        try:
            if to_text(path, errors="").startswith("cmdb:"):
                valid = True
        except Exception as e:
            pass
        return valid

    def parse(self, inventory, loader, path, cache=True):
        # call base method to ensure properties are available for use with other helper methods
        super(InventoryModule, self).parse(inventory, loader, path)
        # 设置配置参数
        self.set_options()
        # TODO 添加插件以及特性
        try:
            # HTTP请求获取需要的结果 TODO 添加安全认证逻辑,添加相关参数,定义主机分组的格式信息
            # 发送请求
            # url = "http://192.168.3.36:8899/inventories/1"
            config = self._read_config_data(path)

            url = self.get_option("url")
            username = self.get_option("username")
            password = self.get_option("password")
            auth="Basic "+base64.b64encode(("%s:%s" % (username, password)).encode()).decode()
            req = request.Request(url, headers={"Authorization":auth}, method="GET")
            response = request.urlopen(req)
            text = response.read()
            host_dict = json.loads(text.decode('utf-8'))
            #logging.debug(str.format("username:{}, password:{}", self.get_option("username"), self.get_options("password")))
            #res_body = '{"group1":{"hosts":[{"ip":"192.168.3.101","port":22,"ansible_ssh_pass":"admin"},{"ip":"192.168.3.102","port":22,"ansible_ssh_pass":"admin"}]}}'
            for group in host_dict["groups"]:
                # 初始化group
                self.inventory.add_group(group['name'])
                for host in group['hosts']:
                    ansible_host = host.pop('ip')
                    ansible_port = host.pop('port')
                    self.inventory.add_host(ansible_host, group=group['name'], port=ansible_port)
                    # 给host添加其他参数,如: ansible_ssh_pass
                    for k, v in host.items():
                        if k.startswith("ansible_"):
                            self.inventory.set_variable(ansible_host, k, v)
        except Exception as e:
            # INFO 如果发生异常需要抛出解析异常
            raise AnsibleParserError('Invalid data from string, could not parse: %s' % to_native(repr(e)))


if __name__ == '__main__':
    try:
        url = "http://192.168.3.124:8899/inventories/awx"
        username = "awx"
        password = "awx"
        auth="Basic "+base64.b64encode(("%s:%s" % (username, password)).encode()).decode()
        req = request.Request(url, headers={"Authorization":auth}, method="GET")
        response = request.urlopen(req)
        text = response.read()
        host_dict = json.loads(text.decode('utf-8'))
        for group in host_dict["groups"]:
            # 初始化group
            print(group['name'])
            for host in group['hosts']:
                ansible_host = host.pop('ip')
                ansible_port = host.pop('port')
                for k, v in host.items():
                    if k.startswith("ansible_"):
                        print(k, v)
    except Exception as e:
        raise AnsibleParserError('Invalid data from string, could not parse: %s' % to_native(e))