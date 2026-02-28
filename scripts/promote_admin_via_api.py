#!/usr/bin/env python3
"""
Promote admin@turath.com using InvenioRDM REST API
Run from local machine
"""

import requests
import sys

# Configuration
BASE_URL = "https://invenio.turath-project.com"
ADMIN_EMAIL = "admin@turath.com"

# Note: InvenioRDM doesn't expose role management via REST API by default
# We need to use the database approach inside the container
# OR create a custom endpoint for this

print("❌ InvenioRDM doesn't expose user role management via REST API")
print("Role assignment must be done via:")
print("  1. CLI commands inside container (invenio roles add)")
print("  2. Direct database access (which we're doing)")
print("  3. Custom admin endpoint (would require code deployment)")
print()
print("The manual container command is the correct approach.")
print("Please run the command I provided in the container shell.")
