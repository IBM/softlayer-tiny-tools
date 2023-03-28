#!/usr/bin/python3
# -*- coding: UTF-8 -*-
"""
Written by Spark.liu
Email: spark.liu@cn.ibm.com

Clone a VM from template example
"""
from pyVmomi import vim
from pyVim.connect import SmartConnect, Disconnect
import pchelper
import subnets
import atexit
import yaml
import os
import logging
import pprint
import argparse

ipv4_mask2prefix = lambda mask: sum(bin(int(i, 10)).count('1') for i in mask.split('.'))
ipv6_mask2prefix = lambda mask: sum(bin(int(i, 16)).count('1') for i in mask.split(':'))
mask2prefix = lambda mask: ipv4_mask2prefix(mask) if mask.find(".") > 0 else ipv6_mask2prefix(mask)

def wait_for_task(task):
    """ wait for a vCenter task to finish """
    task_done = False
    while not task_done:
        if task.info.state == 'success':
            return task.info.result

        if task.info.state == 'error':
            logging.error("there was an error")
            logging.error(task.info.error)
            task_done = True

def get_obj(content, vimtype, name):
    """
    Return an object by name, if name is None the
    first found object is returned
    """
    obj = None
    container = content.viewManager.CreateContainerView(
        content.rootFolder, vimtype, True)
    for c in container.view:
        if name:
            if c.name == name:
                obj = c
                break
        else:
            obj = c
            break

    return obj

def clone_vm(
        content, template, vm_name, datacenter_name, vm_folder, datastore_name,
        cluster_name, resource_pool, power_on, datastorecluster_name, vapp_properties):
    """
    Clone a VM from a template/VM, datacenter_name, vm_folder, datastore_name
    cluster_name, resource_pool, and power_on are all optional.
    """

    # if none git the first one
    datacenter = pchelper.get_obj(content, [vim.Datacenter], datacenter_name)

    if vm_folder:
        destfolder = pchelper.search_for_obj(content, [vim.Folder], vm_folder)
    else:
        destfolder = datacenter.vmFolder

    if datastore_name:
        datastore = pchelper.search_for_obj(content, [vim.Datastore], datastore_name)
    else:
        datastore = pchelper.get_obj(
            content, [vim.Datastore], template.datastore[0].info.name)

    # if None, get the first one
    cluster = pchelper.search_for_obj(content, [vim.ClusterComputeResource], cluster_name)
    if not cluster:
        clusters = pchelper.get_all_obj(content, [vim.ResourcePool])
        cluster = list(clusters)[0]

    if resource_pool:
        resource_pool = pchelper.search_for_obj(content, [vim.ResourcePool], resource_pool)
    else:
        resource_pool = cluster.resourcePool

    vmconf = vim.vm.ConfigSpec()

    if datastorecluster_name:
        podsel = vim.storageDrs.PodSelectionSpec()
        pod = pchelper.get_obj(content, [vim.StoragePod], datastorecluster_name)
        podsel.storagePod = pod

        storagespec = vim.storageDrs.StoragePlacementSpec()
        storagespec.podSelectionSpec = podsel
        storagespec.type = 'create'
        storagespec.folder = destfolder
        storagespec.resourcePool = resource_pool
        storagespec.configSpec = vmconf

        try:
            rec = content.storageResourceManager.RecommendDatastores(
                storageSpec=storagespec)
            rec_action = rec.recommendations[0].action[0]
            real_datastore_name = rec_action.destination.name
        except Exception:
            real_datastore_name = template.datastore[0].info.name

        datastore = pchelper.get_obj(content, [vim.Datastore], real_datastore_name)

    # set relospec
    relospec = vim.vm.RelocateSpec()
    relospec.datastore = datastore
    relospec.pool = resource_pool

    clonespec = vim.vm.CloneSpec()
    clonespec.location = relospec
    clonespec.powerOn = power_on

    logging.info("cloning VM...")
    task = template.Clone(folder=destfolder, name=vm_name, spec=clonespec)
    wait_for_task(task)
    logging.info("VM cloned.")

    logging.info('####### Setting properties for %s' % vm_name)
    vm = get_obj(content, [vim.VirtualMachine], vm_name)
    config = vm.config
    configSpec = vim.vApp.VmConfigSpec()
    for prop in config.vAppConfig.property:
        propSpec = vim.vApp.PropertySpec()
        propSpec.operation = 'edit'
        propSpec.info = prop
        propSpec.info.value = str(vapp_properties[prop.id])

        configSpec.property.append(propSpec)

    spec = vim.vm.ConfigSpec()
    spec.vAppConfig = configSpec

    task = vm.Reconfigure(spec)
    wait_for_task(task)
    logging.info('####### Clone of %s complete' % vm_name)

    logging.info('####### Power on vm  %s' % vm_name)
    # Find the vm and power it on
    task = vm.PowerOn()

    # Wait for power on to complete
    wait_for_task(task)
    logging.info('####### Power on vm  %s complete' % vm_name)


def add_vm(si, sl_service, params):
    # load clone vm config 
    vm_number = params['vm-clone-params']["vm_number"]
    vm_template = params['vm-clone-params']["vm_template"]
    datacenter_name = params['vm-clone-params']["datacenter_name"]
    datastorecluster_name = params['vm-clone-params']["datastorecluster_name"]
    cluster_name = params['vm-clone-params']["cluster_name"]
    prefix = params['vm-clone-params']["prefix"]
    private_subnet_id = params['vm-clone-params']["private_subnet_id"]
    private_if_name = params['vm-clone-params']["private_if_name"]
    public_subnet_id = params['vm-clone-params']["public_subnet_id"]
    public_if_name = params['vm-clone-params']["public_if_name"]
    dns0 = params['vm-clone-params']["dns0"]
    dns1 = params['vm-clone-params']["dns1"]

    # vapp attribute
    vapp_properties = {}

    # find available private and public ip address 
    logging.info("find private subnet id: %s" % private_subnet_id)
    private_subnets = sl_service.get_subnet_info(private_subnet_id)
    if private_subnets["address_space"] != "PRIVATE": 
        err_message = "subnet %s is not private subnet " % private_subnet_id
        logging.fatal(err_message)
        raise(Exception(err_message))
    logging.info("find public subnet id: %s" % public_subnet_id )
    public_subnets = sl_service.get_subnet_info(public_subnet_id)
    if public_subnets["address_space"] != "PUBLIC": 
        err_message = "subnet %s is not public subnet " % private_subnet_id
        logging.fatal(err_message)
        raise( Exception( err_message ))
    available_private_ipaddress = len(private_subnets["ip_addresses"])
    available_public_ipaddress = len(public_subnets["ip_addresses"])
    if available_private_ipaddress < vm_number:
        logging.fatal('private ip address count is not sufficient, provided  %d , expect %d' % len(private_subnets["ip_addresses"]), vm_number )
        raise( Exception("private ip count is not sufficient."))
    logging.info("available private ip address count: %d ", available_private_ipaddress)
    if available_public_ipaddress  < vm_number:
        logging.fatal('public ip address count is not sufficient, provided  %d , expect %d' % len(private_subnets["ip_addresses"]), vm_number )
        raise( Exception("public ip count is not sufficient."))
    logging.info("available public ip address count: %d ", available_public_ipaddress)

    # #private interface VApp Properties
    # KEY                        Lable                       Category                     Default
    # private_if_name           "Private Interface Name"     Private Network Properties   bond0
    # private_ip_address        "Private IP Address"         Private Network Properties
    # private_network_prefix    "Private Network Prefix"     Private Network Properties   24 
    # private_network_gateway   "Private Network Gateway"    Private Network Properties

    # #Public interface VApp Properties
    # KEY                        Lable                       
    # public_if_name            "Public Interface Name"      Public Network Properties    bond1
    # public_ip_address         "Public IP Address"          Public Network Properties   
    # public_network_prefix     "Public Network Prefix"      Public Network Properties    24
    # public_network_gateway    "Public Network Gateway"     Public Network Properties

    # # Other
    # KEY                        Lable
    # dns0                      "DNS0"                       DNS                          10.0.80.11
    # dns1                      "DNS1"                       DNS                          10.0.80.12
    # hostname                  "Hostname"                   System                       elex.com

    vapp_properties["private_if_name"] = private_if_name
    vapp_properties["public_if_name"] = public_if_name
    vapp_properties["private_network_prefix"] = mask2prefix(private_subnets["netmask"])
    vapp_properties["public_network_prefix"] = mask2prefix(public_subnets["netmask"])
    vapp_properties["private_network_gateway"] = private_subnets["gateway"]
    vapp_properties["public_network_gateway"] = public_subnets["gateway"]
    vapp_properties["dns0"] = dns0
    vapp_properties["dns1"] = dns1

    logging.info("start connect vcenter %s:%s" % (vc_host, vc_port))
    content = si.RetrieveContent()

    logging.info("start search template: %s" % vm_template)
    template = pchelper.get_obj(content, [vim.VirtualMachine], vm_template)
    if template is None:
        logging.fatal("Can not find template: %s" % vm_template)
        raise( Exception("template not found"))
    logging.info("success find template: %s", vm_template)

    logging.info(" %d VMs will be created.", vm_number)
    for i in range(vm_number):
        private_ip_address = private_subnets["ip_addresses"][i]["ipAddress"]
        public_ip_address = public_subnets["ip_addresses"][i]["ipAddress"]
        vm_name = "%s_%s_%s" % (prefix, private_ip_address, public_ip_address)
        vapp_properties["private_ip_address"] = private_ip_address
        vapp_properties["public_ip_address"] = public_ip_address
        vapp_properties["hostname"] = vm_name
        logging.info("####### start clone No.: %d vm name: %s" % ((i+1), vm_name))
        logging.info("target VM name: %s, private_ip_address: %s public_ip_address: %s" %
                    (vm_name, private_ip_address, public_ip_address))
        logging.info("vapp properties %s", vapp_properties)
        clone_vm(
            content, template, vm_name, datacenter_name, "",
            "", cluster_name, "", False,
            datastorecluster_name, vapp_properties)
        # mark ip address
        sl_service.add_note_to_ip(private_subnets["ip_addresses"][i]["id"], vm_name)
        sl_service.add_note_to_ip(public_subnets["ip_addresses"][i]["id"], vm_name)

def delete_vm(si, sl_service, params, vm_name):
    VM = None
    if vm_name:
        VM = pchelper.get_obj(si.content, [vim.VirtualMachine], args.vm_name)

    if VM is None:
        raise SystemExit("unable to locate VirtualMachine. Arguments given: {0}".format(vm_name))

    logging.info("Found: {0}".format(VM.name))
    logging.info("The current powerState is: {0}".format(VM.runtime.powerState))
    if format(VM.runtime.powerState) == "poweredOn":
        logging.info("Attempting to power off {0}".format(VM.name))
        task = VM.PowerOffVM_Task()
        wait_for_task(task)
        logging.info("{0}".format(task.info.state))

    logging.info("Destroying VM {0} from vSphere.".format(vm_name))
    task = VM.Destroy_Task()
    wait_for_task(task)
    logging.info("Destroying VM {0} from complete.".format(vm_name))

    private_subnet_id = params['vm-clone-params']["private_subnet_id"]
    public_subnet_id = params['vm-clone-params']["public_subnet_id"]

    sl_service.remove_note_to_ip(private_subnet_id, vm_name)
    sl_service.remove_note_to_ip(public_subnet_id, vm_name)


# start this thing
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    # 创建解析器
    parser = argparse.ArgumentParser(description="执行添加或删除操作")

    # 添加子命令
    subparsers = parser.add_subparsers(title="子命令", dest="command")
    add_parser = subparsers.add_parser("add", help="clone vms")
    delete_parser = subparsers.add_parser("delete", help="delete vms")

    # 添加参数
    delete_parser.add_argument("vm_name", help="vm name")
    # 解析参数并执行相应函数
    args = parser.parse_args()

    # load vc parameters
    vc_host = os.environ.get("VC_HOST")
    vc_user = os.environ.get("VC_USER")
    vc_pwd = os.environ.get("VC_PASSWORD")
    vc_port = os.environ.get("VC_PORT")
    si = SmartConnect(
        host=vc_host,
        user=vc_user,
        pwd=vc_pwd,
        port=vc_port,
        disableSslCertValidation=True)
    # disconnect this thing
    atexit.register(Disconnect, si)
    sl_service = subnets.SL_Service()

    with open('config.yaml', 'r') as f:
        params = yaml.safe_load(f)

    if args.command == "add":
        add_vm(si, sl_service, params)
    elif args.command == "delete":
        logging.info("delete {0}".format(args.vm_name))
        delete_vm(si, sl_service, params, args.vm_name)
