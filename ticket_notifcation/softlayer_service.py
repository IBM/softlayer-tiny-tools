#!/usr/bin/python3
# -*- coding: UTF-8 -*-
import SoftLayer

class SL_Service():
    def __init__(self, account_id, username, apikey):
        self.account_id = account_id
        self.client = SoftLayer.create_client_from_env(username=username, api_key=apikey)
        debugger = SoftLayer.DebugTransport(self.client.transport)
        self.client.transport = debugger
        self.account_service = self.client["Account"]
        self.ticket_service = self.client['Ticket']

    def debug(self):
        for call in self.client.transport.get_last_calls():
            print(self.client.transport.print_reproduceable(call))

    def get_tickets(self):
        mask = "mask[accountId, createDate, id, lastEditDate, lastEditType, lastResponseDate, modifyDate, priority, serviceProviderResourceId, status, title, totalUpdateCount, userEditableFlag, lastUpdate]"
        return self.account_service.getOpenTickets(self.account_id, mask=mask)

if __name__ == "__main__":
    service = SL_Service()
    service.get_tickets()
