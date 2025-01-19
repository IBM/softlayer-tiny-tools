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
    logging.basicConfig(level=logging.DEBUG)
    global_tickets = {}
    #load config
    config = load_yaml_config("./config/config.yaml")
    #config = load_yaml_config("config.yaml")
    notification_users = config["ticket-notification-users"]
    for user in notification_users:
        global_tickets[user["account"]] = {}
    
    while True:
        try:
            for notification_user in notification_users:
                # list all of opened ticket from sl base on account
                keywords = notification_user["keywords"]
                account_id = notification_user["account"]
                account_long_id= notification_user["account-id"]
                predefined_priority = notification_user["priority"]
                sl_service = softlayer_service.SL_Service(account_id, notification_user["apikey-username"], notification_user["apikey"])
                sl_tickets = sl_service.get_tickets()
                logging.info("find opened tickets {} for account {}".format(len(sl_tickets), account_id))

                for sl_ticket in sl_tickets:
                    ticket_id = sl_ticket["id"]
                    if "lastUpdate" not in sl_ticket:
                        logging.warning("ticket {} not have lastUpdate field, skip it.".format(ticket_id))
                        continue
                    ticket_last_update = sl_ticket["lastUpdate"]["createDate"]
                    ticket_priority = sl_ticket["priority"]
                    ticket_title = sl_ticket["title"]
                    ticket_cs_id = sl_ticket["serviceProviderResourceId"]
                    account_name = sl_ticket["account"]["companyName"]
                    logging.debug(ticket_title)

                    if not check_title(keywords, ticket_title):
                        logging.info("ticket {} not in keywords {} and skip it.".format(ticket_cs_id, keywords))
                        continue
                    logging.info("ticket {} keywords check passed".format(ticket_cs_id))
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
                                # send notification
                                for oa in notification_user["oas"]:
                                    call_oa(oa, account_id, account_name, ticket_title, ticket_priority, ticket_id, ticket_cs_id, ticket_last_update, entry, ticket_link)
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
                                for oa in notification_user["oas"]:
                                    call_oa(oa,account_id, account_name, ticket_title, ticket_priority, ticket_id, ticket_cs_id, ticket_last_update, entry, ticket_link)
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


def call_oa(oa, account_id, account_name, title, priority, ticket_id, cs_ticket_Id, lastDate, entry, mail_ticket_link):
    oa_type = oa["oa-type"]
    if oa_type == "feishu":
        logging.info("call feishu OI to notification for ticket {} : {}".format(ticket_id, cs_ticket_Id))
        feishu_service = feishu.Lark()
        feishu_service.build_ticket_message_body(account_id, account_name, title, priority, ticket_id, cs_ticket_Id, lastDate, entry, mail_ticket_link)
        feishu_service.send(oa["oa-send-endpoint"])
    elif oa_type == "dingding":
        logging.info("call dingding OI to notification for ticket {} : {}".format(ticket_id, cs_ticket_Id))
        dingding.push_message(oa["oa-secret"], oa["oa-send-endpoint"], title, priority, cs_ticket_Id, lastDate, entry, mail_ticket_link)
    elif oa_type == "mind":
        logging.info("call mind OI to notification for ticket {} : {}".format(ticket_id, cs_ticket_Id))
        mind.push_message(oa["oa-send-endpoint"], title, priority, cs_ticket_Id, lastDate, entry, mail_ticket_link)
    else:
        logging.info("unsupported OA type, pls contact: {}".format("spark.liu@cn.ibm.com"))

def check_title(keywords, title):
    if len(keywords) == 0 :
        return True
    for keyword in keywords:
        if keyword.lower() in title.lower(): 
            return True
    return False



if __name__ == '__main__':
    main()