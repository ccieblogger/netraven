#!/bin/bash

# NetRaven Services Startup Script
# This script starts all required services for the NetRaven application

set -e  # Exit on any errors

# Directory paths
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
LOG_DIR="$ROOT_DIR/logs"
PID_DIR="$ROOT_DIR/.pids"

# Create directories if they don't exist
mkdir -p "$LOG_DIR"
mkdir -p "$PID_DIR"

# Color codes for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Print header
echo -e "${GREEN}==========================================${NC}"
echo -e "${GREEN}     NetRaven Services Startup Script     ${NC}"
echo -e "${GREEN}==========================================${NC}"

# Check if Poetry is installed
if ! command -v poetry &> /dev/null; then
    echo -e "${RED}Poetry is not installed. Please install it first.${NC}"
    exit 1
fi

# Check for PostgreSQL and Redis
echo -e "\n${YELLOW}Checking required services...${NC}"

if ! sudo systemctl is-active --quiet postgresql; then
    echo -e "${YELLOW}Starting PostgreSQL...${NC}"
    sudo systemctl start postgresql
    if [ $? -ne 0 ]; then
        echo -e "${RED}Failed to start PostgreSQL. Aborting.${NC}"
        exit 1
    fi
fi
echo -e "${GREEN}PostgreSQL is running.${NC}"

if ! sudo systemctl is-active --quiet redis-server; then
    echo -e "${YELLOW}Starting Redis...${NC}"
    sudo systemctl start redis-server
    if [ $? -ne 0 ]; then
        echo -e "${RED}Failed to start Redis. Aborting.${NC}"
        exit 1
    fi
fi
echo -e "${GREEN}Redis is running.${NC}"

# Create default admin user if it doesn't exist
echo -e "\n${YELLOW}Checking for default admin user...${NC}"
cd "$ROOT_DIR"

# Python script to create admin user
cat > "$ROOT_DIR/setup/create_admin.py" <<EOF
import sys
from sqlalchemy.orm import Session
from netraven.db.session import get_db
from netraven.db.models.user import User
from netraven.api.auth import get_password_hash

def create_admin_user():
    try:
        db = next(get_db())
        existing_admin = db.query(User).filter(User.username == "admin").first()
        
        if existing_admin:
            print("Admin user already exists.")
            return 0
            
        new_admin = User(
            username="admin",
            hashed_password=get_password_hash("admin123"),
            is_active=True,
            role="admin",
            email="admin@netraven.local"
        )
        
        db.add(new_admin)
        db.commit()
        print("Admin user created successfully.")
        return 0
    except Exception as e:
        print(f"Error creating admin user: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(create_admin_user())
EOF

chmod +x "$ROOT_DIR/setup/create_admin.py"
echo -e "${YELLOW}Creating default admin user (username: admin, password: admin123)...${NC}"
if poetry run python "$ROOT_DIR/setup/create_admin.py"; then
    echo -e "${GREEN}Admin user created or already exists.${NC}"
else
    echo -e "${RED}Failed to create admin user.${NC}"
    # Continue anyway, as the user might already exist
fi

# Start services function
start_service() {
    local service_name=$1
    local command=$2
    local log_file=$3
    local pid_file=$4

    echo -e "\n${YELLOW}Starting $service_name...${NC}"
    
    # Check if service is already running
    if [ -f "$pid_file" ] && ps -p $(cat "$pid_file") > /dev/null; then
        echo -e "${YELLOW}$service_name is already running with PID $(cat $pid_file).${NC}"
        return 0
    fi
    
    # Start the service
    nohup $command > "$log_file" 2>&1 &
    pid=$!
    echo $pid > "$pid_file"
    
    # Wait briefly to make sure the process didn't immediately die
    sleep 2
    if ps -p $pid > /dev/null; then
        echo -e "${GREEN}$service_name started successfully with PID $pid.${NC}"
        echo -e "${GREEN}Logs available at: $log_file${NC}"
        return 0
    else
        echo -e "${RED}Failed to start $service_name. Check logs at $log_file${NC}"
        return 1
    fi
}

# Start API Service
API_LOG="$LOG_DIR/api.log"
API_PID="$PID_DIR/api.pid"
start_service "API Service" "poetry run uvicorn netraven.api.main:app --host 0.0.0.0 --port 8000" "$API_LOG" "$API_PID"

# Start Scheduler Service
SCHEDULER_LOG="$LOG_DIR/scheduler.log"
SCHEDULER_PID="$PID_DIR/scheduler.pid"
start_service "Scheduler Service" "poetry run python -m netraven.scheduler.scheduler_runner" "$SCHEDULER_LOG" "$SCHEDULER_PID"

# Frontend information (now containerized)
echo -e "\n${YELLOW}Frontend information:${NC}"
echo -e "The frontend is now containerized and can be started separately using Docker."
echo -e "${GREEN}To start the frontend development environment:${NC}"
echo -e "cd $ROOT_DIR && docker-compose up -d"
echo -e "${GREEN}To start the frontend production environment:${NC}"
echo -e "cd $ROOT_DIR && docker-compose -f docker-compose.prod.yml up -d"

# Print summary
echo -e "\n${GREEN}==========================================${NC}"
echo -e "${GREEN}     NetRaven Services Started             ${NC}"
echo -e "${GREEN}==========================================${NC}"
echo -e "API running at: http://localhost:8000/api/docs"
echo -e "Frontend (when started with Docker):"
echo -e " - Development: http://localhost:5173"
echo -e " - Production: http://localhost:80"
echo -e "\nLogin with: username='admin', password='admin123'"
echo -e "\nTo stop the services, run: $ROOT_DIR/setup/stop_netraven.sh"
echo -e "${GREEN}==========================================${NC}"

# Create stop script for convenience
cat > "$ROOT_DIR/setup/stop_netraven.sh" <<EOF
#!/bin/bash

# NetRaven Services Stop Script
SCRIPT_DIR="\$(cd "\$(dirname "\${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="\$(dirname "\$SCRIPT_DIR")"
PID_DIR="\$ROOT_DIR/.pids"

echo "Stopping NetRaven services..."

# Function to stop a service
stop_service() {
    local service_name=\$1
    local pid_file="\$PID_DIR/\$service_name.pid"
    
    if [ -f "\$pid_file" ]; then
        pid=\$(cat "\$pid_file")
        if ps -p \$pid > /dev/null; then
            echo "Stopping \$service_name (PID \$pid)..."
            kill \$pid
            sleep 2
            # Force kill if still running
            if ps -p \$pid > /dev/null; then
                echo "Force stopping \$service_name..."
                kill -9 \$pid
            fi
        else
            echo "\$service_name is not running."
        fi
        rm "\$pid_file"
    else
        echo "\$service_name is not running."
    fi
}

# Only stop backend services
stop_service "scheduler"
stop_service "api"

echo "All NetRaven backend services stopped."
echo "To stop the frontend containers:"
echo "- Development environment: docker-compose down"
echo "- Production environment: docker-compose -f docker-compose.prod.yml down"
EOF

chmod +x "$ROOT_DIR/setup/stop_netraven.sh"

exit 0