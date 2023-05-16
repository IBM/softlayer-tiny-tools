#!/usr/bin/python3
# -*- coding: UTF-8 -*-
import softlayer_service
import feishu
import translate
import logging
import yaml
import dingding
import mind
import time 
import datetime
from datetime import datetime, timedelta, timezone

def load_yaml_config(filename):
    with open(filename, 'r') as f:
        config = yaml.safe_load(f)
    return config


def main():
    # set log level 
    logging.basicConfig(level=logging.INFO)
    global_tickets = {}
    #load config
    config = load_yaml_config("config.yaml")
    translate_service = translate.Translate(config["translate-api-key"], config["translate-service-endpoint"])
    notification_users = config["ticket-notification-users"]
    for user in notification_users:
        global_tickets[user["account"]] = {}
    
    while True:
        try:
            
            for notification_user in notification_users:
                # list all of opened ticket from sl base on account
                account_id = notification_user["account"]
                account_long_id= notification_user["account-id"]
                predefined_priority = notification_user["priority"]
                sl_service = softlayer_service.SL_Service(account_id, notification_user["apikey-username"], notification_user["apikey"])
                sl_tickets = sl_service.get_tickets()
                logging.info("find opened tickets {} for account {}".format(len(sl_tickets), account_id))

                for sl_ticket in sl_tickets:
                    ticket_id = sl_ticket["id"]
                    ticket_last_update = sl_ticket["lastUpdate"]["createDate"]
                    ticket_priority = sl_ticket["priority"]
                    ticket_title = sl_ticket["title"]
                    ticket_cs_id = sl_ticket["serviceProviderResourceId"]
                    ticket_link = "https://cloud.ibm.com/unifiedsupport/cases/manage/{}?accountId={}".format(ticket_cs_id, account_long_id)
                    if ticket_priority <= predefined_priority:
                        if ticket_id not in global_tickets[account_id]:
                            logging.info("find a new ticket {} : {}".format(ticket_id, ticket_cs_id))
                            dt = datetime.fromisoformat(ticket_last_update)

                            local_time = datetime.now(timezone.utc).astimezone()
                            # 或者使用下面这行代码代替上面一行代码
                            # local_time = datetime.now(timezone.utc).replace(tzinfo=None)
                            time_diff = local_time - dt
                            logging.info("new ticket {} : {} last update time is {}, local time is {}".format(ticket_id, ticket_cs_id, dt, local_time))
                            if time_diff < timedelta(days=2):
                                entry = sl_ticket["lastUpdate"]["entry"]
                                logging.info("call translate function for ticket {} : {}".format(ticket_id, ticket_cs_id))
                                entry_translate = translate_service.translateToChinese(entry)
                                entry_translate = entry_translate["translations"][0]["translation"]
                                # send notification
                                for oa in notification_user["oas"]:
                                    call_oa(oa, ticket_title, ticket_priority, ticket_id, ticket_cs_id, ticket_last_update, entry, ticket_link, entry_translate)
                                global_tickets[account_id][ticket_id] = sl_ticket
                            else:
                                logging.info("new ticket {} : {} last update {} is more than 2 days old, skip notification".format(ticket_id, ticket_cs_id, ticket_last_update))
                        else:
                            logging.info("the ticket {} : {} is not new, check last update".format(ticket_id, ticket_cs_id))
                            # compare times
                            previous_ticket_last_update = global_tickets[account_id][ticket_id]["lastUpdate"]["createDate"]
                            time1 = datetime.fromisoformat(previous_ticket_last_update)
                            time2 = datetime.fromisoformat(ticket_last_update)

                            if time1 < time2:
                                logging.info
                                # 工单已经被更新，发送通知
                                entry = sl_ticket["lastUpdate"]["entry"]
                                logging.info("call translate function for ticket {} : {}".format(ticket_id, ticket_cs_id))
                                entry_translate = translate_service.translateToChinese(entry)
                                entry_translate = entry_translate["translations"][0]["translation"]
                                for oa in notification_user["oas"]:
                                    call_oa(oa, ticket_title, ticket_priority, ticket_id, ticket_cs_id, ticket_last_update, entry, ticket_link, entry_translate)
                                global_tickets[account_id][ticket_id] = sl_ticket
                            else:
                                logging.info("ticket {} : {} is not update".format(ticket_id, ticket_cs_id))
                    else:
                        logging.info("ticket: {} : {} priority {} less than set priority {}, skip notification".format(ticket_id, ticket_cs_id, ticket_priority, predefined_priority))
            interval = config["mail-check-interval"]
            logging.info("sleep {}...".format(interval))
            time.sleep(interval)
        except Exception as e:
            logging.error(e)
            raise e

def call_oa(oa, title, priority, ticket_id, cs_ticket_Id, lastDate, entry, mail_ticket_link, entry_translate):
    oa_type = oa["oa-type"]
    if oa_type == "feishu":
        logging.info("call feishu OI to notification for ticket {} : {}".format(ticket_id, cs_ticket_Id))
        feishu_service = feishu.Lark()
        feishu_service.build_ticket_message_body(title, priority, cs_ticket_Id, lastDate, entry, mail_ticket_link, entry_translate)
        feishu_service.send(oa["oa-send-endpoint"])
    elif oa_type == "dingding":
        logging.info("call dingding OI to notification for ticket {} : {}".format(ticket_id, cs_ticket_Id))
        dingding.push_message(oa["oa-secret"], oa["oa-send-endpoint"], title, priority, cs_ticket_Id, lastDate, entry, mail_ticket_link, entry_translate)
    elif oa_type == "mind":
        logging.info("call mind OI to notification for ticket {} : {}".format(ticket_id, cs_ticket_Id))
        mind.push_message(oa["oa-send-endpoint"], title, priority, cs_ticket_Id, lastDate, entry, mail_ticket_link, entry_translate)
    else:
        logging.info("unsupported OA type, pls contact: {}".format("spark.liu@cn.ibm.com"))

if __name__ == '__main__':
    main()