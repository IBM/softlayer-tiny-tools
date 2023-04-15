#!/usr/bin/python3
# -*- coding: UTF-8 -*-
import pprint
from ibm_watson import LanguageTranslatorV3
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator

class Translate():
    def __init__(self, apikey, url):
        self.authenticator = IAMAuthenticator(apikey)
        self.language_translator = LanguageTranslatorV3(
            version='2018-05-01',
            authenticator=self.authenticator
        )
        self.language_translator.set_service_url(url)

    def translateToChinese(self, text): 
        return self.language_translator.translate(text, model_id='en-zh').get_result()


if __name__ == "__main__":
    api_key = ""
    url_translate = ""

    service = Translate(api_key, url_translate)
    ch = service.translateToChinese("this is a test")
    pprint.pprint(ch)