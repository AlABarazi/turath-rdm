#!/bin/bash
# Simple admin promotion - run this directly

TASK_ARN=$(aws ecs list-tasks --cluster invenio-default-cluster --service-name web-ui --desired-status RUNNING --query 'taskArns[0]' --output text)

echo "Task: $TASK_ARN"
echo "Promoting admin@turath.com..."

# Create the Python script inline and execute it
aws ecs execute-command \
  --cluster invenio-default-cluster \
  --task "$TASK_ARN" \
  --container app \
  --interactive \
  --command "/bin/bash"

# Then inside the container, run these commands:
# cd /opt/invenio/var/instance
# pipenv run python << 'EOF'
# from invenio_app.factory import create_app
# from invenio_db import db
# app = create_app()
# with app.app_context():
#     user = db.session.execute(db.text("SELECT id FROM accounts_user WHERE email='admin@turath.com'")).first()
#     role = db.session.execute(db.text("SELECT id FROM accounts_role WHERE name='admin'")).first()
#     if user and role:
#         db.session.execute(db.text("INSERT INTO accounts_userrole (user_id, role_id) VALUES (:u, :r) ON CONFLICT DO NOTHING"), {"u": user[0], "r": role[0]})
#         db.session.commit()
#         print("SUCCESS: Admin role assigned!")
#         roles = db.session.execute(db.text("SELECT r.name FROM accounts_role r JOIN accounts_userrole ur ON r.id=ur.role_id WHERE ur.user_id=:u"), {"u": user[0]}).fetchall()
#         print(f"Roles: {[r[0] for r in roles]}")
#     else:
#         print("ERROR: Not found")
# EOF
# exit
