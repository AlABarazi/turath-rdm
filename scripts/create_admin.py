#!/usr/bin/env python3
"""
Admin setup script for Turath InvenioRDM.
Creates admin user and assigns necessary permissions.
"""

import os
import sys
import subprocess
import logging
from pathlib import Path
from typing import List, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class InvenioAdminSetup:
    """Handle admin user setup for Invenio RDM."""
    
    def __init__(self):
        """Initialize the admin setup."""
        # Change to project root
        script_dir = Path(__file__).parent
        self.project_root = script_dir.parent
        os.chdir(self.project_root)
        
        # On macOS, ensure Homebrew libs are discoverable by the dynamic linker
        if sys.platform == 'darwin':
            dyld_fb = os.environ.get('DYLD_FALLBACK_LIBRARY_PATH', '')
            brew_lib = '/opt/homebrew/lib'
            if brew_lib not in dyld_fb.split(':'):
                os.environ['DYLD_FALLBACK_LIBRARY_PATH'] = (
                    f"{brew_lib}:{dyld_fb}" if dyld_fb else brew_lib
                )
            logger.info(
                "DYLD_FALLBACK_LIBRARY_PATH set for macOS: %s",
                os.environ.get('DYLD_FALLBACK_LIBRARY_PATH')
            )
            # Quick inline verification in this exact context
            try:
                import ctypes.util  # noqa: WPS433 (local import OK for verification)
                logger.info("cairo find_library: %s", ctypes.util.find_library('cairo'))
            except Exception as ex:  # pragma: no cover
                logger.warning("cairo verification failed: %s", ex)
        
        # Detect environment and set command prefix
        if os.getenv('PIPENV_ACTIVE'):
            self.cmd_prefix = []
            logger.info("Detected active pipenv environment")
        else:
            self.cmd_prefix = ['pipenv', 'run']
            logger.info("Using pipenv run to execute commands")
    
    def run_invenio(self, args: List[str], ignore_errors: bool = False) -> Optional[str]:
        """
        Run invenio command with proper error handling.
        
        Args:
            args: Command arguments for invenio
            ignore_errors: If True, don't raise exception on command failure
            
        Returns:
            Command output or None if failed
        """
        cmd = self.cmd_prefix + ['invenio'] + args
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
                return result.stdout.strip()
            else:
                logger.warning(f"Command failed: {' '.join(cmd)}")
                logger.warning(f"Error output: {result.stderr.strip()}")
                return None
                
        except subprocess.CalledProcessError as e:
            logger.error(f"Command failed: {' '.join(cmd)}")
            logger.error(f"Return code: {e.returncode}")
            logger.error(f"Error output: {e.stderr.strip()}")
            if not ignore_errors:
                raise
            return None
    
    def create_admin_role(self) -> bool:
        """Create admin role if it doesn't exist."""
        logger.info("Ensuring admin role exists...")
        
        result = self.run_invenio(
            ['roles', 'create', 'admin', '-d', 'Administrator role'],
            ignore_errors=True
        )
        
        if result is not None:
            logger.info("Admin role created successfully")
            return True
        else:
            logger.info("Admin role likely already exists")
            return False
    
    def create_admin_user(self) -> bool:
        """Create admin user if it doesn't exist."""
        logger.info("Ensuring admin user exists...")
        
        result = self.run_invenio([
            'users', 'create', 'admin@turath.com',
            '--password', '123456',
            '--active',
            '--confirm'
        ], ignore_errors=True)
        
        if result is not None:
            logger.info("Admin user created successfully")
            logger.info(f"User details: {result}")
            return True
        else:
            logger.info("User admin@turath.com likely already exists")
            # Try to activate existing user
            logger.info("Attempting to activate existing user...")
            activate_result = self.run_invenio([
                'users', 'activate', 'admin@turath.com'
            ], ignore_errors=True)
            
            if activate_result is not None:
                logger.info("User activated successfully")
            else:
                logger.info("Failed to activate user - might already be active")
            
            return False
    
    def assign_permissions(self) -> bool:
        """Assign admin permissions and roles."""
        logger.info("Assigning permissions and role...")
        
        success = True
        
        # Grant administration-access system role need
        logger.info("Granting administration-access...")
        result = self.run_invenio([
            'access', 'allow', 'administration-access', 
            'user', 'admin@turath.com'
        ], ignore_errors=True)
        
        if result is None:
            logger.warning("Failed to grant administration-access")
            success = False
        
        # Add user to the admin role
        logger.info("Adding user to admin role...")
        result = self.run_invenio([
            'roles', 'add', 'admin@turath.com', 'admin'
        ], ignore_errors=True)
        
        if result is not None:
            logger.info(f"Role assignment result: {result}")
        else:
            # Some environments might expect reversed order; try it as a fallback
            logger.info("Primary role add failed; trying reversed argument order (role, user)...")
            retry_result = self.run_invenio([
                'roles', 'add', 'admin', 'admin@turath.com'
            ], ignore_errors=True)
            if retry_result is not None:
                logger.info(f"Role assignment (reversed) result: {retry_result}")
            else:
                # Treat as idempotent: likely already assigned
                logger.info("Role assignment appears idempotent or user already has role; continuing")
        
        # Grant superuser-access to the admin role
        logger.info("Granting superuser-access to admin role...")
        result = self.run_invenio([
            'access', 'allow', 'superuser-access', 'role', 'admin'
        ], ignore_errors=True)
        
        if result is None:
            logger.warning("Failed to grant superuser-access")
            success = False
        
        return success
    
    def setup(self) -> bool:
        """Run the complete admin setup process."""
        logger.info("Starting admin setup process...")
        
        try:
            # Create admin role
            self.create_admin_role()
            
            # Create admin user
            self.create_admin_user()
            
            # Assign permissions
            permissions_success = self.assign_permissions()
            
            if permissions_success:
                logger.info("✓ Admin setup process completed successfully")
                return True
            else:
                logger.warning("⚠ Admin setup completed with some warnings")
                return False
                
        except Exception as e:
            logger.error(f"✗ Admin setup failed: {str(e)}")
            return False


def main():
    """Main entry point."""
    try:
        setup = InvenioAdminSetup()
        success = setup.setup()
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        logger.info("Setup interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        sys.exit(1)


if __name__ == '__main__':
    main()
