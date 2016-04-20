# Get API Key
with open('OBA_API_Key.txt') as key_file:
    key_mpm = key_file.read()

# Get API Server Location
with open('OBA_Server_Location.txt', 'r') as server_file:
    oba_url = server_file.read()

# Choose Agency to Record From
agency_ID = "1"

# Library Imports
import requests
import re
import csv
import time

# Create Function to Call and Write the Data
def call_oba_api():
    
    # Access API and Download Data
    api_alerts = oba_url + 'api/gtfs_realtime/alerts-for-agency/'+agency_ID+'.pbtext?key=' + key_mpm + "&removeAgencyIds=false"
    api_positions = oba_url + 'api/gtfs_realtime/vehicle-positions-for-agency/'+agency_ID+'.pbtext?key=' + key_mpm + "&removeAgencyIds=false"
    api_trip_updates = oba_url + 'api/gtfs_realtime/trip-updates-for-agency/'+agency_ID+'.pbtext?key=' + key_mpm + "&removeAgencyIds=false"
    
    r_alerts = requests.get(api_alerts)
    r_positions = requests.get(api_positions)
    r_trip_updates = requests.get(api_trip_updates)
    
    #----------------------------------
    # Write Position Data
    positions_raw = r_positions.content
    
    # Get Positions Header
    begin_header = positions_raw.find("header")
    end_header = positions_raw.find("}")
    pos_header = positions_raw[begin_header:end_header+1]
    
    # Group All the Entities
    loc_entity = [i.start() for i in re.finditer("entity", positions_raw)]
    pos_entities = []
    for i in loc_entity:
        if i!=loc_entity[-1]:
            pos_entities.append(positions_raw[i:(loc_entity[loc_entity.index(i)+1]-1)])
        else:
            pos_entities.append(positions_raw[i:-1])
    
    # Get the Timestamp for the Positions API Call
    loc_timestamp = pos_header.find("timestamp")
    loc_newline = pos_header.find("\n", loc_timestamp)
    pos_call_timestamp=int(pos_header[loc_timestamp:loc_newline].replace("timestamp: ",""))
    
    # Group all the Vehicle Data
    vehicles=[]
    for i in pos_entities:
        loc_vehicle = i.find("vehicle")
        loc_cbrackets = [j.start() for j in re.finditer("}", i)]
        vehicles.append(i[loc_vehicle:loc_cbrackets[-2]+1])
    
    # Get Trip and Route Data
    trip_ids=[]
    route_ids=[]
    for i in vehicles:
        loc_trip = i.find("trip")
        if loc_trip == -1:
            trip_ids.append("NA")
            route_ids.append("NA")
            continue
        loc_trip_id = i.find("trip_id",loc_trip)
        loc_route_id = i.find("route_id", loc_trip)
        
        loc_newline = i.find("\n", loc_trip_id)
        trip_id = i[loc_trip_id:loc_newline].replace("trip_id: ","").replace('"','')
        trip_ids.append(trip_id)
        
        loc_newline = i.find("\n", loc_route_id)
        route_id = i[loc_route_id:loc_newline].replace("route_id: ","").replace('"','')
        route_ids.append(route_id)
    
    # Get Vehicle Positions
    vehicle_positions=[]
    for i in vehicles:
        loc_position = i.find("position")
        if loc_position == -1:
            vehicle_positions.append("NA")
            continue
        loc_cbracket = i.find("}",loc_position)
        vehicle_positions.append(i[loc_position:loc_cbracket+1])
    
    # Get Vehicle Latitudes
    vehicle_latitudes=[]
    for i in vehicles:
        loc_latitude = i.find("latitude")
        if loc_latitude == -1:
            vehicle_latitudes.append("NA")
            continue
        loc_newline = i.find("\n",loc_latitude)
        num = float(i[loc_latitude:loc_newline].replace("latitude: ",""))
        vehicle_latitudes.append(num)
    
    # Get Vehicle Longitudes
    vehicle_longitudes=[]
    for i in vehicles:
        loc_longitude = i.find("longitude")
        if loc_longitude == -1:
            vehicle_longitudes.append("NA")
            continue
        loc_newline = i.find("\n",loc_longitude)
        num = float(i[loc_longitude:loc_newline].replace("longitude: ",""))
        vehicle_longitudes.append(num)
    
    # Get the Timestamp when Vehicle Info Was Reported
    vehicle_timestamps=[]
    for i in vehicles:
        loc_timestamp = i.find("timestamp")
        if loc_longitude == -1:
            vehicle_timestamps.append("NA")
            continue
        loc_newline = i.find("\n",loc_timestamp)
        num = int(i[loc_timestamp:loc_newline].replace("timestamp: ",""))
        vehicle_timestamps.append(num)
    
    # Get Vehicle Ids
    vehicle_ids=[]
    for i in vehicles:
        loc_vehicle_info = [j.start() for j in re.finditer("vehicle", i)]
        loc_vehicle_section = i.find("vehicle", loc_vehicle_info[1])
        if loc_vehicle_info == -1:
            vehicle_ids.append("NA")
            continue
        loc_vehicle_id = i.find("id", loc_vehicle_section)
        loc_newline = i.find("\n", loc_vehicle_id)
        num = i[loc_vehicle_id:loc_newline].replace("id: ","").replace('"','')
        vehicle_ids.append(num)
    
    # Write Vehicle Data to CSV File "Positions_AgencyID_Timestamp"
    with open('./Position_Data_Records/Positions_'+agency_ID+"_"+str(pos_call_timestamp)+".csv", 'wb') as myfile:
        wr = csv.writer(myfile, delimiter = ',', quoting=csv.QUOTE_NONE)
        wr.writerow(("Trip_Id", "Route_Id", "Vehicle_Id", "Vehicle_Timestamp", "Vehicle_Latitude", "Vehicle_Longitude"))
        for i in range(len(vehicles)):
            wr.writerow((trip_ids[i],route_ids[i],vehicle_ids[i],vehicle_timestamps[i],vehicle_latitudes[i],vehicle_longitudes[i]))
    
    #-------------------------
    # Write Trip Updates Data
    trip_updates_raw = r_trip_updates.content
    
    # Get Header
    begin_header = trip_updates_raw.find("header")
    end_header = trip_updates_raw.find("}")
    trip_updates_header = trip_updates_raw[begin_header:end_header+1]
    
    # Get Trip Updates Entities
    loc_entity = [i.start() for i in re.finditer("entity", trip_updates_raw)]
    trip_updates_entities = []
    for i in loc_entity:
        if i!=loc_entity[-1]:
            trip_updates_entities.append(trip_updates_raw[i:(loc_entity[loc_entity.index(i)+1]-1)])
        else:
            trip_updates_entities.append(trip_updates_raw[i:-1])
    
    # Get Trip Updates API Call Timestamp
    loc_timestamp = trip_updates_header.find("timestamp")
    loc_newline = trip_updates_header.find("\n", loc_timestamp)
    trip_updates_timestamp=int(trip_updates_header[loc_timestamp:loc_newline].replace("timestamp: ",""))
    
    # Group the Trip Updates
    trip_updates=[]
    for i in trip_updates_entities:
        loc_trip_update = i.find("trip_update")
        loc_cbrackets = [j.start() for j in re.finditer("}", i)]
        trip_updates.append(i[loc_trip_update:loc_cbrackets[-2]+1])
    
    # Get the Trip and Route Ids
    trip_ids=[]
    route_ids=[]
    for i in trip_updates:
        loc_trip = i.find("trip")
        if loc_trip == -1:
            trip_ids.append("NA")
            route_ids.append("NA")
            continue
        loc_trip_id = i.find("trip_id",loc_trip)
        loc_route_id = i.find("route_id", loc_trip)
        
        loc_newline = i.find("\n", loc_trip_id)
        trip_id = i[loc_trip_id:loc_newline].replace("trip_id: ","").replace('"','')
        trip_ids.append(trip_id)
        
        loc_newline = i.find("\n", loc_route_id)
        route_id = i[loc_route_id:loc_newline].replace("route_id: ","").replace('"','')
        route_ids.append(route_id)
    
    # Group the Stop Time Updates
    stop_time_updates=[]
    for i in trip_updates:
        loc_stop_time_update = i.find("stop_time_update")
        if loc_stop_time_update == -1:
            stop_time_updates.append("NA")
            continue
        loc_cbrackets = [j.start() for j in re.finditer("}", i)]
        stop_time_updates.append(i[loc_stop_time_update:loc_cbrackets[-3]+1])
    
    # Get the Departure Times and Stop Ids
    departure_times=[]
    stop_ids=[]
    for i in stop_time_updates:
        loc_stop_time_update = i.find("stop_time_update")
        if loc_stop_time_update == -1:
            departure_times.append("NA")
            stop_ids.append("NA")
            continue
        loc_time = i.find("time:",loc_stop_time_update)
        loc_stop_id = i.find("stop_id", loc_stop_time_update)
        
        loc_newline = i.find("\n", loc_time)
        departure_time = int(i[loc_time:loc_newline].replace("time: ","").replace('"',''))
        departure_times.append(departure_time)
        
        loc_newline = i.find("\n", loc_stop_id)
        stop_id = i[loc_stop_id:loc_newline].replace("stop_id: ","").replace('"','')
        stop_ids.append(stop_id)
    
    # Get the Vehicle Ids
    vehicle_ids=[]
    for i in trip_updates:
        loc_vehicle = i.find("vehicle")
        if loc_vehicle == -1:
            vehicle_ids.append("NA")
            continue
        loc_id = i.find("id", loc_vehicle)
        loc_newline = i.find("\n", loc_id)
        num = i[loc_id:loc_newline].replace("id: ","").replace('"','')
        vehicle_ids.append(num)
    
    # Get the Trip Update Timestamps
    trip_update_timestamps=[]
    for i in trip_updates:
        loc_timestamp = i.find("timestamp:")
        if loc_longitude == -1:
            trip_update_timestamps.append("NA")
            continue
        loc_newline = i.find("\n",loc_timestamp)
        num = int(i[loc_timestamp:loc_newline].replace("timestamp: ",""))
        trip_update_timestamps.append(num)
    
    # Get the Delays
    trip_update_delays=[]
    for i in trip_updates:
        loc_delay = i.find("delay:")
        if loc_delay == -1:
            trip_update_delays.append("NA")
            continue
        loc_newline = i.find("\n",loc_delay)
        num = int(i[loc_delay:loc_newline].replace("delay: ",""))
        trip_update_delays.append(num)
    
    # Write Trip Update info to CSV File "Trip_Updates_AgencyID_Timestamp"
    with open('./Trip_Update_Data_Records/Trip_Updates_'+agency_ID+"_"+str(trip_updates_timestamp)+".csv", 'wb') as myfile:
        wr = csv.writer(myfile, delimiter = ',', quoting=csv.QUOTE_NONE)
        wr.writerow(("Trip_Id", "Route_Id", "Vehicle_Id", "Trip_Update_Timestamp", "Departure_Time", "Stop_Id", "Delay"))
        for i in range(len(trip_updates)):
            wr.writerow((trip_ids[i],route_ids[i],vehicle_ids[i],trip_update_timestamps[i],departure_times[i],stop_ids[i],trip_update_delays[i]))
    
    
#-------------------------
# Begin Loop of Collecting Data
stop_sign = True
number_of_records = 0
error_count=0

while stop_sign:
    try:
        number_of_records +=1
        call_oba_api()
        error_count=0
    except:
        print "Error occurred at: ", time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(int(time.time())))
        error_count+=1
        print "Errors: ", error_count
    if number_of_records>=4:
        stop_sign=False
    if error_count>=3:
        stop_sign=False
    time.sleep(3)
