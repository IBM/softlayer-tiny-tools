import requests
import json
from datetime import datetime, timezone, timedelta

card_title_style = ("red","yellow","blue","green")


class Lark():
    def __init__(self):
        self.ticket_template =  {
            "msg_type": "interactive",
            "card": {
                "elements": [],
                "header": {
                    "title": {
                        "tag": "plain_text",
                        "content": "This is header"
                    },
                        "template":"red"
                }
            }
        }

    
    def build_notifcation_body(self,
        title,
        priority,
        accountID,
        accountShortID,
        body,
        state,
        severity,
        componentNames,
        continentNames, 
        regionNames,
        regions,
        sourceID,
        category, 
        subCategory,
        startTime,
        endTime,
        updateTime):
        self.ticket_template["card"]["header"] = self.get_header(title, priority)
        elements =  self.ticket_template["card"]["elements"]

        self.add_element(elements, "account_id", accountID)
        self.add_element(elements, "account", accountShortID)
        self.add_element(elements, "content", body)
        self.add_element(elements, "state", state)
        self.add_element(elements, "severity", severity)
        self.add_element(elements, "component_names", componentNames)
        self.add_element(elements, "continent_names", continentNames)
        self.add_element(elements, "region_names", regionNames)
        self.add_element(elements, "regions", regions)
        self.add_element(elements, "source_ID", sourceID)
        self.add_element(elements, "category", category)
        self.add_element(elements, "sub_category", subCategory)
        self.add_element(elements, "start_time", self.convert_to_beijing_time(startTime))
        self.add_element(elements, "end_time", self.convert_to_beijing_time(endTime))
        self.add_element(elements, "update_time", self.convert_to_beijing_time(updateTime))


    def add_element(self, elements, key, content):
        if isinstance(content, list):
            content = ", ".join(content)
        if content:
            elements.append(self.wrapElement(key, content))


    def get_header(self, title, priority):
        header ={
            "title": {
                "tag": "plain_text",
                "content": title
            },
                "template": "grey"
        }
        if priority>0 and priority<5: 
            header["template"]= card_title_style[priority-1]
    
        return header

    def convert_to_beijing_time(self, unix_time):
        if unix_time == None :
             return None
        # 判断时间戳的位数，13位通常是毫秒，10位通常是秒
        if len(str(int(unix_time))) == 13:
            unix_time = unix_time / 1000
        # 将 Unix 时间戳转换为 datetime 对象
        utc_time = datetime.fromtimestamp(unix_time, tz=timezone.utc)
        # 将 UTC 时间转换为北京时间 (UTC+8)
        beijing_time = utc_time + timedelta(hours=8)
        return beijing_time
    
    def send(self, url):
        # 将数据转换为JSON格式
        json_data = json.dumps(self.ticket_template)
        print(json_data)
        # 发送POST请求，将JSON数据发送到指定端点
        post_headers = {'Content-Type': 'application/json'}
        response = requests.post(url, data=json_data, headers=post_headers)
        # 输出响应内容
        print(response.text)

    def wrapElement(self, field_name, field):
        element =             {
                "tag": "div",
                "text": {
                    "content": "**{0}** : {1}".format(field_name, field),
                    "tag": "lark_md"
                    }
                }
        return element


