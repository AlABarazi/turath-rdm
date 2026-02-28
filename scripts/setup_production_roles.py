#!/usr/bin/env python3
"""
Production role setup for Turath InvenioRDM.
Designed to run in AWS ECS containers.

This script:
1. Creates admin and curator roles
2. Assigns permissions to roles
3. Verifies admin@turath-project.com has proper permissions
4. Outputs verification report

Safe to run multiple times (idempotent).
"""

import os
import sys
import subprocess
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ProductionRoleSetup:
    """Handle role setup for production InvenioRDM."""
    
    def __init__(self):
        """Initialize the setup."""
        # In ECS, we're already in /opt/invenio/var/instance
        self.cmd_prefix = ['pipenv', 'run', 'invenio']
        logger.info("Production role setup initialized")
    
    def run_invenio(self, args: list, ignore_errors: bool = False) -> tuple:
        """
        Run invenio command with proper error handling.
        
        Args:
            args: Command arguments for invenio
            ignore_errors: If True, don't raise exception on command failure
            
        Returns:
            Tuple of (success: bool, output: str)
        """
        cmd = self.cmd_prefix + args
        logger.debug(f"Running command: {' '.join(cmd)}")
        
        try:
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                check=not ignore_errors,
                env=os.environ.copy(),
            )
            
            if result.returncode == 0:
                logger.debug(f"Command succeeded: {' '.join(cmd)}")
                return (True, result.stdout.strip())
            else:
                logger.warning(f"Command failed: {' '.join(cmd)}")
                logger.warning(f"Error output: {result.stderr.strip()}")
                return (False, result.stderr.strip())
                
        except subprocess.CalledProcessError as e:
            logger.error(f"Command failed: {' '.join(cmd)}")
            logger.error(f"Return code: {e.returncode}")
            logger.error(f"Error output: {e.stderr.strip()}")
            if not ignore_errors:
                raise
            return (False, e.stderr.strip())
    
    def create_role(self, role_name: str, description: str) -> bool:
        """Create a role if it doesn't exist."""
        logger.info(f"Ensuring '{role_name}' role exists...")
        
        success, output = self.run_invenio(
            ['roles', 'create', role_name, '-d', description],
            ignore_errors=True
        )
        
        if success:
            logger.info(f"✓ Role '{role_name}' created successfully")
            return True
        elif "already exists" in output.lower() or "duplicate" in output.lower():
            logger.info(f"✓ Role '{role_name}' already exists")
            return True
        else:
            logger.warning(f"✗ Failed to create role '{role_name}': {output}")
            return False
    
    def assign_permission_to_role(self, permission: str, role: str) -> bool:
        """Assign permission to role."""
        logger.info(f"Assigning '{permission}' to role '{role}'...")
        
        success, output = self.run_invenio(
            ['access', 'allow', permission, 'role', role],
            ignore_errors=True
        )
        
        if success:
            logger.info(f"✓ Permission '{permission}' granted to role '{role}'")
            return True
        elif "already exists" in output.lower() or "already granted" in output.lower():
            logger.info(f"✓ Permission '{permission}' already granted to role '{role}'")
            return True
        else:
            logger.warning(f"✗ Failed to grant permission: {output}")
            return False
    
    def assign_user_to_role(self, email: str, role: str) -> bool:
        """Assign user to role."""
        logger.info(f"Adding user '{email}' to role '{role}'...")
        
        success, output = self.run_invenio(
            ['roles', 'add', email, role],
            ignore_errors=True
        )
        
        if success:
            logger.info(f"✓ User '{email}' added to role '{role}'")
            return True
        elif "already" in output.lower():
            logger.info(f"✓ User '{email}' already in role '{role}'")
            return True
        else:
            logger.warning(f"✗ Failed to add user to role: {output}")
            return False
    
    def verify_user_exists(self, email: str) -> bool:
        """Check if user exists."""
        logger.info(f"Verifying user '{email}' exists...")
        
        success, output = self.run_invenio(
            ['users', 'list'],
            ignore_errors=True
        )
        
        if success and email in output:
            logger.info(f"✓ User '{email}' exists")
            return True
        else:
            logger.warning(f"✗ User '{email}' not found")
            return False
    
    def setup_admin_role(self) -> bool:
        """Set up admin role and permissions."""
        logger.info("=" * 60)
        logger.info("Setting up ADMIN role...")
        logger.info("=" * 60)
        
        # Create admin role
        if not self.create_role('admin', 'Administrator role'):
            return False
        
        # Assign permissions to admin role
        permissions = [
            'superuser-access',
            'administration-access'
        ]
        
        for permission in permissions:
            if not self.assign_permission_to_role(permission, 'admin'):
                logger.warning(f"Failed to assign {permission}, continuing...")
        
        # Verify and assign admin@turath-project.com to admin role
        admin_email = 'admin@turath-project.com'
        if self.verify_user_exists(admin_email):
            self.assign_user_to_role(admin_email, 'admin')
        else:
            logger.warning(f"Admin user {admin_email} does not exist - manual creation needed")
        
        logger.info("✓ Admin role setup complete")
        return True
    
    def setup_curator_role(self) -> bool:
        """Set up curator role and permissions."""
        logger.info("=" * 60)
        logger.info("Setting up CURATOR role...")
        logger.info("=" * 60)
        
        # Create curator role
        if not self.create_role('curator', 'Content curator role'):
            return False
        
        # Note: Curators get permissions through record ownership
        # and community roles, not global permissions
        logger.info("✓ Curator role created (permissions via record ownership)")
        
        logger.info("✓ Curator role setup complete")
        return True
    
    def generate_report(self) -> None:
        """Generate verification report."""
        logger.info("=" * 60)
        logger.info("VERIFICATION REPORT")
        logger.info("=" * 60)
        
        # List all roles
        logger.info("\n--- Roles in System ---")
        success, output = self.run_invenio(['roles', 'list'], ignore_errors=True)
        if success:
            print(output)
        
        # Show admin role permissions
        logger.info("\n--- Admin Role Permissions ---")
        success, output = self.run_invenio(
            ['access', 'show', 'role', 'admin'], 
            ignore_errors=True
        )
        if success:
            print(output)
        else:
            logger.info("(Use 'invenio access show role admin' to view)")
        
        logger.info("\n" + "=" * 60)
        logger.info("Setup complete! Roles are ready for use.")
        logger.info("=" * 60)
    
    def setup(self) -> bool:
        """Run the complete setup process."""
        logger.info("Starting production role setup...")
        logger.info(f"Environment: {os.environ.get('INVENIO_INSTANCE_PATH', 'default')}")
        
        try:
            # Setup admin role
            if not self.setup_admin_role():
                logger.error("Admin role setup failed")
                return False
            
            # Setup curator role
            if not self.setup_curator_role():
                logger.error("Curator role setup failed")
                return False
            
            # Generate verification report
            self.generate_report()
            
            logger.info("✓ Production role setup completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"✗ Setup failed with exception: {str(e)}")
            import traceback
            traceback.print_exc()
            return False


def main():
    """Main entry point."""
    print("\n" + "=" * 60)
    print("Turath InvenioRDM - Production Role Setup")
    print("=" * 60 + "\n")
    
    try:
        setup = ProductionRoleSetup()
        success = setup.setup()
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        logger.info("Setup interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
