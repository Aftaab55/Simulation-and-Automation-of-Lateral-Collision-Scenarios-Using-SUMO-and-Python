import xml.etree.ElementTree as ET
import pandas as pd
import math

def haversine(lon1, lat1, lon2, lat2):
    """
    Calculate the great-circle distance (in meters) between two points
    on Earth given their latitude and longitude in decimal degrees.
    """
    # Convert degrees to radians
    lon1, lat1, lon2, lat2 = map(math.radians, [lon1, lat1, lon2, lat2])
    
    # Haversine formula
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    
    # Earth radius in meters (mean radius = 6371 km)
    r = 6371 * 1000
    return c * r

# Load the FCD XML file
tree = ET.parse(r"C:\Users\aftaa\OneDrive\Desktop\Polito Mechanical\Thesis\Simulations\Automatisation\4\Lateral\Lateral Scenario1\Output\fcd.xml")
root = tree.getroot()

# Create a list to hold all vehicle states
vehicle_states = []

# Parse XML
for timestep in root.findall('timestep'):
    time = float(timestep.get('time'))
    vehicles = timestep.findall('vehicle')
    vehicle_info = []
    for vehicle in vehicles:
        veh_id = vehicle.get('id')
        lane = vehicle.get('lane')
        lon = float(vehicle.get('x'))  # longitude (x in SUMO)
        lat = float(vehicle.get('y'))  # latitude (y in SUMO)
        vehicle_info.append({'id': veh_id, 'lane': lane, 'lon': lon, 'lat': lat})
    
    # Compare all vehicles in the same timestep
    for i in range(len(vehicle_info)):
        for j in range(i+1, len(vehicle_info)):
            v1 = vehicle_info[i]
            v2 = vehicle_info[j]
            if v1['lane'] == v2['lane']:  # same lane
                distance = haversine(v1['lon'], v1['lat'], v2['lon'], v2['lat'])
                if distance <= 2.5:  # 2.5-meter threshold
                    vehicle_states.append({
                        'time': time,
                        'lane': v1['lane'],
                        'vehicle1': v1['id'],
                        'vehicle2': v2['id'],
                        'gap_meters': round(distance, 2),
                        'lon1': round(v1['lon'], 6),
                        'lat1': round(v1['lat'], 6),
                        'lon2': round(v2['lon'], 6),
                        'lat2': round(v2['lat'], 6)
                    })

# Create DataFrame and save to Excel
output_df = pd.DataFrame(vehicle_states)
output_df.to_excel(r"C:\Users\aftaa\OneDrive\Desktop\Polito Mechanical\Thesis\Simulations\Automatisation\4\Lateral\Lateral Scenario1\Output\Output1.xlsx", index=False)

print("Done! Lateral gaps (in meters) saved to Output1.xlsx")