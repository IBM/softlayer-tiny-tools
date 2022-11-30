#!/usr/bin/python3
# -*- coding: UTF-8 -*-
import SoftLayer
import getopt
import sys
import json
from pprint import pprint

datacenter = ''
pool_id = ''

try:
    opts, args = getopt.getopt(
        sys.argv[1:],
        "hd:p:",
        ["datacenter=", "pool_id="],
        )
except getopt.GetoptError:
    print("%s -d <datacenter> -p <pool_id>" % sys.argv[0])
    print("example:")
    print("         %s -d dal09 -p 778891" % sys.argv[0])
    print("")
    sys.exit(2)
for opt, arg in opts:
    if opt == '-h':
        print("%s  -d dal09  -p 778891" % sys.argv[0])
        print("example:")
        print("         %s  -d dal09  -p 778891" % sys.argv[0])
        print("")
        sys.exit()
    elif opt in ("-p", "--pool_id"):
        pool_id = arg
    elif opt in ("-d", "--datacenter"):
        datacenter = arg

class SL_Service():
    def __init__(self):
        self.client = SoftLayer.create_client_from_env()
        debugger = SoftLayer.DebugTransport(self.client.transport)
        self.client.transport = debugger
        self.account_service = self.client['Account']
        self.poolService = self.client['SoftLayer_Network_Bandwidth_Version1_Allotment']
    
    # list all of devices by DC 
    def get_devices(self):
        try:
            objectFilterBms = {
                "hardware": {
                    "datacenter": {
                        "name": {
                            "operation": datacenter
                            }
                        }
                    },
                    # "bareMetalInstanceFlag": {
                    #     "operation": 1
                    # },
                    "virtualRackId": {
                        "operation": "not null"
                }
            }
            objectMask = 'mask[hostname, id, bareMetalInstanceFlag, bandwidthAllotmentDetail[bandwidthAllotmentId]， virtualRackId， virtualRackName]'
            devices = self.account_service.getHardware(mask=objectMask, filter=objectFilterBms)
            return devices 
        except SoftLayer.SoftLayerAPIError as e:
            print("Error. " % (e.faultCode, e.faultString))
            print("列出设备失败，请检查配置与权限。")
            raise e
    
    def debug(self):
        for call in self.client.transport.get_last_calls():
            pprint(self.client.transport.print_reproduceable(call))
    
    # add device to bandwidth_pool
    def add_pools(self, devices):
        try:
            target_devices = []
            for device  in devices: 
                if 'virtualRackId' in device.keys() and str(device['virtualRackId']) != pool_id:
                    target_devices.append(device)
            if len(target_devices) != 0: 
                result = self.poolService.requestVdrContentUpdates(target_devices, [], [], [], id=pool_id)
                if result: 
                    print("下列设备共 %d 台，将被添加到带宽池中" % len(devices))
                    print(json.dumps(target_devices, sort_keys=True, indent=2, separators=(',', ': ')))
                    print("所有设备共 %d 台，被添加到带宽池中" % len(devices))
                else: 
                    print("添加失败")
            else: 
                print(json.dumps(devices, sort_keys=True, indent=2, separators=(',', ': ')))
                print("以上所有设备 %d 台， 已经在带宽池中，不需要重复添加。" % len(devices))
        except SoftLayer.SoftLayerAPIError as e:
            print("Error. " % (e.faultCode, e.faultString))
            print("添加设备失败，请检查配置与权限。")
            raise e



if __name__ == "__main__":
    service = SL_Service()
    devices = service.get_devices()
    print(devices)
    service.add_pools(devices)