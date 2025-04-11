#!/bin/bash

# Get directory of the current script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"

# Color codes for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Running comprehensive frontend container diagnostics...${NC}"

# Check container status
echo -e "\n${YELLOW}1. Container Status:${NC}"
if docker ps | grep -q "netraven-frontend-dev"; then
    echo -e "${GREEN}Container is running.${NC}"
    # Get container details
    echo -e "${YELLOW}Container details:${NC}"
    docker inspect --format='ID: {{.Id}}\nState: {{.State.Status}}\nStarted: {{.State.StartedAt}}\nHealth: {{.State.Health.Status}}' netraven-frontend-dev
else
    echo -e "${RED}Container is not running!${NC}"
    if docker ps -a | grep -q "netraven-frontend-dev"; then
        echo -e "${RED}Container exists but is not active. Exit code and status:${NC}"
        docker inspect --format='Exit Code: {{.State.ExitCode}}\nError: {{.State.Error}}\nFinished: {{.State.FinishedAt}}' netraven-frontend-dev
    fi
fi

# Show container logs
echo -e "\n${YELLOW}2. Container Logs:${NC}"
docker logs netraven-frontend-dev 2>&1 | tail -n 30

# Check network configuration
echo -e "\n${YELLOW}3. Network Configuration:${NC}"
echo -e "${YELLOW}Container network settings:${NC}"
docker inspect --format='{{range $k, $v := .NetworkSettings.Ports}}{{$k}} -> {{range $v}}{{.HostIp}}:{{.HostPort}}{{end}}{{end}}' netraven-frontend-dev

# Check host ports
echo -e "\n${YELLOW}4. Host Port Status:${NC}"
if command -v netstat &>/dev/null; then
    echo -e "${YELLOW}Checking if port 5173 is open on the host:${NC}"
    netstat -tuln | grep 5173
elif command -v ss &>/dev/null; then
    echo -e "${YELLOW}Checking if port 5173 is open on the host:${NC}"
    ss -tuln | grep 5173
else
    echo -e "${YELLOW}Neither netstat nor ss available. Please install one to check port status.${NC}"
fi

# Check container file system
echo -e "\n${YELLOW}5. Container File System:${NC}"
echo -e "${YELLOW}Checking if node_modules exists in the container:${NC}"
docker exec -it netraven-frontend-dev ls -la /app | grep node_modules || echo -e "${RED}node_modules not found!${NC}"
echo -e "${YELLOW}Checking if package.json exists:${NC}"
docker exec -it netraven-frontend-dev ls -la /app | grep package.json || echo -e "${RED}package.json not found!${NC}"
echo -e "${YELLOW}Checking vite.config.js:${NC}"
docker exec -it netraven-frontend-dev cat /app/vite.config.js | grep -A 10 "server:"

# Try accessing the application
echo -e "\n${YELLOW}6. Application Access:${NC}"
echo -e "${YELLOW}Attempting to fetch homepage (HTTP):${NC}"
curl -v -m 5 http://localhost:5173 2>&1 | grep -E '(Connected to|Failed to connect)'

echo -e "\n${YELLOW}Troubleshooting Recommendations:${NC}"
echo -e "1. Check if Vite is binding correctly to 0.0.0.0 (all interfaces)"
echo -e "2. Ensure firewall isn't blocking port 5173"
echo -e "3. Try rebuilding with: docker-compose down && docker-compose build --no-cache frontend && docker-compose up -d"
echo -e "4. Enter the container to debug: docker exec -it netraven-frontend-dev /bin/sh"
echo -e "5. Check if the 'dev' script in package.json is configured correctly"

chmod +x "$ROOT_DIR/setup/diagnose_frontend.sh"
