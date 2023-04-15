#!/usr/bin/python3
# -*- coding: UTF-8 -*-
import SoftLayer

class SL_Service():
    def __init__(self, account_id, username, apikey):
        self.account_id = account_id
        self.client = SoftLayer.create_client_from_env(username=username, api_key=apikey)
        self.account_service = self.client["Account"]
        self.ticket_service = self.client['Ticket']

    def get_tickets(self):
        mask = "mask[accountId, createDate, id, lastEditDate, lastEditType, lastResponseDate, modifyDate, priority, serviceProviderResourceId, status, title, totalUpdateCount, userEditableFlag, lastUpdate]"
     #   ticket = self.ticket_service.getObject(id=id)
        # ticket = self.ticket_service.getAllTicketStatuses()
        # groups = self.ticket_service.getAllTicketGroups()
        # pprint.pprint(ticket)
        # pprint.pprint(groups)
        # ticket = self.ticket_service.getObject(id="151902956")
        # pprint.pprint(ticket)
        # all = self.ticket_subject.getAllObjects()
        # print("1111111111")
        # pprint.pprint(all)
      #  my = self.service_now.getObject("CS3209279")
        return self.account_service.getOpenTickets(self.account_id, mask=mask)
    
   
if __name__ == "__main__":
    service = SL_Service()
    service.get_tickets()
