#!/usr/bin/python3
# -*- coding: UTF-8 -*-
import requests
import json
import logging

def push_message(endpoint, title, priority, cs_ticket_Id, lastDate, entry, mail_ticket_link, entry_translate):
    logging.info("ding ding send msg for ticket {}".format(cs_ticket_Id))
    post_headers = {'Content-Type': 'application/json'}
    data = "题目:  {} ".format(title) + r"\n\n" + \
           "优先级:  {} ".format(priority) + r"\n\n" + \
           "工单号:  {} ".format(cs_ticket_Id) + r"\n\n" + \
           "工单跳转:  {} ".format(mail_ticket_link) + r"\n\n" + \
           "更新日期:  {} ".format(lastDate) + r"\n\n" + \
           "最新更新内容:  {} ".format(entry) + r"\n\n" + \
           "译文:  {} ".format(entry_translate) + r"\n\n" + \
           "翻译由 Ibm watson language translator 提供" + r"\n\n" 
    message = {
        "text": data
    }

    response = requests.post(endpoint, data=json.dumps(message), headers=post_headers)
    logging.info(response.status_code)
    logging.info(response.text)
    
   
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    title = 'HPVS gen2 for VPC connect VPE timeout'
    priority = 4
    ticketId =  'CS3245985'
    lastDate = '2023-02-22T00:59:10-06:00'
    entry = 'Can you provide the info on below mentioned points '
    translated_entry = "这个是一个测试项目"
    endpoint = ""
    ticket_url = ""
    push_message(endpoint, ticket_url, title, ticketId, priority, lastDate, entry, translated_entry)
    

    # # 指定端点URL
    # endpoint = ''
    # service = Lark()
    # service.build_ticket_message_body(title, priority, ticketId, lastDate, entry, url)
    # service.send(endpoint)


