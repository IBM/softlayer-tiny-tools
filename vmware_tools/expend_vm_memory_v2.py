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
import sys
import getopt

vm_name =''
memory_size = ''

def output_help_message():
    print("%s -n <name>  -m <memory_size> " % sys.argv[0])
    print("example:")
    print("           %s -n \"vm-name\"  -m 2" % sys.argv[0])
    print("")

try:
    opts, args = getopt.getopt(
        sys.argv[1:],
        "hn:m:",
        ["name", "memory_size=",],
        )
except getopt.GetoptError:
    output_help_message()
    sys.exit(2)
    
for opt, arg in opts:
    if opt == '-h':
        output_help_message()
        sys.exit()
    elif opt in ("-n", "--name"):
        vm_name = arg
    elif opt in ("-m", "--memory_size"):
        memory_size = arg

if vm_name == "" or memory_size == "" :
    output_help_message()
    sys.exit(2)

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

def upgrade_memory(si, vm_name, size_gb):
    logging.info("扩容虚拟机： {} : {}G".format(vm_name, size_gb))
    vm = None
    content = si.RetrieveContent()

    vm = pchelper.get_obj(content, [vim.VirtualMachine], vm_name)

    if vm is None:
        raise SystemExit("unable to locate VirtualMachine. Arguments given: {0}".format(vm_name))

    # Get the virtual machine's configuration object
    config = vm.config

    # Update the virtual machine's memory size
    memory_mb = config.hardware.memoryMB + int(size_gb) * 1024
    logging.info("upgrade vm {} RAM from {} to {}".format(vm_name, config.hardware.memoryMB, memory_mb))
    # config.hardware.memoryMB = memory_mb

    cspec = vim.vm.ConfigSpec()
    # cspec.numCPUs = 4 # if you want 4 cpus
    # cspec.numCoresPerSocket = 2 # if you want dual-processor with dual-cores
    cspec.memoryMB = memory_mb # 1GB of memory
    # WaitForTask(vm.Reconfigure(cspec))

    # Apply the changes to the virtual machine
    task = vm.ReconfigVM_Task(spec=cspec)
    wait_for_task(task)


# start this thing
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)


    # load vc parameters
    vc_host = os.environ.get("VC_HOST")
    vc_user = os.environ.get("VC_USER")
    vc_pwd = os.environ.get("VC_PASSWORD")
    vc_port = os.environ.get("VC_PORT")
    logging.info("start connect vcenter %s:%s" % (vc_host, vc_port))
    si = SmartConnect(
        host=vc_host,
        user=vc_user,
        pwd=vc_pwd,
        port=vc_port,
        disableSslCertValidation=True)
    # disconnect this thing
    atexit.register(Disconnect, si)

    upgrade_memory(si, vm_name, memory_size)
