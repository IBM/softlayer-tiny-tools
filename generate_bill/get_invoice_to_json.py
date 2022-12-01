#!/usr/bin/python3
# -*- coding: UTF-8 -*-
import SoftLayer
import getopt
import sys
import json
import logging

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
    # format of start and end date is  '01/01/2015'
    def get_invoices(self, startDate, endDate):
        logging.info("开始获取账单")
        #  items[laborAfterTaxAmount, laborFee, laborFeeTaxRate, laborTaxAmount, notes, oneTimeAfterTaxAmount, oneTimeFee, oneTimeFeeTaxRate, oneTimeTaxAmount, parentId, productItemId, recurringAfterTaxAmount, recurringFee, #recurringFeeTaxRate, recurringTaxAmount, resourceTableId, serviceProviderId, setupAfterTaxAmount
        #objectMask = "mask[id, createDate, typeCode, amount, invoiceTotalAmount, invoiceTotalOneTimeAmount, invoiceTotalOneTimeTaxAmount, invoiceTotalPreTaxAmount, invoiceTotalRecurringAmount, invoiceTotalRecurringTaxAmount, payment, startingBalance, endingBalance, items[billingItemId, categoryCode, createDate, description, domainName, hostName, hourlyRecurringFee, id, invoiceId, recurringFeeTaxRate, recurringTaxAmount, resourceTableId, serviceProviderId, setupAfterTaxAmount]]"
        objectMask = "mask[id, accountId, createDate, typeCode, amount, items[associatedInvoiceItemId, notes, billingItemId, categoryCode, oneTimeFee, description, domainName, hostName, id, invoiceId, parentId, recurringFee, resourceTableId]]"
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

        try:
            invoices = self.account_service.getInvoices(mask=objectMask, filter=objectFilter)
            if len(invoices) == 0:
                logging.warning("没找到账单")
                exit(0)
       #     print(invoices)
            return  invoices
        except SoftLayer.SoftLayerAPIError as e:
            raise e
           # raise ("Failed to get invoice list with error code %s and err msg %s " % (e.faultCode, e.faultString))

    def generate_bill(self, invoices, deviceMap):
        logging.info("开始合并账单")
        invoice = invoices[0]
        bill = {
            "id" : invoice["id"],
            "accountId": invoice["accountId"],
            "amount": invoice["amount"],
            "createDate": invoice["createDate"],
            "items":   [],
        }
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
                "domainName": item["domainName"],
                "oneTimeFee": item["oneTimeFee"]
                }
            if item.get("hostName", "") != "":
                resource["hostName"] = item["hostName"]

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
            bill["items"].append(resource)
        return bill

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
        
            
if __name__ == "__main__":
    service = SL_Service()
    # devices = service.get_devices()
    # deviceMap = service.check_duplicate(devices)
    invoices = service.get_invoices(start_date, end_date)
    print(json.dumps(invoices, sort_keys=True, indent=2, separators=(',', ': ')))
    # bill = service.generate_bill(invoices, deviceMap)
    # print(json.dumps(bill, sort_keys=True, indent=2, separators=(',', ': ')))

    # total = 0.0
    # for item in bill["items"]:
    #     total += item["fee"]
    # logging.info("原始账单金额为：%s" % bill["amount"])
    # logging.info("合并账单后金额为：%.2f" % total)