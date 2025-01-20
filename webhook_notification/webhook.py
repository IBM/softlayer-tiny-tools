from flask import Flask, request, jsonify
import feishu
import logging
import yaml

app = Flask(__name__)

users = {}

@app.route('/webhook', methods=['POST'])
def webhook():
    # Get the JSON data from the request
    data = request.get_json()
    logging.info("Received webhook data: {}".format(data))

    accountID = add_default_null(data, "account_id")
    if accountID not in users:
        logging.info("skip process, as user {} not in config list.".format(accountID))
        return jsonify({"message": "invalid users"}), 400
    else: 
        feishu_endpoints = users[accountID]["oas"]
        accountShortID = users[accountID]["account"]
        logging.info("find account id {}".format(accountShortID))

    body = add_default_null(data, "body")
    body = join_body_text(data["body"])
    category = add_default_null(data, "category")
    componentNames = add_default_null(data,"componentNames")
    state = add_default_null(data, "state")
    title = add_default_null(data, "title")
    title = join_body_text(title)
    startTime= add_default_null(data, "startTime")
    endTime = add_default_null(data, "endTime")
    severity = add_default_null(data,"severity")
    continentNames = add_default_null(data, "continentNames")
    regionNames = add_default_null(data, "regionNames")
    regions = add_default_null(data, "regions")
    sourceID = add_default_null(data, "sourceID")
    category = add_default_null(data, "category")
    subCategory = add_default_null(data, "subCategory")
    startTime = add_default_null(data, "startTime")
    endTime = add_default_null(data, "endTime")
    updateTime = add_default_null(data,"updateTime")
    priority = get_priority(severity)

    feishu_service = feishu.Lark()
    feishu_service.build_notifcation_body(
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
        updateTime)
    for oa in feishu_endpoints:
        feishu_endpoint = oa["oa-send-endpoint"]
        logging.info(feishu_endpoint)
        feishu_service.send(feishu_endpoint)

    # Return a response
    return jsonify({"message": "Webhook received successfully"}), 200

def join_body_text(body_array):
    # Check if the body_array is a list and contains dictionaries with a 'text' field
    if isinstance(body_array, list):
        # Extract 'text' fields and join them with a new paragraph separator
        paragraphs = "\n\n".join(item["text"] for item in body_array if "text" in item)
        return paragraphs
    else:
        return ""
def add_default_null(body, key):
    if key in body:
        return body[key]
    else: 
        return None 

def get_priority(severity):
    if severity in ["Severity 1", "High impact", "Major"]:
        return 1 
    elif severity in ["Severity 2", "Medium impact"]:
        return 2
    elif severity in ["Severity 3"]:
        return 3 
    elif severity in ["Severity 4", "Low impact", "Minor"]:
        return 4 
    return 0 

def load_yaml_config(filename):
    with open(filename, 'r') as f:
        config = yaml.safe_load(f)
    return config

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    config = load_yaml_config("./config/config.yaml")
    port = config["port"]
    for notification_user in config["notification-users"]:
        users[notification_user["account-id"]] = notification_user
    # Run the server
    app.run(host='0.0.0.0', port=port)
