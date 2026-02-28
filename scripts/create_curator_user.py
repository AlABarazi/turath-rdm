#!/usr/bin/env python3
"""
Create curator user for Turath InvenioRDM production.
Designed to run in AWS ECS containers.

Usage:
    pipenv run python create_curator_user.py <email> [password]

Example:
    pipenv run python create_curator_user.py curator@turath-project.com
    (will prompt for password if not provided)

Safe to run multiple times (idempotent).
"""

import os
import sys
import subprocess
import logging
import getpass

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class CuratorUserCreator:
    """Create curator users in production."""
    
    def __init__(self):
        """Initialize the creator."""
        self.cmd_prefix = ['pipenv', 'run', 'invenio']
        logger.info("Curator user creator initialized")
    
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
    
    def validate_email(self, email: str) -> bool:
        """Basic email validation."""
        if '@' not in email or '.' not in email:
            logger.error(f"Invalid email format: {email}")
            return False
        return True
    
    def create_user(self, email: str, password: str) -> bool:
        """Create user account."""
        logger.info(f"Creating user account for {email}...")
        
        success, output = self.run_invenio(
            ['users', 'create', email, '--password', password, '--active', '--confirm'],
            ignore_errors=True
        )
        
        if success:
            logger.info(f"✓ User {email} created successfully")
            return True
        elif "already exists" in output.lower() or "duplicate" in output.lower():
            logger.info(f"✓ User {email} already exists")
            return True
        else:
            logger.error(f"✗ Failed to create user: {output}")
            return False
    
    def assign_curator_role(self, email: str) -> bool:
        """Assign curator role to user."""
        logger.info(f"Assigning curator role to {email}...")
        
        success, output = self.run_invenio(
            ['roles', 'add', email, 'curator'],
            ignore_errors=True
        )
        
        if success:
            logger.info(f"✓ Curator role assigned to {email}")
            return True
        elif "already" in output.lower():
            logger.info(f"✓ User {email} already has curator role")
            return True
        else:
            logger.error(f"✗ Failed to assign role: {output}")
            return False
    
    def verify_user(self, email: str) -> None:
        """Verify user was created correctly."""
        logger.info(f"\nVerifying user {email}...")
        
        # List user
        success, output = self.run_invenio(
            ['users', 'list'],
            ignore_errors=True
        )
        
        if success and email in output:
            logger.info(f"✓ User {email} found in system")
        else:
            logger.warning(f"✗ User {email} not found in user list")
    
    def create_curator(self, email: str, password: str) -> bool:
        """Complete curator user creation process."""
        logger.info("=" * 60)
        logger.info(f"Creating Curator User: {email}")
        logger.info("=" * 60)
        
        # Validate email
        if not self.validate_email(email):
            return False
        
        # Create user
        if not self.create_user(email, password):
            return False
        
        # Assign curator role
        if not self.assign_curator_role(email):
            return False
        
        # Verify
        self.verify_user(email)
        
        logger.info("=" * 60)
        logger.info(f"✓ Curator user {email} is ready!")
        logger.info("=" * 60)
        logger.info("\nNext steps:")
        logger.info(f"  1. User can login at: https://invenio.turath-project.com/login")
        logger.info(f"  2. User email: {email}")
        logger.info(f"  3. User has 'curator' role for API access")
        logger.info(f"  4. Generate API token: invenio tokens create -n 'Curator Token' -u {email}")
        
        return True


def main():
    """Main entry point."""
    print("\n" + "=" * 60)
    print("Turath InvenioRDM - Create Curator User")
    print("=" * 60 + "\n")
    
    # Parse arguments
    if len(sys.argv) < 2:
        print("Usage: python create_curator_user.py <email> [password]")
        print("\nExample:")
        print("  python create_curator_user.py curator@turath-project.com")
        print("  python create_curator_user.py curator@turath-project.com SecurePass123")
        sys.exit(1)
    
    email = sys.argv[1]
    
    # Get password (from arg or prompt)
    if len(sys.argv) >= 3:
        password = sys.argv[2]
    else:
        password = getpass.getpass(f"Enter password for {email}: ")
        password_confirm = getpass.getpass("Confirm password: ")
        
        if password != password_confirm:
            logger.error("Passwords do not match!")
            sys.exit(1)
    
    if len(password) < 6:
        logger.error("Password must be at least 6 characters")
        sys.exit(1)
    
    # Create curator
    try:
        creator = CuratorUserCreator()
        success = creator.create_curator(email, password)
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        logger.info("\nInterrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
