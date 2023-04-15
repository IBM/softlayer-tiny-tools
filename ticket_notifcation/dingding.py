import requests
import json
import logging
import time
import hmac
import hashlib
import base64
import urllib.parse

def get_sign(secret):
    timestamp = str(round(time.time() * 1000))
    secret_enc = secret.encode('utf-8')
    string_to_sign = '{}\n{}'.format(timestamp, secret)
    string_to_sign_enc = string_to_sign.encode('utf-8')
    hmac_code = hmac.new(secret_enc, string_to_sign_enc, digestmod=hashlib.sha256).digest()
    sign = urllib.parse.quote_plus(base64.b64encode(hmac_code))
    return timestamp, sign

def push_message(secret, endpoint, title, priority, cs_ticket_Id, lastDate, entry, mail_ticket_link, entry_translate):
    logging.info("ding ding send msg for ticket {}".format(cs_ticket_Id))
    post_headers = {'Content-Type': 'application/json'}
    data = {
        "msgtype": "actionCard",
        "actionCard": {
            "title": title, 
            "text":  "### 工单号: {}\n".format(cs_ticket_Id) +
            "> ### 优先级: {}\n".format(priority) +
            "> ### 工单跳转: [{}]({}) \n".format(cs_ticket_Id, mail_ticket_link) +
            "> ### 更新日期: {}\n\n".format(lastDate) +
            "> ### 最新更新: \n\n\n" +
            "> #### {}\n\n\n".format(entry) +
            "> ### 译文: \n\n\n" +
            "> ####  {}\n\n\n".format(entry_translate) +
            "> ### 翻译由 [Ibm watson language translator]({}) 提供 ".format("https://www.ibm.com/cloud/watson-language-translator")
            }
    }
    timestamp, sign = get_sign(secret)
    endpoint = endpoint+ "&timestamp={}&sign={}".format(timestamp, sign)
    response = requests.post(endpoint, data=json.dumps(data), headers=post_headers)
    logging.info(response.status_code)
    logging.info(response.text)
    
   
if __name__ == "__main__":
    title = 'HPVS gen2 for VPC connect VPE timeout'
    priority = 4
    ticketId =  'CS3245985'
    lastDate = '2023-02-22T00:59:10-06:00'
    entry = 'Can you provide the info on below mentioned points '
    translated_entry = "这个是一个测试项目"
    endpoint = ""
    ticket_url = ""
    push_message(endpoint, ticket_url, title, ticketId, priority, lastDate, entry, translated_entry)
    

