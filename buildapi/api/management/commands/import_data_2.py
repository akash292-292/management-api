import csv
from django.core.management.base import BaseCommand
from api.models import menu_hours
#for storing business hours of each store into database
class Command(BaseCommand):
    help = 'Import data from CSV to PostgreSQL'
    def add_arguments(self, parser):
        parser.add_argument('csv_file', type=str, help='imports csv to database')
    def handle(self, *args, **kwargs):
        csv_file = kwargs['csv_file']
        with open(csv_file, 'r') as file:
            reader = csv.DictReader(file)
            for row in reader:
                menu_hours.objects.create(
                    store_id=row['store_id'],
                    start_time_local=row['start_time_local'],
                    end_time_local=row['end_time_local'],
                    day=row['day'],
                )

        self.stdout.write(self.style.SUCCESS('Data imported successfully'))
