#!/usr/bin/python3
# -*- coding: UTF-8 -*-
import SoftLayer
from pprint import pprint
import logging

logging.basicConfig(level=logging.INFO)

class PhysicalServerManager:
    """
    物理服务器管理器，用于与 SoftLayer API 交互以管理物理服务器
    """
    def __init__(self):
        """
        初始化 SoftLayer API 客户端
        """
        self.client = SoftLayer.Client()
        
    def list_servers_with_status(self, status_code):
        """
        列出具有特定 hardwareStatus 的所有物理服务器
        Status id 23 is SPARE_POOL Status id 5 is ACTIVE

        Args:
            status_code (int): 硬件状态码

        Returns:
            list: 包含所有符合条件的物理服务器信息的字典列表
        """
        object_filter = {"hardware":{"hardwareStatus":{"id":{"operation":status_code}}}}

        try:
            # 使用 objectFilter 调用 SoftLayer_Hardware API
            hardware_list = self.client.call(
                "SoftLayer_Account",
                "getHardware",
                filter=object_filter,
                mask="id,hostname,domain,datacenter.name,hardwareStatus,hardwareStatus,sparePoolBillingItem"
            )
            return hardware_list

        except SoftLayer.SoftLayerAPIError as e:
            print(f"Unable to retrieve hardware. Error: {e.faultString}")
            return []
    
    def cancel_device(self, billing_item_id):
        """
        取消指定的计费项

        Args:
            billing_item_id (int): 计费项 ID

        Returns:
            bool: 是否成功取消
        """
        try:
            result = self.client.call(
                "SoftLayer_Billing_Item",
                "cancelItem",
                id=billing_item_id
            )
            return result
        except SoftLayer.SoftLayerAPIError as e:
            print(f"Unable to cancel billing item {billing_item_id}. Error: {e.faultString}")
            return False
    
    def cancel_devices_with_status(self, status_code):
        logging.info("list all of device with status code %s", status_code)
        devices = self.list_servers_with_status(status_code)
        logging.info("****%d**** device will be canceled", len(devices))
        pprint(devices[0])
        for device in devices:
            logging.info("Cancel device with device_name: %s, device_id: %s, sparePoolBillingItem:%s",
            device["hostname"],
            device["id"],
            device["sparePoolBillingItem"]["id"]
            )
            self.cancel_device(device["sparePoolBillingItem"]["id"])
            break

if __name__ == "__main__":
    manager = PhysicalServerManager()
    #Status id 23 is SPARE_POOL Status id 5 is ACTIVE
    status_code = 23  # 筛选 hardwareStatus 为 23 的设备
    servers = manager.cancel_devices_with_status(status_code)
   



