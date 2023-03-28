#!/usr/bin/python3
# -*- coding: UTF-8 -*-
import SoftLayer
import logging
import pprint


class SL_Service():
    def __init__(self):
        self.client = SoftLayer.create_client_from_env()
        self.account_service = self.client['Account']
        self.subnet_service = self.client['Network_Subnet']
        self.ipaddress_service = self.client["Network_Subnet_IpAddress"]

    def get_subnet_info(self, subnet_id):
        """
        获取指定子网的 IP 地址信息

        :param api_key: SoftLayer API 密钥
        :param subnet_id: 子网的 ID
        :return: 包含子网信息和 IP 地址列表的字典
        """
        mask = "mask[id,addressSpace,networkIdentifier,netmask,gateway,usableIpAddressCount,note,ipAddresses[id,ipAddress,note,isReserved,isBroadcast,isNetwork,isGateway]]"
        # 获取子网信息
        subnet = self.subnet_service.getObject(id=subnet_id, mask=mask)

        ipaddress = []

        for ipaddrs in subnet["ipAddresses"]:
            if "note" not in ipaddrs \
                and ipaddrs["isReserved"] is not True \
                and ipaddrs["isBroadcast"] is not True \
                and ipaddrs["isNetwork"] is not True \
                and ipaddrs["isGateway"] is not True:
                ipaddress.append(ipaddrs)

        # 构造包含子网信息和 IP 地址列表的字典
        subnet_info = {
            "id": subnet["id"],
            'address_space': subnet['addressSpace'],
            'network_identifier': subnet['networkIdentifier'],
            'netmask': subnet['netmask'],
            'gateway': subnet['gateway'],
            'usable_ip_address_count': len(ipaddress),
            'ip_addresses': ipaddress
        }

        return subnet_info
    
    def remove_note_to_ip(self, subnet_id, note):
        """
        获取指定子网的 IP 地址信息

        :param api_key: SoftLayer API 密钥
        :param subnet_id: 子网的 ID
        :return: 包含子网信息和 IP 地址列表的字典
        """
        mask = "mask[id,addressSpace,networkIdentifier,netmask,gateway,usableIpAddressCount,note,ipAddresses[id,ipAddress,note,isReserved,isBroadcast,isNetwork,isGateway]]"
        # 获取子网信息
        subnet = self.subnet_service.getObject(id=subnet_id, mask=mask)

        for ipaddress in subnet["ipAddresses"]:
            logging.debug(ipaddress)
            if "note" in ipaddress and ipaddress["note"] == note:
                address = self.ipaddress_service.getObject(id=ipaddress["id"])
                address["note"] = ""
                result = self.ipaddress_service.editObject(address, id=ipaddress["id"])
                return result

    def add_note_to_ip(self, ip_id, note):
        address = self.ipaddress_service.getObject(id=ip_id)
        address["note"] = note
        result = self.ipaddress_service.editObject(address, id=ip_id)
        return result


if __name__ == "__main__":
    service = SL_Service()
    service.add_note_to_ip("199460334", "spark_test")
    subnets = service.get_subnet_info("1154823")
    pprint.pprint(subnets)
