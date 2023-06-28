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
    ./check_env.sh API_ENDPOINT "https://$API_ENDPOINT/internal/scanning/scanning-analysis-collector" /etc/host_analyzer.env
    ./check_env.sh SCHEDULE "@dailydefault"  /etc/host_analyzer.env
    ./check_env.sh ACCESS_KEY $ACCESS_KEY /etc/host_analyzer.env
    ./create_host_analyzer_service.sh
    service host_analyzer start
    service host_analyzer enable
}

# INSTALL AND RUNN kspm-analyzer
install_kspm_analyzer() {
    echo "start install kspm analyzer...."
    if [ ! -f /bin/kspm-analyzer ]; then
        cp ./kspm-analyzer/bin/kspm-analyzer /bin
    fi
    if [ ! -f ./kspm-analyzer/configs ]; then
        cp -r ./kspm-analyzer/configs /
    fi
    if  [ ! -f ./kspm-analyzer/binaries ]; then
    cp ./kspm-analyzer/binaries /
    fi
    AM_COLLECTOR_ENDPOINT=$API_ENDPOINT
    ./check_env.sh API_ENDPOINT $API_ENDPOINT /etc/kspm_analyzer.env
    ./check_env.sh ACCESS_KEY $ACCESS_KEY /etc/kspm_analyzer.env
    ./check_env.sh HOST_ROOT_PATH / /etc/kspm_analyzer.env
    ./create_kspm_analyzer_service.sh
    service host_analyzer start
    service host_analyzer enable
}

# Check or install agent service
DRAGENT_SERVICE_SCRIPT="/etc/init.d/dragent"
if [ -f $DRAGENT_SERVICE_SCRIPT ]; then
    echo "$DRAGENT_SERVICE_SCRIPT Service script already exists."
    if pgrep -x "dragent" >/dev/null; then
        echo "The service 'dragent' is running. skip install"
    else
        service dragent start
    fi
else 
    install_agent
fi 

# Check or install host_analyzer service
HOST_ANALYZER_SERVICE_SCRIPT="/etc/init.d/host_analyzer"
if [ -f $HOST_ANALYZER_SERVICE_SCRIPT ]; then
    echo "$HOST_ANALYZER_SERVICE_SCRIPT Service script already exists."
    if pgrep -x "host_analyzer" >/dev/null; then
        echo "The service 'host_analyzer' is running. skip install"
    else
        service host_analyzer start
    fi
else 
    install_host_analyzer
fi

# Check or install kspm_analyzer service
KSPM_ANALYZER_SERVICE_SCRIPT="/etc/init.d/kspm_analyzer"
if [ -f $KSPM_ANALYZER_SERVICE_SCRIPT ]; then
    echo "$KSPM_ANALYZER_SERVICE_SCRIPT Service script already exists."
    if pgrep -x "kspm_analyzer" >/dev/null; then
        echo "The service 'kspm_analyzer' is running. skip install"
    else
        service kspm_analyzer start
    fi
else 
    install_kspm_analyzer
fi



