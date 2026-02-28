#!/usr/bin/env python3
"""
Assign admin role using the Flask app's working database connection.
Run this in the container where the web app is running.

Usage:
  cd /opt/invenio/var/instance
  python /tmp/assign_admin_via_webapp.py
"""

from invenio_app.factory import create_app
from invenio_db import db

app = create_app()

with app.app_context():
    print("=== Assigning Admin Role to admin@turath.com ===")
    
    # Get user ID
    user_result = db.session.execute(
        db.text("SELECT id, email FROM accounts_user WHERE email = 'admin@turath.com'")
    )
    user_row = user_result.first()
    
    if not user_row:
        print("ERROR: User admin@turath.com not found!")
        print("Please register this user via the website first.")
        exit(1)
    
    user_id, email = user_row
    print(f"✓ Found user: {email} (ID: {user_id})")
    
    # Get admin role ID
    role_result = db.session.execute(
        db.text("SELECT id, name FROM accounts_role WHERE name = 'admin'")
    )
    role_row = role_result.first()
    
    if not role_row:
        print("ERROR: Admin role not found!")
        print("Run setup_production_roles.py first to create roles.")
        exit(1)
    
    role_id, role_name = role_row
    print(f"✓ Found role: {role_name} (ID: {role_id})")
    
    # Check if already assigned
    check_result = db.session.execute(
        db.text("""
            SELECT 1 FROM accounts_userrole 
            WHERE user_id = :uid AND role_id = :rid
        """),
        {"uid": user_id, "rid": role_id}
    )
    
    if check_result.first():
        print("✓ User already has admin role!")
    else:
        # Assign role
        db.session.execute(
            db.text("""
                INSERT INTO accounts_userrole (user_id, role_id) 
                VALUES (:uid, :rid)
            """),
            {"uid": user_id, "rid": role_id}
        )
        db.session.commit()
        print("✓ Admin role assigned successfully!")
    
    print("\n=== Verification ===")
    verify_result = db.session.execute(
        db.text("""
            SELECT u.email, r.name 
            FROM accounts_user u
            JOIN accounts_userrole ur ON u.id = ur.user_id
            JOIN accounts_role r ON ur.role_id = r.id
            WHERE u.email = 'admin@turath.com'
        """)
    )
    
    roles = list(verify_result)
    if roles:
        print(f"User roles: {[(email, role) for email, role in roles]}")
    else:
        print("No roles found (this shouldn't happen)")
    
    print("\n✅ Done! Try accessing:")
    print("   https://invenio.turath-project.com/administration")
