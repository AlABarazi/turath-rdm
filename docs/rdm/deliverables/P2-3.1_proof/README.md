# P2-3.1 Proof Package

**Deliverable**: User Roles & Permissions - Proof of Implementation  
**Date**: February 2026  
**Production Site**: https://invenio.turath-project.com

## Overview

This directory contains proof that the P2-3.1 deliverable ("Refine User Roles & Permissions") has been successfully implemented on the production system.

## Required Evidence

### 1. Role Creation Logs ✅

**File**: `deployment_log.txt`

Output from running `./scripts/deploy_roles_to_production.sh` showing:
- Admin role created
- Curator role created
- Permissions assigned to admin role
- admin@turath-project.com verified

**How to generate**:
```bash
cd ~/Projects/Turath/turath-rdm
./scripts/deploy_roles_to_production.sh 2>&1 | tee docs/rdm/deliverables/P2-3.1_proof/deployment_log.txt
```

---

### 2. Admin Panel Access Screenshot ✅

**File**: `admin_panel_access.png`

Screenshot showing:
- URL: `https://invenio.turath-project.com/administration`
- User logged in as: admin@turath-project.com
- Admin panel visible (proves superuser-access works)

**How to capture**:
1. Open https://invenio.turath-project.com/login
2. Login as admin@turath-project.com
3. Navigate to /administration
4. Take screenshot showing URL bar + admin panel
5. Save as `admin_panel_access.png`

---

### 3. Permission Denial Screenshot ✅

**File**: `non_admin_403_error.png`

Screenshot showing:
- URL: `https://invenio.turath-project.com/administration`
- User logged in as: curator@turath-project.com (or public user)
- 403 Forbidden error OR redirect to login
- Proves role-based access control is working

**How to capture**:
1. Logout from admin account
2. Login as curator OR public user
3. Try to access /administration
4. Take screenshot of 403 error
5. Save as `non_admin_403_error.png`

---

### 4. API Permission Tests ✅

**File**: `api_permission_tests.txt`

Command-line output showing:
- Admin user can access protected endpoints (200 OK)
- Non-admin user gets 403 on protected endpoints
- Role enforcement at API level

**How to generate**:
```bash
# Test admin access (should succeed)
echo "=== Testing Admin Access ===" > api_tests.txt
curl -k -H "Authorization: Bearer $ADMIN_TOKEN" \
  https://invenio.turath-project.com/api/user/me \
  >> api_tests.txt 2>&1

# Test curator access (should succeed for records)
echo -e "\n=== Testing Curator Access ===" >> api_tests.txt
curl -k -H "Authorization: Bearer $CURATOR_TOKEN" \
  https://invenio.turath-project.com/api/records?size=1 \
  >> api_tests.txt 2>&1

# Test public access to admin endpoint (should fail)
echo -e "\n=== Testing Public Access to Admin Endpoint ===" >> api_tests.txt
curl -k https://invenio.turath-project.com/administration \
  >> api_tests.txt 2>&1

mv api_tests.txt docs/rdm/deliverables/P2-3.1_proof/api_permission_tests.txt
```

---

### 5. Role Verification Report ✅

**File**: `role_verification.txt`

Output from InvenioRDM showing:
- List of all roles in system
- Users assigned to each role
- Permissions granted to each role

**How to generate**:
```bash
# Run in production container
aws ecs execute-command --cluster invenio-default-cluster \
  --task <TASK_ARN> --container app --interactive \
  --command "bash -c '
cd /opt/invenio/var/instance
echo \"=== Roles in System ===\" > /tmp/role_verification.txt
pipenv run invenio roles list >> /tmp/role_verification.txt
echo -e \"\\n=== Admin Role Members ===\" >> /tmp/role_verification.txt
pipenv run invenio access show role admin >> /tmp/role_verification.txt
cat /tmp/role_verification.txt
'"

# Copy output to local file
```

---

## Checklist for Milestone Submission

- [ ] `deployment_log.txt` - Role setup execution output
- [ ] `admin_panel_access.png` - Admin user accessing /administration
- [ ] `non_admin_403_error.png` - Non-admin denied access
- [ ] `api_permission_tests.txt` - API-level permission enforcement
- [ ] `role_verification.txt` - System role verification report
- [ ] Parent document: `../P2-3.1_user_roles_permissions.md`

---

## Summary for Client/Reviewer

**What was delivered**:
1. **Formal role structure** documented in `P2-3.1_user_roles_permissions.md`
2. **Production deployment** of admin and curator roles
3. **Backend enforcement** - all permissions enforced at API level
4. **Zero UI changes** - custom frontend works as-is

**How it works**:
- System Administrator (admin@turath-project.com): Full access via `/administration` panel
- Curator: API access for record creation/editing
- Public: Read-only access

**Why no "Edit" buttons needed**:
- Custom Turath frontend already omits default InvenioRDM buttons
- All permissions enforced by backend (Flask/REST API)
- Admin panel available for admin users only

**Production URL**: https://invenio.turath-project.com

---

## Verification Commands

### Quick Health Check
```bash
# Check site is up
curl -k -I https://invenio.turath-project.com/

# Check admin endpoint (should redirect to login or show panel)
curl -k -I https://invenio.turath-project.com/administration
```

### Verify Roles in Production
```bash
# Connect to production container
TASK_ARN=$(aws ecs list-tasks --cluster invenio-default-cluster \
  --service-name web-ui --query 'taskArns[0]' --output text)

aws ecs execute-command --cluster invenio-default-cluster \
  --task "$TASK_ARN" --container app --interactive \
  --command "/bin/bash"

# Inside container:
cd /opt/invenio/var/instance
pipenv run invenio roles list
pipenv run invenio access show role admin
```

---

## Contact

For questions about this deliverable:
- Documentation: `/docs/rdm/deliverables/P2-3.1_user_roles_permissions.md`
- Scripts: `/scripts/setup_production_roles.py`
- Deployment: `/scripts/deploy_roles_to_production.sh`
