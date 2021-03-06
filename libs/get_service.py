#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
@Author: reber
@Mail: reber0ask@qq.com
@Date: 2019-08-24 17:55:54
@LastEditTime: 2020-01-18 02:27:28
'''
import time
from concurrent.futures import ThreadPoolExecutor
from threading import Lock
from nmap import nmap

try:
    from config import log_level
    from config import log_file_path
    from libs.mylog import MyLog
except ModuleNotFoundError:
    from Rpscan.config import log_level
    from Rpscan.config import log_file_path
    from Rpscan.libs.mylog import MyLog

lock = Lock()
log_file = log_file_path.joinpath("{}.log".format(
    time.strftime("%Y-%m-%d", time.localtime())))
logger = MyLog(loglevel=log_level, logger_name='get service', logfile=log_file)


class NmapGetPortService(object):
    """获取端口运行的服务"""

    def __init__(self, ip_port_dict, thread_num=10):
        super(NmapGetPortService, self).__init__()
        self.ip_port_dict = ip_port_dict
        self.thread_num = thread_num
        self.port_service_list = dict()
        self.init_thread()
        logger.info("[*] Get the service of the port...")

    def init_thread(self):
        '''设定线程数量'''
        if len(self.ip_port_dict) < self.thread_num:
            self.thread_num = len(self.ip_port_dict)

    def nmap_get_service(self, ip_port):
        '''nmap 获取端口的 service'''
        ip, port = ip_port
        try:
            nm_scan = nmap.PortScanner()
            args = '-p T:'+str(port)+' -Pn -sT -sV -n'
            # args = '--allports -Pn -sT -sV -n --version-all --min-parallelism 100'
            nm_scan.scan(ip, arguments=args)
            # logger.info(nm_scan.command_line())

            self.port_service_list[ip] = list()
            port_result = nm_scan[ip]['tcp']
            for port in port_result.keys():
                state = port_result[port]['state']
                name = port_result[port]['name']
                product = port_result[port]['product']
                version = port_result[port]['version']

                result = "{:<17}{:<7}{:<10}{:<16}{:<32}{}".format(
                    ip, port, state, name, product, version)
                lock.acquire()
                logger.info(result)
                lock.release()

                service_result = dict()
                service_result['port'] = port
                service_result['state'] = state
                service_result['name'] = name
                service_result['product'] = product
                service_result['version'] = version
                self.port_service_list[ip].append(service_result)
        except Exception as e:
            # logger.error(e)
            pass

    def run(self):
        try:
            with ThreadPoolExecutor(max_workers=self.thread_num) as executor:
                for ip in self.ip_port_dict.keys():
                    ports = map(str, self.ip_port_dict[ip])
                    ports = ",".join(ports)
                    executor.submit(self.nmap_get_service, (ip, ports))
        except KeyboardInterrupt:
            logger.error("User aborted.")
            exit(0)

        return self.port_service_list
