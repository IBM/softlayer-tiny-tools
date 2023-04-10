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