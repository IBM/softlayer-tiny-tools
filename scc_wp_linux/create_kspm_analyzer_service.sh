#!/bin/bash

# Service name and description
SERVICE_NAME="kspm-analyzer"
SERVICE_DESC="KSPM Analyzer Service"

# Path to your program
PROGRAM_PATH="/bin/kspm-analyzer"

# Service script path
SERVICE_SCRIPT="/etc/init.d/$SERVICE_NAME"

# Create the service script
create_service_script() {
    echo "Creating KSPM Analyzer service script..."
    cat << EOF > $SERVICE_SCRIPT
#!/bin/bash
### BEGIN INIT INFO
# Provides:          $SERVICE_NAME
# Required-Start:    \$local_fs \$network
# Required-Stop:     \$local_fs \$network
# Default-Start:     2 3 4 5
# Default-Stop:      0 1 6
# Short-Description: $SERVICE_DESC
# Description:       $SERVICE_DESC
### END INIT INFO

# Function to start the service
start() {
    echo "Starting $SERVICE_DESC..."
    $PROGRAM_PATH &
}

# Function to stop the service
stop() {
    echo "Stopping $SERVICE_DESC..."
    killall -9 kspm-analyzer
}

# Function to check the status of the service
status() {
    if pgrep kspm-analyzer >/dev/null; then
        echo "$SERVICE_DESC is running."
    else
        echo "$SERVICE_DESC is not running."
    fi
}

# Environment variable
source /etc/kspm-analyzer.env

case "\$1" in
    start)
        start
        ;;
    stop)
        stop
        ;;
    status)
        status
        ;;
    restart)
        stop
        start
        ;;
    *)
        echo "Usage: \$0 {start|stop|restart|status}"
        exit 1
        ;;
esac

exit 0
EOF

    chmod +x $SERVICE_SCRIPT
    update-rc.d $SERVICE_NAME defaults
}

# Main script logic
if [ "$EUID" -ne 0 ]; then
    echo "Please run the script as root."
    exit 1
fi

if [ -f "$SERVICE_SCRIPT" ]; then
    echo "$SERVICE_SCRIPT Service script already exists."
else
    create_service_script
    echo "$SERVICE_SCRIPT Service script created successfully."
fi
