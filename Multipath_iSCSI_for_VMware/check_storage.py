#!/usr/bin/python3
# -*- coding: UTF-8 -*-
import SoftLayer

# Connect to SoftLayer
client = SoftLayer.create_client_from_env()
 
# Assert that iSCSI isolation is enabled
isolation_disabled = client['SoftLayer_Account'].getIscsiIsolationDisabled()
print(isolation_disabled)
assert isolation_disabled == False