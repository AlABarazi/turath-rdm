-- Assign admin role to admin@turath.com
-- Run this against production database

-- Get user and role IDs, then create the mapping
INSERT INTO accounts_userrole (user_id, role_id)
SELECT 
    u.id as user_id,
    r.id as role_id
FROM accounts_user u
CROSS JOIN accounts_role r
WHERE u.email = 'admin@turath.com'
  AND r.name = 'admin'
  AND NOT EXISTS (
    SELECT 1 FROM accounts_userrole ur 
    WHERE ur.user_id = u.id AND ur.role_id = r.id
  );

-- Verify the assignment
SELECT 
    u.email,
    r.name as role
FROM accounts_user u
JOIN accounts_userrole ur ON u.id = ur.user_id
JOIN accounts_role r ON ur.role_id = r.id
WHERE u.email = 'admin@turath.com';
