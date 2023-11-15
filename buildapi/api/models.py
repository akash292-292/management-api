from django.db import models

# Create your models here.
# to store store_id and timezeon_str csv file to database.
class bq_results(models.Model):
        store_id=models.TextField(max_length=100)
        timezone_str=models.CharField(max_length=100)
    
 # to store   store_id,day,start_time_local,end_time_local csv file to database.
class menu_hours(models.Model):
        store_id=models.TextField(max_length=100)
        day=models.IntegerField()
        start_time_local=models.TextField(max_length=100)
        end_time_local=models.TextField(max_length=100)
# to store store_id,status,timestamp_utc csv file to database.
class store_status(models.Model):
        store_id=models.TextField(max_length=100)
        status=models.TextField(max_length=100)
        timestamp_utc=models.TextField(max_length=100)
        
#to merge bq_results and menu_hours model to help us in future classfication.
class AggregatedStoreInfo(models.Model):
      store_id=models.TextField(max_length=100)
      timeszone_str=models.TextField(max_length=100)
      day=models.IntegerField()
      start_time_local_1=models.TextField(max_length=100)
      end_time_local_1=models.TextField(max_length=100)
      start_time_local_2=models.TextField(max_length=100)
      end_time_local_2=models.TextField(max_length=100)

#to store time_stamp along with day to make calculations easy
class timestamp_day(models.Model):
        store_id=models.TextField(max_length=100)
        status=models.TextField(max_length=100)
        timestamp_utc=models.TextField(max_length=100)
        day=models.TextField(null=True)


#store_id, uptime_last_hour(in minutes), uptime_last_day(in hours), update_last_week(in hours), 
# downtime_last_hour(in minutes), downtime_last_day(in hours), downtime_last_week(in hours)    
# Model for output report generations.
class report(models.Model):
        store_id=models.TextField(max_length=1000)
        uptime_last_hour=models.IntegerField()
        uptime_last_day=models.IntegerField()
        update_last_week=models.IntegerField()
        downtime_last_hour=models.IntegerField()
        downtime_last_day=models.IntegerField()
        downtime_last_week=models.IntegerField()