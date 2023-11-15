import csv
from django.core.management.base import BaseCommand
from api.models import bq_results
#for storing timezone of each store into database 
class Command(BaseCommand):
    help = 'Import data from CSV to PostgreSQL'

    def add_arguments(self, parser):
        parser.add_argument('csv_file', type=str, help='for importing data to databse')

    def handle(self, *args, **kwargs):
        csv_file = kwargs['csv_file']

        with open(csv_file, 'r') as file:
            reader = csv.DictReader(file)
            for row in reader:
                bq_results.objects.create(
                    store_id=row['store_id'],
                    timezone_str=row['timezone_str'],
                )

        self.stdout.write(self.style.SUCCESS('Data imported successfully'))
