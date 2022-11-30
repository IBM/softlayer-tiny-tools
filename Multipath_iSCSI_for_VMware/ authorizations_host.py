#!/usr/bin/python3
# -*- coding: UTF-8 -*-
import SoftLayer

# Connect to SoftLayer
client = SoftLayer.create_client_from_env()
 
# Assert that iSCSI isolation is enabled
isolation_disabled = client['SoftLayer_Account'].getIscsiIsolationDisabled()
print(isolation_disabled)
assert isolation_disabled == False


STORAGE_ID = 409813173
SUBNET_ID = 1146195
HOST_IDS = (1874193, 3056108)
 
# Connect to SoftLayer
client = SoftLayer.create_client_from_env()
 
# Authorize hosts to storage
for host_id in HOST_IDS :
  try :
    client['SoftLayer_Network_Storage_Iscsi'].allowAccessFromHost('SoftLayer_Hardware', host_id, id = STORAGE_ID)
  except :
    if 'Already Authorized' in sys.exc_info()[1].message :
      pass
    else :
      raise
 
# Lookup the "iSCSI ACL object id" for each host
hardwareMask = 'mask[allowedHardware[allowedHost[credential]]]'
result = client['SoftLayer_Network_Storage_Iscsi'].getObject(id = STORAGE_ID, mask = hardwareMask)
aclOids = [x['allowedHost']['id'] for x in result['allowedHardware']]
 
# Add our iSCSI subnet to each host's iSCSI ACL
for acl_id in aclOids :
  # Assign; note subnet is passed as array
  client['SoftLayer_Network_Storage_Allowed_Host'].assignSubnetsToAcl([SUBNET_ID], id = acl_id)
 
  # Verify success
  result = client['SoftLayer_Network_Storage_Allowed_Host'].getSubnetsInAcl(id = acl_id)
  assert len(result) > 0