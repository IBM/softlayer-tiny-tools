import requests
import json

card_title_style = ("red","yellow","blue","green")

lark_ticket_template = {
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

    def build_ticket_message_body(self, account_id, account_name, title, priority, ticketId, cs_ticketId,lastDate, entry, url):
        self.ticket_template["card"]["header"] = self.get_header(title, priority)
        elements =  self.ticket_template["card"]["elements"]

        elements.append(self.wrapElement("account_id", account_id))
        elements.append(self.wrapElement("account_name", account_name))
        elements.append(self.wrapElement("优先级", priority))
        elements.append(self.wrapElement("工单号", "[{}]({})".format(cs_ticketId, url)))
        elements.append(self.wrapElement("IMS", "[{}]({})".format(ticketId, "https://internal.softlayer.com/Ticket/ticketEdit/{}".format(ticketId))))
        # elements.append(self.get_link(ticketId, url))
        elements.append(self.wrapElement("更新日期", lastDate))
        elements.append(self.wrapElement("内容", entry))
    
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
        self.add_element(elements, "start_time", startTime)
        self.add_element(elements, "end_time", endTime)
        self.add_element(elements, "update_time", updateTime)


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

    def get_link(self, ticket_number, url):
        return {
                    "actions": [{
                            "tag": "button",
                            "text": {
                                    "content":  "**{0}** : {1}".format("工单号", ticket_number),
                                    "tag": "lark_md"
                            },
                            "url": url,
                            "type": "default",
                            "value": {}
                    }],
                    "tag": "action"
            }

   
if __name__ == "__main__":
    title = 'HPVS gen2 for VPC connect VPE timeout'
    priority = 4
    ticketId =  'CS3245985'
    lastDate = '2023-02-22T00:59:10-06:00'
    entry = 'Can you provide the info on below mentioned points '
    url = ""

    # 指定端点URL
    endpoint = ''
    service = Lark()
    service.build_ticket_message_body(title, priority, ticketId, lastDate, entry, url)
    service.send(endpoint)


