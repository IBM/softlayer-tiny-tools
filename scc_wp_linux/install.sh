#!/bin/bash
set -e

# Check if ACCESS_KEY and API_ENDPOINT environment variables are set
if [ -z "$ACCESS_KEY" ] || [ -z "$API_ENDPOINT" ]; then
    echo "Error: The environment variables ACCESS_KEY and API_ENDPOINT must be set."
    exit 1
fi

# INSTALL AND RUNN AGENT
install_agent() {
    echo "start install agent...."
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
    echo "install completed...."
}

install_host_analyzer() {
    # INSTALL AND RUNN HOST ANALYZER
    echo "start install host analyzer...."
    cp ./host_analyzer /usr/bin/
    chmod +x /usr/bin/host_analyzer

    AM_COLLECTOR_ENDPOINT=$API_ENDPOINT
    ./check_env.sh AM_COLLECTOR_ENDPOINT "https://$API_ENDPOINT/internal/scanning/scanning-analysis-collector"
    ./check_env.sh SCHEDULE "@dailydefault" 
    ./check_env.sh ACCESS_KEY $ACCESS_KEY
    ./create_host_analyzer_service.sh
    service host_analyzer start
    service host_analyzer enable

    # INSTALL AND RUNN kspm-analyzer
    export HOST_ROOT_PATH=/
    cp -rf ./ksmp-analyzer /root/
    cd /root/ksmp-analyzer 
}

# Check or install agent service
if pgrep -x "dragent" >/dev/null; then
    echo "The service 'dragent' is running. skill install"
else
    install_agent
fi

# Check or install host_analyzer service
if pgrep -x "host_analyzer" >/dev/null; then
    echo "The service 'host_analyzer' is running. skill install"
else
    install_host_analyzer
fi



