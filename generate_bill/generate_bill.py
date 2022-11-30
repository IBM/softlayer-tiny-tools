#!/usr/bin/python3
# -*- coding: UTF-8 -*-
import SoftLayer
import getopt
import sys
start_date = ''
end_date = ''
output_format  = ''
invoice_type = []
supported_invoice_type = ("ALL", "NEW", "RECURRING", "ONE-TIME-CHARGE","CREDIT","REFUND","MANUAL_PAYMENT_CREDIT")

try:
    opts, args = getopt.getopt(
        sys.argv[1:],
        "hs:e:f:t:",
        ["start_date=", "end_date=", "output_format=", "type="],
        )
except getopt.GetoptError:
    print("%s -s <start_date> -e <end_date> -f <pdf_or_xls> -t <invoice-type>" % sys.argv[0])
    print("example:")
    print("         %s -s 03/01/2022 -e 03/30/2022 -f pdf" % sys.argv[0])
    print("")
    sys.exit(2)
for opt, arg in opts:
    if opt == '-h':
        print("%s -s <start_date> -e <end_date> -f <pdf_or_xls> -t <invoice-type>" % sys.argv[0])
        print("example:")
        print("         %s -s 03/01/2022 -e 03/30/2022 -f pdf -t ALL" % sys.argv[0])
        print("")
        sys.exit()
    elif opt in ("-s", "--start_date"):
        start_date = arg
    elif opt in ("-e", "--end_date"):
        end_date = arg
    elif opt in ("-f", "--output_format"):
        output_format = arg
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
        objectMask = "mask[id, createDate, typeCode]"
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
            print(invoices)
            return  invoices
        except SoftLayer.SoftLayerAPIError as e:
            raise e
           # raise ("Failed to get invoice list with error code %s and err msg %s " % (e.faultCode, e.faultString))


    def save_invoices(self, invoices, format):
        try:
            for invoice in invoices:
                invoice_id = invoice['id']
                if format.lower() == 'pdf':
                    binary_output = self.billing_invoice_service.getPdf(id= invoice_id)
                    with open('./{id}_{create_data}.pdf'.format(id=invoice['id'],create_data=invoice['createDate']), mode='wb') as f:
                        f.write(binary_output.data)
                else:
                    binary_output = self.billing_invoice_service.getExcel(id= invoice_id)
                    with open('./{id}_{create_data}.xls'.format(id=invoice['id'],create_data=invoice['createDate']), mode='wb') as f:
                        f.write(binary_output.data)
        except Exception as e: 
            raise e

if __name__ == "__main__":
    service = SL_Service()
    invoices = service.get_invoices(start_date, end_date)
    service.save_invoices(invoices, output_format)