#!/bin/bash

# INSTALL AND RUNN AGENT

# Check if ACCESS_KEY and API_ENDPOINT environment variables are set
if [ -z "$ACCESS_KEY" ] || [ -z "$API_ENDPOINT" ]; then
    echo "Error: The environment variables ACCESS_KEY and API_ENDPOINT must be set."
    exit 1
fi

# Define the base command for installing the agent
install_command="curl -sL https://ibm.biz/install-sysdig-agent | sudo bash -s -- -a ${ACCESS_KEY} \
-c ingest.${API_ENDPOINT} --collector_port 6443 --secure true -ac \"sysdig_capture_enabled: false\""

# Check if TAGS environment variable is set
if [ -z "$TAGS" ]; then
    # Install agent with tags
    install_command+=" --tags ${TAGS}"
fi

# Execute the installation command
eval "$install_command"


# INSTALL AND RUNN HOST ANALYZER 
cp ./host_analyzer /user/bin/
chmod +x /user/bin/host_analyzer

AM_COLLECTOR_ENDPOINT=$API_ENDPOINT
export AM_COLLECTOR_ENDPOINT=https://$API_ENDPOINT/internal/scanning/scanning-analysis-collector
export SCHEDULE=@dailydefault 
./create_host_analyzer_service.sh
service host_analyzer start
service host_analyzer enable

# INSTALL AND RUNN kspm-analyzer
export HOST_ROOT_PATH=/
cp -rf ./ksmp-analyzer /root/
cd /root/ksmp-analyzer 





