#!/usr/bin/python3
# -*- coding: UTF-8 -*-
import SoftLayer
import logging
import pprint
from SoftLayer import DNSManager

logging.basicConfig(level=logging.INFO)

class SL_Service():
    def __init__(self):
        self.client = SoftLayer.create_client_from_env()
        self.dns_manager = DNSManager(self.client)
    
    def create_dns_reverse_record(self, ipadress, domain, ttl):
        ptr = self.dns_manager.create_record_ptr(ipadress, domain, ttl)
        return ptr

            
if __name__ == "__main__":
    service = SL_Service()
    ptr = service.create_dns_reverse_record("1.1.1.1", "test.txe", 180)
    pprint.pprint(ptr)

# import yaml

# with open('clone_vm_params.yaml', 'r') as f:
#     params = yaml.safe_load(f)

# print(params['vm-clone-params']['vm-name']) # 输出: spark_test
