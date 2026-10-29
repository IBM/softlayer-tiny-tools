#!/usr/bin/python3
# -*- coding: UTF-8 -*-
import SoftLayer
import sys
from pprint import pprint as pp
import getopt

# https://sldn.softlayer.com/python/order_quote_advanced/
# export $SL_USER
# export $SL_APIKEY

quote_id = 0
quantity =0 
provisionScripts= ''
prefix= ''
index = 0
suffix = ''
domain = ''
private_vlan = None
public_vlan = None
private_subnet = None
public_subnet = None
extendedHardwareTesting = False
verify = False
list_subnets = None


try:
    opts, args = getopt.getopt(
        sys.argv[1:],
        "",
        ["quote_id=", "ext_test=", "quantity=", "provisionScripts=", "prefix=", "index=", "suffix=", "domain=", "private_vlan=", "public_vlan=", "private_subnet=", "public_subnet=", "verify=", "list_subnets="],
        )
except getopt.GetoptError:
    print("example:")
    print('         %s --quote_id=2987038 --ext_test=true --quantity=2 --provisionScripts="https://10.1.1.1/init.sh" --prefix="s" --index=192 --suffix="-dal9" --domain="test.com" --private_vlan=3250707 [--private_subnet=1234567]' % sys.argv[0])
    print("")
    sys.exit(2)
for opt, arg in opts:
    if opt == '-h':
        print("example:")
        print('         %s --quote_id=2987038 --ext_test=true  --quantity=2 --provisionScripts="https://10.1.1.1/init.sh" --prefix="s" --index=192 --suffix="-dal9" --domain="test.com" --private_vlan=3250707 [--private_subnet=1234567]' % sys.argv[0])
        print("")
        sys.exit(2)
    elif opt in ("--quote_id"):
        quote_id = int(arg)
    elif opt in ("--quantity"):
        quantity = int(arg)
    elif opt in ("--provisionScripts"):
        provisionScripts = arg
    elif opt in ("--prefix"):
        prefix = arg
    elif opt in ("--index"):
        index = int(arg)
    elif opt in ("--suffix"):
        suffix = arg
    elif opt in ("--domain"):
        domain = arg
    elif opt in ("--private_vlan"):
        private_vlan = int(arg)
    elif opt in ("--public_vlan"):
        public_vlan = int(arg)
    elif opt in ("--private_subnet"):
        private_subnet = int(arg)
    elif opt in ("--public_subnet"):
        public_subnet = int(arg)
    elif opt in ("--ext_test="):
        if arg == "true":
            extendedHardwareTesting= True
        else: 
            extendedHardwareTesting= False
    elif opt in ("--verify"):
        verify = arg == "true"
    elif opt in ("--list_subnets"):
        list_subnets = int(arg)

class example():

    def __init__(self):
        self.client = SoftLayer.create_client_from_env()
        debugger = SoftLayer.DebugTransport(self.client.transport)
        self.client.transport = debugger

    def orderQuote(self, quote_id, quantity, extendedHardwareTesting=True, provisionScripts="", prefix="", index=0, suffix="", domain="", private_vlan = None, public_vlan = None, private_subnet = None, public_subnet = None, verify = False):
        # If you have more than 1 server in the quote, you will need to append
        # a copy of this for each VSI, with hostnames changed as needed

        quote = self.client['Billing_Order_Quote']
        quote_container = quote.getRecalculatedOrderContainer(id=quote_id)
        # print("================= QUOTE CONTAINER =================")
        # pp(quote_container)
        # print("================= QUOTE CONTAINER =================")

        container = quote_container
        container['complexType'] = "SoftLayer_Container_Product_Order_Hardware_Server"
        container['quantity'] = quantity
        container['hardware'] = []
        if provisionScripts: 
            container['provisionScripts'] = []
        if extendedHardwareTesting: 
            container['extendedHardwareTesting'] = True
        for x in range(quantity): 
            baremetal = {
                'hostname': prefix + str(index+x) + suffix,
                'domain': domain
            }

            if private_vlan:
                vlan = {"id": int(private_vlan)}
                if private_subnet:
                    vlan["primarySubnet"] = {"id": int(private_subnet)}
                baremetal.update({
                    "primaryBackendNetworkComponent": {"networkVlan": vlan}})
            if public_vlan:
                vlan = {"id": int(public_vlan)}
                if public_subnet:
                    vlan["primarySubnet"] = {"id": int(public_subnet)}
                baremetal.update({
                    'primaryNetworkComponent': {"networkVlan": vlan}})
                
            container['hardware'].append(baremetal)
            if provisionScripts: 
                container['provisionScripts'].append(provisionScripts)          
        
        pp(container)
        if verify:
            self.client['Billing_Order_Quote'].verifyOrder(container, id=quote_id)
            print("================= 校验通过, 未实际下单 =================")
            return
        result = self.client['Billing_Order_Quote'].placeOrder(container, id=quote_id)
        print("================= RECEIPT CONTAINER =================")
        pp(result)
        print("================= RECEIPT CONTAINER =================")

    def listQuotes(self):
        # https://softlayer.github.io/reference/datatypes/SoftLayer_Billing_Order_Quote/
        mask = "mask[order[id, orderTotalAmount, orderTopLevelItems[id, description]], ordersFromQuoteCount]"
        quotes = self.client['SoftLayer_Account'].getActiveQuotes(mask=mask)
        print("ID, createDate, name, status, order count, description")
        for quote in quotes:
            print("{}, {}, {}, {}, {}, {}".format(
                quote['id'], quote['createDate'], quote['name'], quote['status'], 
                quote['ordersFromQuoteCount'], quote['order']['orderTopLevelItems'][0]['description'])
            )

    def listLocations(self):
        locations = self.client['SoftLayer_Location'].getDatacenters()
        pp(locations)

    def listLocationsForQuote(self, quoteId):
        mask="mask[id, order[id, orderTopLevelItems[id, package[id, availableLocations[location[longName, id]]]]]]"
        locations = self.client['Billing_Order_Quote'].getObject(id=quoteId, mask=mask)

        package_id = locations['order']['orderTopLevelItems'][0]['package']['id']
        print("Package {} is available in the following locations...".format(package_id))
        for dc in locations['order']['orderTopLevelItems'][0]['package']['availableLocations']:
            print("{}, id={}".format(dc['location']['longName'], dc['location']['id']))

    def listSshKeys(self):
        keys = self.client['SoftLayer_Account'].getSshKeys()
        pp(keys)

    def listImageTemplates(self):
        mask = "mask[id,name,note]"
        imageTemplates = self.client['SoftLayer_Account'].getPrivateBlockDeviceTemplateGroups(mask=mask)
        print("ID - Name - Note")
        for template in imageTemplates:
            try:
                print("%s - %s - %s" % (template['id'], template['name'], template['note']))
            except KeyError:
                print("%s - %s - %s" % (template['id'], template['name'], 'None'))

    def listVlansInLocation(self, location_id):
        mask = "mask[id,vlanNumber,primaryRouter[hostname,datacenter[id,name]]]"
        objfilter2 = { "networkVlans":    
                        {"primaryRouter": 
                            {"datacenter": { "id" : {"operation":location_id} } }
                        }
                    }
        subnets = self.client['SoftLayer_Account'].getNetworkVlans(mask=mask,filter=objfilter2)
        for subnet in subnets:
            print("%s, %s, %s" % ( subnet['id'], subnet['vlanNumber'], subnet['primaryRouter']['hostname']))

    def listSubnetsOnVlan(self, vlan_id):
        mask = "mask[id,vlanNumber,networkSpace,primaryRouter[hostname],subnets[id,networkIdentifier,cidr,subnetType,usableIpAddressCount]]"
        vlan = self.client['SoftLayer_Network_Vlan'].getObject(id=vlan_id, mask=mask)
        print("VLAN ID: %s, VLAN 号: %s, 类型: %s, 路由: %s" % (
            vlan['id'], vlan['vlanNumber'], vlan.get('networkSpace', ''), vlan.get('primaryRouter', {}).get('hostname', '')))
        print("子网 ID, 网段, 类型, 可用 IP 数")
        for subnet in vlan.get('subnets', []):
            print("%s, %s/%s, %s, %s" % (
                subnet['id'], subnet['networkIdentifier'], subnet['cidr'],
                subnet['subnetType'], subnet.get('usableIpAddressCount', '')))
        print("")
        print("下单时 --private_subnet / --public_subnet 只能使用 PRIMARY 或 ADDITIONAL_PRIMARY 类型的子网")

    def debug(self):
        for call in self.client.transport.get_last_calls():
            print(self.client.transport.print_reproduceable(call))
    
    def confirm(self, quote_id, quantity, extendedHardwareTesting, provisionScripts="", prefix="", index=0, suffix="", domain="", private_vlan = None, public_vlan = None, private_subnet = None, public_subnet = None, verify = False):
        print("")
        print("请核对下列创建订单信息：")
        if private_vlan:
            print("     私有vlan ID: %d" % private_vlan)
        else:
            print("     私有vlan ID: 系统自动分配")
        if private_subnet:
            print("     私有子网 ID: %d" % private_subnet)
        if public_vlan:
            print("     公有vlan ID: %d" % public_vlan)
        else:
            print("     公有vlan ID: 系统自动分配")
        if public_subnet:
            print("     公有子网 ID: %d" % public_subnet)
        if provisionScripts:
            print("     初始化脚本为: %s" % provisionScripts)
        if extendedHardwareTesting: 
            print("     扩展测试: 开启")
        else:
            print("     扩展测试: 关闭")
        print("     折扣 ID 为: %d" % quote_id )
        print("     %d 台设备将被创建, 设备名称为:" % quantity)
        for x in range(quantity): 
            print("         " + prefix + str(index+x) + suffix + "." + domain)
        print("")
        if verify:
            print("     模式: 仅校验订单 (verifyOrder), 不会实际下单")
            print("")
        confirm = input("是否继续(Y/N)")
        if confirm.lower() == "y":
            if verify:
                print("开始校验订单.......")
            else:
                print("开始下单, 请不要中断脚本.......")
        else:
            print("退出....")
            exit(2)

    
if __name__ == "__main__":
    #quote_id = 2987038
    main = example()
    if list_subnets:
        main.listSubnetsOnVlan(list_subnets)
        sys.exit(0)
    # main.listImageTemplates()
    # main.listQuotes()
    # main.listLocationsForQuote(quote_id)
    # main.listLocations()
    # dal13 = 1854895
    # ams03 = 814994
    # dal09 = 449494
    # # main.listSshKeys()
    # # main.listVlansInLocation(dal13)
    # backend_vlan = 2068355 #951, bcr01a.dal13
    # front_vlan = 2068353 # 907, fcr01a.dal13
    main.confirm(quote_id=quote_id, extendedHardwareTesting=extendedHardwareTesting, quantity=quantity, provisionScripts=provisionScripts, prefix=prefix, index=index, suffix=suffix, domain=domain, private_vlan=private_vlan, public_vlan=public_vlan, private_subnet=private_subnet, public_subnet=public_subnet, verify=verify)
    main.orderQuote(quote_id=quote_id, extendedHardwareTesting=extendedHardwareTesting, quantity=quantity, provisionScripts=provisionScripts, prefix=prefix, index=index, suffix=suffix, domain=domain, private_vlan=private_vlan, public_vlan=public_vlan, private_subnet=private_subnet, public_subnet=public_subnet, verify=verify)
    # main.debug()