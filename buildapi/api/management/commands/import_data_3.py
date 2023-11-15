
import csv
from django.core.management.base import BaseCommand
from api.models import store_status 
#for storing timestamps  of each store into database
class Command(BaseCommand):
    help = 'Import data from CSV to PostgreSQL'

    def add_arguments(self, parser):
        parser.add_argument('csv_file', type=str, help='Files\bq_results.csv')

    def handle(self, *args, **kwargs):
        csv_file = kwargs['csv_file']

        with open(csv_file, 'r') as file:
            reader = csv.DictReader(file)
            for row in reader:
                store_status.objects.create(
                    store_id=row['store_id'],
                    status=row['status'],
                    timestamp_utc=row['timestamp_utc'],
                    # Map each field to the corresponding CSV column
                )

        self.stdout.write(self.style.SUCCESS('Data imported successfully'))
