#!/usr/bin/python3
# -*- coding: UTF-8 -*-
import softlayer_service
import feishu
import translate
import logging
import gmail
import re
import yaml
import dingding
import mind
import time 

from urllib.parse import parse_qs

def load_yaml_config(filename):
    with open(filename, 'r') as f:
        config = yaml.safe_load(f)
    return config

def build_config_map(config):
    account_map = {}
    for user in config["ticket-notification-users"]:
        account_map[user["account-id"]] = user
    return account_map

def main():
    config = load_yaml_config("config.yaml")
    
    while True:
        try:
            # set log level 
            logging.basicConfig(level=logging.INFO)
            account_map = build_config_map(config)
            translate_service = translate.Translate(config["translate-api-key"], config["translate-service-endpoint"])

            token_path = "token.json"
            credentials_path = 'credentials.json'
            links = gmail.get_mail_links(token_path, credentials_path)
            parsed_mail_tickets = []
            for link in links: 
                url = gmail.parse_url(link)
                if url["Netloc"] == "cloud.ibm.com" and "/cases/manage" in url["Path"]:
                    match = re.search(r'\/(\w+)$', url["Path"])
                    service_now_id= ""
                    if match:
                        service_now_id = match.group(1)

                    query_params = parse_qs(url["Query"])
                    account_id = query_params.get('accountId', [''])[0]
                    logging.info("account ID: {}".format(account_id))
                    logging.info("service_now_id: {}".format(service_now_id))
                    parsed_mail_tickets.append({"account_id" :account_id, "service_now_id": service_now_id, "link": link})
            
            logging.debug(parsed_mail_tickets)
            
            for mail_ticket in parsed_mail_tickets:
                if mail_ticket["account_id"] not in account_map:
                    logging.info("can not find account id ,{},in config yaml fail.".format[mail_ticket["account_id"]])
                    continue
            
                config_accounts_map = account_map[mail_ticket["account_id"]]

                # list all of opened ticket from sl
                account_short_id = config_accounts_map["account"]
                print(config_accounts_map["apikey"])
                sl_service = softlayer_service.SL_Service(account_short_id, config_accounts_map["apikey-username"], config_accounts_map["apikey"])
                sl_tickets = sl_service.get_tickets()
                logging.info("find opened tickets {} for account {}".format(len(sl_tickets), account_short_id))

                for sl_ticket in sl_tickets:
                    cs_ticket_Id = sl_ticket["serviceProviderResourceId"]
                    if cs_ticket_Id == mail_ticket["service_now_id"]:
                        title = sl_ticket["title"]
                        priority = sl_ticket["priority"]
                        if priority <= config_accounts_map["priority"]:
                            lastDate = sl_ticket["lastUpdate"]["createDate"]
                            entry = sl_ticket["lastUpdate"]["entry"]
                            logging.info("call translate function for ticket {}".format(cs_ticket_Id))
                            entry_translate = translate_service.translateToChinese(entry)
                            entry_translate = entry_translate["translations"][0]["translation"]
                            call_oa(config_accounts_map["oa"], title, priority, cs_ticket_Id, lastDate, entry, mail_ticket["link"], entry_translate)
                        else:
                            logging.info("ticket: {} priority {} less than set priority {}, skip notification".format(cs_ticket_Id, priority, config_accounts_map["priority"]))
                        break
        except Exception as e:
            logging.error(e)
        interval = config["mail-check-interval"]
        logging.info("sleep {}...".format(interval))
        time.sleep(interval)

def call_oa(oa, title, priority, cs_ticket_Id, lastDate, entry, mail_ticket_link, entry_translate):
    oa_type = oa["oa-type"]
    if oa_type == "feishu":
        logging.info("call feishu OI to notification for ticket: {}".format(cs_ticket_Id))
        feishu_service = feishu.Lark()
        feishu_service.build_ticket_message_body(title, priority, cs_ticket_Id, lastDate, entry, mail_ticket_link, entry_translate)
        feishu_service.send(oa["oa-send-endpoint"])
    elif oa_type == "dingding":
        logging.info("call dingding OI to notification for ticket: {}".format(cs_ticket_Id))
        dingding.push_message(oa["oa-secret"], oa["oa-send-endpoint"], title, priority, cs_ticket_Id, lastDate, entry, mail_ticket_link, entry_translate)
    elif oa_type == "mind":
        logging.info("call mind OI to notification for ticket: {}".format(cs_ticket_Id))
        mind.push_message(oa["oa-send-endpoint"], title, priority, cs_ticket_Id, lastDate, entry, mail_ticket_link, entry_translate)
    else:
        logging.info("unsupported OA type, pls contact: {}".format("spark.liu@cn.ibm.com"))

if __name__ == '__main__':
    #function_requests("","")
    main()