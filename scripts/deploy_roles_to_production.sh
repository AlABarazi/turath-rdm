#!/bin/bash
#
# Deploy role setup to production (AWS ECS)
# 
# This script:
# 1. Runs aws-login (requires 2FA)
# 2. Finds running web-ui task
# 3. Copies setup script to container
# 4. Executes setup script
# 5. Displays results
#
# Usage: ./scripts/deploy_roles_to_production.sh
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Turath Production Role Deployment${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Check we're in the right directory
if [ ! -f "scripts/setup_production_roles.py" ]; then
    echo -e "${RED}Error: Must run from turath-rdm project root${NC}"
    exit 1
fi

# Step 1: AWS Login
echo -e "${YELLOW}Step 1: AWS Login (2FA required)${NC}"
echo "Changing to terraform directory for aws-login..."
cd ~/Projects/inveniordm-terraform || {
    echo -e "${RED}Error: Could not find terraform directory${NC}"
    exit 1
}

if ! command -v aws-login &> /dev/null; then
    echo -e "${RED}Error: aws-login command not found${NC}"
    exit 1
fi

echo "Running aws-login (approve on mobile device)..."
aws-login || {
    echo -e "${RED}Error: AWS login failed${NC}"
    exit 1
}

echo -e "${GREEN}✓ AWS login successful${NC}"
echo ""

# Step 2: Find running web-ui task
echo -e "${YELLOW}Step 2: Finding running web-ui task${NC}"

CLUSTER="invenio-default-cluster"
SERVICE="web-ui"

TASK_ARN=$(aws ecs list-tasks \
    --cluster "$CLUSTER" \
    --service-name "$SERVICE" \
    --desired-status RUNNING \
    --query 'taskArns[0]' \
    --output text)

if [ "$TASK_ARN" == "None" ] || [ -z "$TASK_ARN" ]; then
    echo -e "${RED}Error: No running tasks found for service $SERVICE${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Found task: ${TASK_ARN}${NC}"
echo ""

# Step 3: Copy setup script to container
echo -e "${YELLOW}Step 3: Copying setup script to container${NC}"

SCRIPT_PATH="$HOME/Projects/Turath/turath-rdm/scripts/setup_production_roles.py"

if [ ! -f "$SCRIPT_PATH" ]; then
    echo -e "${RED}Error: Setup script not found at $SCRIPT_PATH${NC}"
    exit 1
fi

# Create a temporary file with the script content
TEMP_SCRIPT="/tmp/setup_production_roles.py"
cp "$SCRIPT_PATH" "$TEMP_SCRIPT"
chmod +x "$TEMP_SCRIPT"

echo -e "${GREEN}✓ Script ready for deployment${NC}"
echo ""

# Step 4: Execute setup in container
echo -e "${YELLOW}Step 4: Executing setup in production container${NC}"
echo -e "${BLUE}This will:${NC}"
echo "  - Create admin and curator roles"
echo "  - Assign permissions to admin role"
echo "  - Verify admin@turath-project.com has access"
echo ""
echo -e "${YELLOW}Press Enter to continue or Ctrl+C to cancel...${NC}"
read -r

echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}PRODUCTION ROLE SETUP OUTPUT${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Execute the script in the container
# We need to:
# 1. Copy the script content into the container
# 2. Execute it with pipenv run python

aws ecs execute-command \
    --cluster "$CLUSTER" \
    --task "$TASK_ARN" \
    --container app \
    --interactive \
    --command "bash -c 'cat > /tmp/setup_production_roles.py << '\''EOFSCRIPT'\''
$(cat "$TEMP_SCRIPT")
EOFSCRIPT
chmod +x /tmp/setup_production_roles.py
cd /opt/invenio/var/instance
pipenv run python /tmp/setup_production_roles.py
rm /tmp/setup_production_roles.py
'"

SETUP_EXIT_CODE=$?

echo ""
echo -e "${BLUE}========================================${NC}"

if [ $SETUP_EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}✓ Role setup completed successfully!${NC}"
    echo ""
    echo -e "${GREEN}Next steps:${NC}"
    echo "  1. Test admin access: https://invenio.turath-project.com/administration"
    echo "  2. Create curator user: ./scripts/create_curator_user.py curator@turath-project.com"
    echo "  3. Collect proof screenshots for deliverable"
else
    echo -e "${RED}✗ Role setup failed (exit code: $SETUP_EXIT_CODE)${NC}"
    echo ""
    echo -e "${YELLOW}Troubleshooting:${NC}"
    echo "  1. Check CloudWatch logs: aws logs tail /invenio-default/web-ui --since 5m"
    echo "  2. Verify database connectivity in container"
    echo "  3. Try manual execution: aws ecs execute-command ..."
fi

echo -e "${BLUE}========================================${NC}"
echo ""

# Cleanup
rm -f "$TEMP_SCRIPT"

exit $SETUP_EXIT_CODE
