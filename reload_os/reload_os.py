#!/usr/bin/python3
# -*- coding: UTF-8 -*-
import SoftLayer
import getopt
import sys


address_list =''
api_key = ''
username = ''
customProvisionScriptUri = 'http://10.173.199.82/scripts/init_os_for_ls.sh'

def output_help_message():
    print("%s -i <ipaddress-list>  -k <api_key> -u <username>" % sys.argv[0])
    print("example:")
    print("           %s -p \"10.1.1.1 10.1.1.2\"  -k my-api-key -u test" % sys.argv[0])
    print("")

try:
    opts, args = getopt.getopt(
        sys.argv[1:],
        "hi:p:k:u:",
        ["ip_addresses", "api_key=", "username=",],
        )
except getopt.GetoptError:
    output_help_message()
    sys.exit(2)
    
for opt, arg in opts:
    if opt == '-h':
        output_help_message()
        sys.exit()
    elif opt in ("-i", "--ip_addresses"):
        address_list = arg
    elif opt in ("-k", "--api_key"):
        api_key = arg
    elif opt in ("-u", "--username"):
        username = arg

class SL_Service():
    def __init__(self, username, api_key):
        self.client = SoftLayer.create_client_from_env(username, api_key)
        self.hardwareService = self.client['SoftLayer_Hardware_Server']
        self.serversToReload = {}
        self.ipsToReload = address_list.split(" ")
        print(self.ipsToReload)
    
    def find_servers(self):
        # the list of servers to reload
        """
        We are looking for the server with the specified IP addresses
        and the price for the new OS to load
        """
        try:
            for ipToReload in self.ipsToReload:
                server = self.hardwareService.findByIpAddress(ipToReload)
                if server and server['id']:
                    self.serversToReload[ipToReload] = {}
                    self.serversToReload[ipToReload]['id'] = server['id']
                else:
                    print("can't find device: %s, skip it" % (ipToReload) )
            print(self.serversToReload)
            return
        except SoftLayer.SoftLayerAPIError as e:
            print("Unable to find the bare metal servers: \nfaultCode= %s, \nfaultString= %s"
                % (e.faultCode, e.faultString))
            exit(1)

    def reload_os(self):
        config = {
            "upgradeHardDriveFirmware": 0,
            "upgradeBios": 0,
            "hardDrives": [
                {
                    "complexType": "SoftLayer_Hardware_Component_HardDrive",
                    "partitions": [
                        { "name": "/boot", "minimumSize": ".5"},
                        { "name": "/swap", "minimumSize": "8"},
                        { "name": "/", "minimumSize": "1", "grow": "1"},
                    ]
                }
            ],
            "lvmFlag": 0,
        }
        if customProvisionScriptUri != '':
            config['customProvisionScriptUri'] = customProvisionScriptUri

        try:
            for ipToReload in self.ipsToReload:
                reload = self.hardwareService.reloadOperatingSystem('FORCE', config, id=self.serversToReload[ipToReload]['id'])
                print(reload)
        except SoftLayer.SoftLayerAPIError as e:
            print("Unable to reload the bare metal servers: \nfaultCode= %s, \nfaultString= %s"
                % (e.faultCode, e.faultString))
            exit(1)
     

if __name__ == "__main__":
    service = SL_Service(username, api_key)
    service.find_servers()
    service.reload_os()