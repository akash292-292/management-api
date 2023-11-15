import pandas as pd
from api.models import menu_hours, bq_results, store_status,AggregatedStoreInfo,timestamp_day,report
from django.http import HttpResponse
from django.db import IntegrityError
from datetime import datetime, timedelta, timezone,time
import requests
import os,shutil
import csv
from django.http import FileResponse
from django.shortcuts import get_object_or_404
#from django.contrib.staticfiles.templatetags.staticfiles import static
import mimetypes
import os

reportname="reportid"
report_name = set()
cnt=0
def home(request):
    return HttpResponse("hi")

def trigger_report(request):
    global reportname,cnt,report_name
    cnt=cnt+1
    curr_reportname=reportname+str(cnt)
    #print(curr_reportname)
    def insert_missing_business_hours():
        #Function to insert if business hours are missing 
        # it will get unique store IDs from table_a
        unique_store_ids = store_status.objects.values_list('store_id', flat=True).distinct()
        for store_id in unique_store_ids:
            if not menu_hours.objects.filter(store_id=store_id).exists():
                for day in range(7):
                    try:
                        menu_hours.objects.create(
                            store_id=store_id,
                            day=day, 
                            start_time_local=time(0, 0, 0),
                            end_time_local=time(23, 59, 59)
                        )
                    except IntegrityError:
                        # Handle IntegrityError if the record already exists
                        pass
        
    insert_missing_business_hours()

    #Function to insert if timezones are missing

    def insert_missing_timezone_records():
        unique_store_ids = store_status.objects.values_list('store_id', flat=True).distinct()
        for store_id in unique_store_ids:
            if not bq_results.objects.filter(store_id=store_id).exists():
                bq_results.objects.create(store_id=store_id, timezone_str="America/Chicago")

    insert_missing_timezone_records()

    def create_aggregated_store_info():
        # Iterating  over store_status  schema
        for store_statu in store_status.objects.all():
            store_id = store_statu.store_id
            timezone_entry = bq_results.objects.get(store_id=store_id)
            timeszone_str = timezone_entry.timezone_str
           
            # Iterating over all week days (0-6)
            for day in range(7):
                # Get store hours for the day
                try:
                    menu_hours_entries = menu_hours.objects.filter(store_id=store_id, day=day)[:2]
                    
                    # initializing variables to some default values
                    start_time_local_1, end_time_local_1, start_time_local_2, end_time_local_2 = '00:00:00', '23:59:59', '00:00:00', '00:00:00'
    
                    # Update values if entries are found
                    if menu_hours_entries:
                        start_time_local_1 = menu_hours_entries[0].start_time_local
                        end_time_local_1 = menu_hours_entries[0].end_time_local
    
                        if len(menu_hours_entries) >= 2 and \
        (menu_hours_entries[0].start_time_local != menu_hours_entries[1].start_time_local or
         menu_hours_entries[0].end_time_local != menu_hours_entries[1].end_time_local):
                            start_time_local_2 = menu_hours_entries[1].start_time_local
                            end_time_local_2 = menu_hours_entries[1].end_time_local
    
                except menu_hours.DoesNotExist:
                    pass
    
                # Creating the AggregatedStoreInfo entry
                AggregatedStoreInfo.objects.update_or_create(
                    store_id=store_id,
                    timeszone_str=timeszone_str,
                    day=day,
                    defaults=
                    {
                       'start_time_local_1': start_time_local_1,
                       'end_time_local_1': end_time_local_1,
                       'start_time_local_2': start_time_local_2,
                       'end_time_local_2':end_time_local_2,
                    }
                    
                    )
                
    create_aggregated_store_info() 

    def merge_timestamp_day():
        for old_record in store_status.objects.all():
            timestamp_utc = pd.to_datetime(old_record.timestamp_utc, format='%Y-%m-%d %H:%M:%S.%f %Z')
            day = (timestamp_utc.weekday() + 1) % 7
    
            #  new record in timestamp_day is created
            new_record = timestamp_day.objects.create(
                store_id=old_record.store_id,
                status=old_record.status,
                timestamp_utc=old_record.timestamp_utc,
                day=(day+6)%7,
            )
            
    merge_timestamp_day()

    unique_store_ids = store_status.objects.values_list('store_id', flat=True).distinct()
    #iterating through the all store_ids
    for id in unique_store_ids:
        def calculate_last_hour_uptime(store_id):
            #  to get current timestamp
            current_timestamp = datetime.utcnow()
        
            # to  get the last hour timestamp
            last_hour_timestamp = current_timestamp - timedelta(hours=1)
        
            # Convert timestamps to string for comparison
            current_timestamp_str = current_timestamp.strftime('%Y-%m-%d %H:%M:%S')
            last_hour_timestamp_str = last_hour_timestamp.strftime('%Y-%m-%d %H:%M:%S')
        
            # to get the nearest time_stamps
            store_data = store_status.objects.filter(
                store_id=id,
                timestamp_utc__gte=last_hour_timestamp_str,
                timestamp_utc__lte=current_timestamp_str
            ).values()
              #if no timestamps are recorded
            if not store_data:
                return 0
        
            store_df = pd.DataFrame.from_records(store_data)
        
            # getting business hours
            current_day = current_timestamp.weekday()
            business_hours_data = AggregatedStoreInfo.objects.filter(store_id=id, day=current_day).values()
            #if business hours are zero 
            if not business_hours_data:
                return 0
        
            business_hours_df = pd.DataFrame.from_records(business_hours_data)
        
            # Merge the store data with business hours data based on timestamps
            merged_data = pd.merge(store_df, business_hours_df, on='timestamp_utc', how='left')
         
            # timestamps outside the  business hours are removed
            merged_data = merged_data[
                (merged_data['timestamp_utc'] >= merged_data['start_time_local_1']) &
                (merged_data['timestamp_utc'] <= merged_data['end_time_local_1']) |
                (merged_data['timestamp_utc'] >= merged_data['start_time_local_2']) &
                (merged_data['timestamp_utc'] <= merged_data['end_time_local_2'])
            ]
        
            # filling the gaps with status based on the available status
            merged_data['status'].fillna(method='pad', inplace=True)
            merged_data['status'].fillna(0, inplace=True)
        
            # for calculating the last hour
            last_hour_uptime = merged_data[merged_data['timestamp_utc'] >= last_hour_timestamp_str]['status'].sum()
        
            return last_hour_uptime
        last_hour_uptime_result = calculate_last_hour_uptime(id)
        last_hour_downtime_result=60-last_hour_uptime_result
        store_data = pd.DataFrame(list(store_status.objects.values()))



        def calculate_last_day_uptime(store_id):
            downtime_last_day = 0
            uptime_last_day = 0
        
            # Assuming YourModel has columns 'store_id', 'timestamp_utc', and 'status'
            store_data = pd.DataFrame.from_records(
                store_status.objects.filter(store_id=store_id).values('timestamp_utc', 'status')
            )
        
            # Convert timestamps to datetime objects and localize to UTC
            store_data["timestamp_utc"] = pd.to_datetime(store_data["timestamp_utc"])
        
            # Ensure the DataFrame is sorted by timestamp
            store_data = store_data.sort_values(by="timestamp_utc")
        
            # Create a DataFrame with all timestamps in the past day at 1-minute intervals
            all_timestamps = pd.date_range(end=datetime.utcnow().replace(tzinfo=timezone.utc), periods=1440, freq='T')
            all_timestamps = pd.DataFrame({"timestamp_utc": all_timestamps})
        
            # Merge with the existing data to include all timestamps
            store_data = pd.merge(all_timestamps, store_data, on='timestamp_utc', how='left')
        
            # Interpolate missing values based on the existing data
            store_data["status"] = store_data["status"].interpolate(method="pad", limit=1)
        
            # Ensure the DataFrame is sorted again after interpolation
            store_data = store_data.sort_values(by="timestamp_utc")
        
            # Calculate the timestamps for the past day
            one_day_ago = datetime.utcnow().replace(tzinfo=timezone.utc) - timedelta(days=1)
        
            # Iterate over each timestamp in the past day
            for timestamp in store_data["timestamp_utc"]:
                # Skip if timestamp is not in the past day
                if timestamp >= one_day_ago:
                    # Use iloc to avoid issues with NaN values during conversion
                    predicted_status = store_data.loc[store_data["timestamp_utc"] == timestamp, "status"].iloc[0]
        
                    # Count downtime and uptime based on predictions
                    if pd.notna(predicted_status):  # Check for NaN values
                        if int(predicted_status) == 0:
                            downtime_last_day += 1
                        else:
                            uptime_last_day += 1
        
            # Convert downtime from hours to minutes
            downtime_last_day *= 60
        
            # Calculate uptime for the last day in minutes
            last_day_uptime = uptime_last_day - downtime_last_day
        
            return last_day_uptime
        last_day_uptime=calculate_last_day_uptime(id)
        last_day_downtime=24-last_day_uptime
        

        def calculate_last_week_uptime(store_id):
            downtime_last_week = 0
            uptime_last_week = 0
        
            store_data = pd.DataFrame.from_records(
                store_status.objects.filter(store_id=store_id).values('timestamp_utc', 'status')
            )
        
            # Convert timestamps to datetime objects and localize to UTC
            store_data["timestamp_utc"] = pd.to_datetime(store_data["timestamp_utc"])
        
            # Ensure the DataFrame is sorted by timestamp
            store_data = store_data.sort_values(by="timestamp_utc")
        
            # Create a DataFrame with all timestamps in the past week at 1-hour intervals
            all_timestamps = pd.date_range(end=datetime.utcnow().replace(tzinfo=timezone.utc), periods=168, freq='H')
            all_timestamps = pd.DataFrame({"timestamp_utc": all_timestamps})
        
            # Merge with the existing data to include all timestamps
            store_data = pd.merge(all_timestamps, store_data, on='timestamp_utc', how='left')
        
            # Interpolating missing values for easy of calculation
            store_data["status"] = store_data["status"].interpolate(method="pad", limit=1)
        
            # sorting the data_frame
            store_data = store_data.sort_values(by="timestamp_utc")
        
            # Calculate the timestamps for the past week
            one_week_ago = datetime.utcnow().replace(tzinfo=timezone.utc) - timedelta(weeks=1)
        
            # Iterate over each timestamp in the past week
            for timestamp in store_data["timestamp_utc"]:
                # Skippinf if timestamp is not in the past week
                if timestamp >= one_week_ago:
                    predicted_status = store_data.loc[store_data["timestamp_utc"] == timestamp, "status"].iloc[0]
        
                    # Counting downtime and uptime based on predictions
                    if pd.notna(predicted_status):  # Checking for NaN values
                        if int(predicted_status) == 0:
                            downtime_last_week += 1
                        else:
                            uptime_last_week += 1
        
            # Calculating uptime for the last week in hours
            last_week_uptime = uptime_last_week - downtime_last_week
        
            return last_week_uptime
        lst_week_uptime=calculate_last_week_uptime(id)
        lst_week_downtime=7*24-lst_week_uptime
        #print(last_day_uptime)
        #print(last_day_downtime)
        #print(last_hour_uptime_result)
        #print(last_hour_downtime_result)
        #print(lst_week_uptime)
        #print(lst_week_downtime)
        
        report.objects.create(
            store_id=id,
            uptime_last_hour=last_hour_uptime_result,
            uptime_last_day=last_day_uptime,
            update_last_week=lst_week_uptime,
            downtime_last_hour=last_hour_downtime_result,
            downtime_last_day=last_day_downtime,
            downtime_last_week=lst_week_downtime,

        )
    report_name.add(curr_reportname)
    response = HttpResponse(content_type='csv')
    response['Content-Disposition'] = 'attachment; filename="exported_data.csv"'

    writer = csv.writer(response)
    writer.writerow(['store_id', 'uptime_last_hour', 'uptime_last_day','update_last_week','downtime_last_hour','downtime_last_day','downtime_last_week'])  # Add your field names

    queryset = report.objects.all()
    for obj in queryset:
        writer.writerow([obj.store_id, obj.uptime_last_hour, obj.uptime_last_day,obj.update_last_week,obj.downtime_last_hour,obj.downtime_last_day,obj.downtime_last_week])  # Add your field values
    folder_path = 'C:/Users/akash/projects/management/buildapi/outputfiles'

    # Ensure the folder exists, create it if necessary
    os.makedirs(folder_path, exist_ok=True)

    # Create the full path to save the file
    save_path = os.path.join(folder_path, curr_reportname+'.csv')

    # Save the CSV content to a file
    with open(save_path, 'w', newline='') as file:
        file.write(response.content.decode('utf-8'))
    #return response
    return HttpResponse(curr_reportname)
     
def get_report(request):
    report_id = report_id = request.GET.get('report_id')
    if report_id in report_name:
        print(report_id)
        base_path = 'C:/Users/akash/projects/management/buildapi/outputfiles/'
        # base_path=base_path+report_id

    # Combine the base path and the provided file path
        file_path = os.path.join(base_path, f'{report_id}.csv')
        print(file_path)
        # Check if the file exists
        if not os.path.exists(file_path):
            return HttpResponse('File not found')

        # Get the content type of the file
        content_type, encoding = mimetypes.guess_type(file_path)

        # Open the file and create a FileResponse
        
        response = FileResponse(open(file_path, 'rb'), content_type=content_type)
        response['Content-Disposition'] = f'attachment; filename="{os.path.basename(file_path)}"'

        return response
    else:
        return HttpResponse('Running')

    #return response
print('completed')



      
    
