#!/bin/bash

# Service name and description
SERVICE_NAME="host_analyzer"
SERVICE_DESC="Host Analyzer Service"

# Path to your program
PROGRAM_PATH="/usr/bin/host_analyzer"

# Service script path
SERVICE_SCRIPT="/etc/init.d/$SERVICE_NAME"

# Create the service script
create_service_script() {
    echo "Creating service script..."
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
    killall -9 host_analyzer
}

case "\$1" in
    start)
        start
        ;;
    stop)
        stop
        ;;
    restart)
        stop
        start
        ;;
    *)
        echo "Usage: \$0 {start|stop|restart}"
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
