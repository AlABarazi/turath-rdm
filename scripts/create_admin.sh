#!/bin/bash

# Ensure we run from the project root and use the local virtualenv
cd "$(dirname "$0")/.." || exit 1
# Activate venv explicitly to avoid Homebrew/system Python
source .venv/bin/activate

# Make the script exit on any error
# set -e # Temporarily disable exit on error to handle existing user/role

echo "Setting up admin user and permissions..."

# Try to create the admin role (will fail gracefully if exists)
echo "Ensuring admin role exists..."
invenio roles create admin -d "Administrator role" || echo "Admin role likely already exists."

# Try to create the user (will fail if exists)
echo "Ensuring admin user exists..."
if ! invenio users create admin@turath.com --password 123456 --active --confirm; then
    echo "User admin@turath.com likely already exists. Attempting to activate..."
    # Attempt to activate existing user (might need adjustment based on actual command)
    invenio users activate admin@turath.com || echo "Failed to activate user - might already be active."
fi

# Assign permissions and role (should be idempotent)
echo "Assigning permissions and role..."
# Grant administration-access system role need
invenio access allow administration-access user admin@turath.com
# Add user to the admin role
invenio roles add admin@turath.com admin
# Grant superuser-access to the admin role
invenio access allow superuser-access role admin

echo "$(tput setaf 2)✓ Admin setup process completed (check logs for any specific errors).$(tput sgr0)"

# Re-enable exit on error if needed later in a larger script
# set -e
