from django.core.management.base import BaseCommand
from django.db import connection
from django.conf import settings


class Command(BaseCommand):
    help = 'Optimize database performance with additional indexes and settings'

    def add_arguments(self, parser):
        parser.add_argument(
            '--analyze',
            action='store_true',
            help='Run ANALYZE on all tables to update statistics',
        )
        parser.add_argument(
            '--vacuum',
            action='store_true',
            help='Run VACUUM on PostgreSQL database (PostgreSQL only)',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting database optimization...'))
        
        with connection.cursor() as cursor:
            # Get database engine
            engine = settings.DATABASES['default']['ENGINE']
            
            if 'postgresql' in engine:
                self.optimize_postgresql(cursor, options)
            elif 'sqlite' in engine:
                self.optimize_sqlite(cursor, options)
            else:
                self.stdout.write(
                    self.style.WARNING(f'Optimization not implemented for {engine}')
                )

        self.stdout.write(self.style.SUCCESS('Database optimization completed!'))

    def optimize_postgresql(self, cursor, options):
        """Optimize PostgreSQL database"""
        self.stdout.write('Optimizing PostgreSQL database...')
        
        # Update table statistics
        if options['analyze']:
            self.stdout.write('Running ANALYZE...')
            cursor.execute('ANALYZE;')
            
        # Vacuum database
        if options['vacuum']:
            self.stdout.write('Running VACUUM...')
            cursor.execute('VACUUM;')
            
        # Set optimal PostgreSQL settings for authentication workload
        optimizations = [
            "SET shared_preload_libraries = 'pg_stat_statements';",
            "SET log_statement = 'mod';",
            "SET log_min_duration_statement = 1000;",  # Log slow queries
        ]
        
        for sql in optimizations:
            try:
                cursor.execute(sql)
                self.stdout.write(f'Applied: {sql}')
            except Exception as e:
                self.stdout.write(
                    self.style.WARNING(f'Could not apply {sql}: {e}')
                )

    def optimize_sqlite(self, cursor, options):
        """Optimize SQLite database"""
        self.stdout.write('Optimizing SQLite database...')
        
        # Update table statistics
        if options['analyze']:
            self.stdout.write('Running ANALYZE...')
            cursor.execute('ANALYZE;')
            
        # SQLite optimizations
        optimizations = [
            'PRAGMA optimize;',
            'PRAGMA journal_mode = WAL;',
            'PRAGMA synchronous = NORMAL;',
            'PRAGMA cache_size = 10000;',
            'PRAGMA temp_store = MEMORY;',
        ]
        
        for sql in optimizations:
            try:
                cursor.execute(sql)
                self.stdout.write(f'Applied: {sql}')
            except Exception as e:
                self.stdout.write(
                    self.style.WARNING(f'Could not apply {sql}: {e}')
                )