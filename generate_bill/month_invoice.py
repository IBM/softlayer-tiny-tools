#!/usr/bin/python3
# -*- coding: UTF-8 -*-
import SoftLayer
import getopt
import sys
import json
import logging
import re


domain_re = re.compile(r'[(](.*?)[)]', re.S) #最小匹配
start_date = ''
end_date = ''
invoice_type = []
supported_invoice_type = ("ALL", "NEW", "RECURRING", "ONE-TIME-CHARGE","CREDIT","REFUND","MANUAL_PAYMENT_CREDIT" )

logging.basicConfig(level=logging.INFO)

try:
    opts, args = getopt.getopt(
        sys.argv[1:],
        "hs:e:t:",
        ["start_date=", "end_date=", "type="],
        )
except getopt.GetoptError:
    print("%s -s <start_date> -e <end_date> -t <invoice-type>" % sys.argv[0])
    print("example:")
    print("         %s -s 03/01/2022 -e 03/30/2022" % sys.argv[0])
    print("")
    sys.exit(2)
for opt, arg in opts:
    if opt == '-h':
        print("%s -s <start_date> -e <end_date> -t <invoice-type>" % sys.argv[0])
        print("example:")
        print("         %s -s 03/01/2022 -e 03/30/2022 -t ALL" % sys.argv[0])
        print("")
        sys.exit()
    elif opt in ("-s", "--start_date"):
        start_date = arg
    elif opt in ("-e", "--end_date"):
        end_date = arg
    elif opt in ("-t", "--type"):
        if arg not in supported_invoice_type:
            print("unsupported invoice type")
            exit(1)
        invoice_type.append(arg)

class SL_Service():
    def __init__(self):
        self.client = SoftLayer.create_client_from_env()
        self.account_service = self.client['Account']
        self.billing_invoice_service = self.client['Billing_Invoice']
    
    # get all of invoices during a times 
    # format of start and end date is '01/01/2015'
    def get_invoices(self, startDate, endDate):
        logging.info("开始获取账单")
        #  items[laborAfterTaxAmount, laborFee, laborFeeTaxRate, laborTaxAmount, notes, oneTimeAfterTaxAmount, oneTimeFee, oneTimeFeeTaxRate, oneTimeTaxAmount, parentId, productItemId, recurringAfterTaxAmount, recurringFee, #recurringFeeTaxRate, recurringTaxAmount, resourceTableId, serviceProviderId, setupAfterTaxAmount
        #objectMask = "mask[id, createDate, typeCode, amount, invoiceTotalAmount, invoiceTotalOneTimeAmount, invoiceTotalOneTimeTaxAmount, invoiceTotalPreTaxAmount, invoiceTotalRecurringAmount, invoiceTotalRecurringTaxAmount, payment, startingBalance, endingBalance, items[billingItemId, categoryCode, createDate, description, domainName, hostName, hourlyRecurringFee, id, invoiceId, recurringFeeTaxRate, recurringTaxAmount, resourceTableId, serviceProviderId, setupAfterTaxAmount]]"
     #   objectMask = "mask[id, accountId, createDate, typeCode, amount, items[associatedInvoiceItemId, oneTimeFee, billingItemId, categoryCode, description, domainName, hostName, id, invoiceId, parentId, recurringFee, resourceTableId]]"
        objectMask = "mask[id, accountId, createDate, typeCode, amount, items[associatedInvoiceItemId, billingItemId, categoryCode, oneTimeFee, description, domainName, hostName, id, invoiceId, parentId, recurringFee, resourceTableId, notes]]"
  
        objectFilter = {
            'invoices': {
                'createDate': {
                    'operation': 'betweenDate',
                    'options': [
                        {
                        'name': 'startDate',
                        'value': [startDate]
                        },
                        {
                        'name': 'endDate',
                        'value': [endDate]
                        }
                    ]
                }
            }
        }

        if "ALL" not in invoice_type:
            objectFilter["invoices"]["typeCode"] =  {
                        'operation': 'in', 
                        'options': [{
                            'name': 'data',
                            'value': []
                        }]
                }
            for it in invoice_type:
                objectFilter["invoices"]['typeCode']['options'][0]['value'].append(it)

        # print(objectFilter)
        # print(objectMask)

        try:
            invoices = self.account_service.getInvoices(mask=objectMask, filter=objectFilter)
            if len(invoices) == 0:
                logging.warning("没找到账单")
                exit(0)
            return  invoices
        except SoftLayer.SoftLayerAPIError as e:
            raise e

    def generate_bill(self, invoices, deviceMap):
        logging.info("开始合并账单")
        resourceCollection = []
        for invoice in invoices:
        # bill = {
        #     "id" : invoice["id"],
        #     "accountId": invoice["accountId"],
        #     "amount": invoice["amount"],
        #     "createDate": invoice["createDate"],
        #     "items":   [],
        # }
            if invoice["typeCode"] == "ONE-TIME-CHARGE":
                for item in invoice["items"]:
                    # when device active from spare pool, one time charge will occur
                    if item["categoryCode"] == "one_time_charge" and "Activated from Spare Pool" in item["description"]:
                        fqdn = get_pqdn(item["description"])
                        resource = {
                            "type": item["categoryCode"],
                            "description": item["description"],
                            "fee": float(item["oneTimeFee"]),
                            "invoiceId": invoice["id"],
                            "invoiceCreateDate": invoice["createDate"],
                            "invoiceType": invoice["typeCode"],
                            "hostName": fqdn[0],
                            "domainName": fqdn[1]
                        }
                        if len(deviceMap.get(item.get("hostName", ""), [])) != 0:
                            resource["id"] = deviceMap[item["hostName"]][0]["id"]
                            resource["primaryIpAddress"] = deviceMap[item["hostName"]][0]["primaryIpAddress"]
                            resource["privateIpAddress"] = deviceMap[item["hostName"]][0]["privateIpAddress"]
                        resourceCollection.append(resource)
            else: 
                parentItem = {}
                for item in invoice["items"]:
                    if item["associatedInvoiceItemId"] == "":
                        id = str(item["id"])
                        parentItem[id] = item
                        parentItem[id]["subItems"]=[]
                
                for item in invoice["items"]:
                    if item["associatedInvoiceItemId"] != "":
                        id = str(item["associatedInvoiceItemId"])
                        if parentItem[id] != "":
                            parentItem[id]["subItems"].append(item)

                for item in parentItem.values():
                    resource = {
                        "type": item["categoryCode"],
                        "description": item["description"],
                        "fee": float(item["recurringFee"]),
                        "invoiceId": invoice["id"],
                        "invoiceCreateDate": invoice["createDate"],
                        "invoiceType": invoice["typeCode"],
                        }
                    if item.get("hostName", "") != "":
                        resource["hostName"] = item["hostName"]
                        resource["domainName"] = item["domainName"]

                    if len(deviceMap.get(item.get("hostName", ""), [])) != 0:
                        resource["id"] = deviceMap[item["hostName"]][0]["id"]
                        resource["primaryIpAddress"] = deviceMap[item["hostName"]][0]["primaryIpAddress"]
                        resource["privateIpAddress"] = deviceMap[item["hostName"]][0]["privateIpAddress"]

                    resource["items"] = [{
                            "categoryCode" : item["categoryCode"],
                            "description" : item["description"],
                            "recurringFee": item["recurringFee"],
                            }]

                    for subItem in item["subItems"]:
                        subResource = {
                            "categoryCode" : subItem["categoryCode"],
                            "description" : subItem["description"],
                            "recurringFee": subItem["recurringFee"],
                        }
                        resource["fee"] += float(subItem["recurringFee"])
                        resource["items"].append(subResource)
                    resource["fee"] = float("%.2f" % resource["fee"])
                    resourceCollection.append(resource)
        return resourceCollection

    def get_devices(self):
        objectMask = 'mask[id, hostname, daysInSparePool]'
        logging.info("开始获取设备列表")
        servers = self.account_service.getHardware()
        #print(json.dumps(servers, sort_keys=True, indent=2, separators=(',', ': ')))
        return servers

    
    def check_duplicate(self, devices):
        deviceMap = {}
        duplicate = False 
        for device in devices:
             # skip DEPLOY status device 3  and spare pool device 23
            if device.get("hardwareStatusId", 0) == 3 or \
                device.get("hardwareStatusId", 0) ==  23:
                continue
            if deviceMap.get(device["hostname"], "") == "":
                deviceMap[device["hostname"]] = [device]
            else:
                deviceMap[device["hostname"]].append(device)
                duplicate = True
        if duplicate:
            for deviceList in deviceMap.values():
                if len(deviceList) != 1: 
                    for device in deviceList: 
                        logging.error("重复的设备名称：%s, %s", device["hostname"], json.dumps(device, sort_keys=True, indent=2, separators=(',', ': ')))
            logging.error("请把设备的名称去重")
           # exit(1)
        return deviceMap

# from description "Activated from Spare Pool - (dal0932g1tbr107.test.com)\r\n* Pro-Rated Recurring Fee: $46.61" 
# extract fdns dal0932g1tbr107.test.com
def get_pqdn(description):
    fqdn_list =  re.findall(domain_re, description)
    if len(fqdn_list) == 0:
        return ["", ""]
    else:
        return fqdn_list[0].split(".", 1)


if __name__ == "__main__":
    # description = "Activated from Spare Pool - (dal0932g1tbr107.flyingbird.com)\r\n* Pro-Rated Recurring Fee: $46.61"
    # print(get_pqdn(description))
    service = SL_Service()
    devices = service.get_devices()
    deviceMap = service.check_duplicate(devices)
    invoices = service.get_invoices(start_date, end_date)
    # print(json.dumps(invoices, sort_keys=True, indent=2, separators=(',', ': ')))

    items = service.generate_bill(invoices, deviceMap)
    print(json.dumps(items, sort_keys=True, indent=2, separators=(',', ': ')))

    itemsTotal = 0.0
    billTotal =0.0
    for item in items:
        itemsTotal += float(item["fee"])
    for invoice in invoices:
        billTotal += float(invoice["amount"])
    logging.info("原始月账单总金额为：%.2f" % billTotal)
    logging.info("合并账单后金额为：%.2f" % itemsTotal)