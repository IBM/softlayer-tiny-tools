## install requirements
pip3 install -r requirements.txt  
## edit env.sh and config.yaml
source env.sh
## add execution privilege 
chmod +x clone_vm.py
## clone VM 
clone_vm.py add 
## delete VM 
clone_vm.py delete  vm_name


## 虚拟机内存 扩容 2 GB
./expend_vm_memory.py -i "10.155.206.72"  -m 2

## 基于vm 名字扩容
./expend_vm_memory_v2.py -n "vm-name" -m 2