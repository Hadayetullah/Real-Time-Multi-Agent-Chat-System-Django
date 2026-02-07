"""
Django Management Command: wait_for_db
Waits for the database to be available before proceeding
Essential for Docker deployments where services start in parallel
"""

import time
from django.core.management.base import BaseCommand
from django.db import connections
from django.db.utils import OperationalError


class Command(BaseCommand):
    """
    Django command that waits for database to be available
    This prevents migrations and other DB operations from failing
    when containers start simultaneously
    """
    
    # Help text shown when running: python manage.py help wait_for_db
    help = 'Waits for database to be available'
    
    def handle(self, *args, **options):
        """
        Main command execution method
        Polls database connection until it succeeds or max attempts reached
        """
        # Print status message to console
        self.stdout.write('Waiting for database connection...')
        
        # Initialize database connection status
        db_conn = None
        
        # Maximum attempts to connect (30 attempts = ~30 seconds with 1s delay)
        max_attempts = 30
        attempt = 0
        
        # Keep trying until database is available or max attempts reached
        while not db_conn and attempt < max_attempts:
            try:
                # Attempt to get database connection
                # This will raise OperationalError if database is not ready
                db_conn = connections['default']
                
                # Try to actually use the connection
                # cursor() will fail if database is not ready
                db_conn.cursor()
                
            except OperationalError:
                # Database is not ready yet
                attempt += 1
                
                # Print waiting message with attempt number
                self.stdout.write(
                    self.style.WARNING(
                        f'Database unavailable, waiting... (attempt {attempt}/{max_attempts})'
                    )
                )
                
                # Wait 1 second before trying again
                time.sleep(1)
        
        # Check if we successfully connected or ran out of attempts
        if db_conn:
            # Success! Database is available
            self.stdout.write(
                self.style.SUCCESS('Database connection established!')
            )
        else:
            # Failed to connect after max attempts
            self.stdout.write(
                self.style.ERROR(
                    f'Failed to connect to database after {max_attempts} attempts'
                )
            )
            # Exit with error code
            raise OperationalError('Could not connect to database')