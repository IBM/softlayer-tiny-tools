import os.path
import logging
import base64
import re

from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

logging.setLogRecordFactory

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly', 'https://www.googleapis.com/auth/gmail.modify']
SENDER = "no_reply@cloud.ibm.com"

def parse_url(url):
    parsed_url = urlparse(url)
    return {
        'Scheme': parsed_url.scheme,
        'Netloc': parsed_url.netloc,
        'Path': parsed_url.path,
        'Params': parsed_url.params,
        'Query': parsed_url.query,
        'Fragment': parsed_url.fragment
    }

def get_message_body(message):
    # 获取邮件正文部分
    if 'parts' in message['payload']:
        for part in message['payload']['parts']:
            if part['mimeType'] == 'text/html':
                data = part['body']['data']
                break
    else:
        data = message['payload']['body']['data']

    # 对邮件正文进行解码和解析
    decoded_data = base64.urlsafe_b64decode(data).decode('utf-8')
    soup = BeautifulSoup(decoded_data, 'html.parser')
    return soup

def get_message_links(message):
    soup = get_message_body(message)
    logging.debug(soup.get_text())
    # 提取邮件正文中的所有超链接
    links = []
    for link in soup.find_all('a'):
        href = link.get('href')
        if href:
            links.append(href)
    return links

def mark_as_read(service, message_id):
    # 将指定的邮件标记为已读
    try:
        message = service.users().messages().get(userId='me', id=message_id).execute()
        labels = message['labelIds']
        labels.remove('UNREAD')
        body = {'removeLabelIds': ['UNREAD'], 'addLabelIds': labels}
        service.users().messages().modify(userId='me', id=message_id, body=body).execute()
    except HttpError as error:
        print('An error occurred: %s' % error)

def get_mail_creds(token_path, credentials_path):
    """Shows basic usage of the Gmail API.
    Lists the user's Gmail labels.
    """
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(credentials_path, SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open(token_path, 'w') as token:
            token.write(creds.to_json())
    return creds

def get_mail_links(token_path, credentials_path):
    creds = get_mail_creds(token_path, credentials_path)

    try:
        # 调用Gmail API获取未读邮件
        service = build('gmail', 'v1', credentials=creds)
        filter = 'is:unread from:{}'.format(SENDER)
        logging.info(filter)
        results = service.users().messages().list(userId='me', q=filter).execute()
    
        links =[]
        if 'messages' in results:
            logging.info("get unread mail number: {}".format(len(results['messages'])))
            for message in results['messages']:
                # 调用Gmail API获取邮件内容
                msg = service.users().messages().get(userId='me', id=message['id']).execute()
                # 输出邮件主题和正文
                logging.debug('Subject: {}'.format(msg['payload']['headers'][17]['value']))
                logging.debug('Body: {}'.format(get_message_body(msg)))
                message_links = get_message_links(msg)
                if message_links:
                    logging.debug('Links:')
                    for link in message_links:
                        logging.info(link)
                        links.append(link)
                else:
                    logging.info('No links found.')
                mark_as_read(service, msg['id'])
        else:
            logging.info('No unread messages found.')
        return links

    except HttpError as error:
        logging.info(f'An error occurred: {error}')

if __name__ == '__main__':
    token_path = "token.json"
    credentials_path = 'credentials.json'
    links = get_mail_links(token_path, credentials_path)
    for link in links: 
        url = parse_url(link)
        if url["Netloc"] == "cloud.ibm.com" and "/cases/manage" in url["Path"]:
            match = re.search(r'\/(\w+)$', url["Path"])
            service_now_id= ""
            if match:
                service_now_id = match.group(1)

            query_params = parse_qs(url["Query"])
            account_id = query_params.get('accountId', [''])[0]
            logging.info("account ID: {}".format(account_id))
            logging.info("service_now_id: {}".format(service_now_id))
