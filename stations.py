import os
import json
import urllib.request
import urllib.parse
import pandas as pd
import folium
import matplotlib.pyplot as plt


pickle_filename = "metadata_all.pickle"
# pickle_filename = "metadata_3.pickle"

def read_pickle():
    print("read pickle")
    return pd.read_pickle(pickle_filename)

def write_pickle(stations):
    df = pd.DataFrame(stations)
    df.to_pickle(pickle_filename)
    print(f"Wrote dataframe: {pickle_filename}")
    print(df.head())

def write_json(data):
    json_formatted_str = json.dumps(data, indent=2)
    with open('station_metadata.json', 'w') as file:
            file.write(json_formatted_str)
    print("wrote json")

def process_stations(stations):
    for station in stations:
        print(f"{station['STID']}: {station['NAME']}")
        print(f"Distance: {station['DISTANCE']}")
        print(f"Lat/Lon : {station['LATITUDE']},{station['LONGITUDE']}")
        print("-----------------------------------")

def do_request():
    latlon = ( 40.667882, -111.924244)
    distance = 20
    limit = 1000
    api_token = "d9c53d5242bc454f86c9346bd233a96f"
    query_params = {
        "status": "active",
        "limit": limit,
        "radius": f"{latlon[0]},{latlon[1]},{distance}",
        "token": api_token,
    }
    encoded_params = urllib.parse.urlencode(query_params)
    url = f"https://api.synopticlabs.org/v2/stations/metadata?{encoded_params}"
    print(url)
    with urllib.request.urlopen(url) as response:
        data = json.loads(response.read().decode())
        if data["SUMMARY"]["RESPONSE_CODE"] == 1:
            stations = data['STATION']
            write_pickle(stations)
            write_json(stations)
            process_stations(stations)
        else:
            print("Error: Failed to retrieve weather stations.")

def draw_folium(df):
    map_center = [float(df.loc[0, 'LATITUDE']), float(df.loc[0, 'LONGITUDE'])]
    m = folium.Map(location=map_center, zoom_start=10)

    for _, row in df.iterrows(): # Add markers for each station
        lat = float(row['LATITUDE'])
        lon = float(row['LONGITUDE'])
        name = row['NAME']
        stid = row['STID']
        folium.Marker(
            [lat, lon],
            popup=f"<b>{stid}</b><br>{name}"
        ).add_to(m)
    m.save('map.html')

def draw_matplot(df):
    # Convert latitude and longitude columns to float
    # df['LATITUDE'] = df['LATITUDE'].astype(float)
    # df['LONGITUDE'] = df['LONGITUDE'].astype(float)

    # Create scatter plot
    plt.scatter(df['LONGITUDE'].astype(float), df['LATITUDE'].astype(float), c='blue', marker='o')

    # Set plot title and labels
    plt.title('Station Locations')
    plt.xlabel('Longitude')
    plt.ylabel('Latitude')

    plt.savefig('map.png')
    # Display the plot
    # plt.show()

def main():
    # pd.set_option('display.max_columns', None)
    # pd.set_option('display.max_rows', None)
    # pd.set_option('display.expand_frame_repr', False)
    if os.path.exists(pickle_filename):
        df = read_pickle()
        # print(df.columns)
        df_f = df[['STID', 'NAME', 'DISTANCE', 'LATITUDE', 'LONGITUDE']]
        print(df_f)
        draw_folium(df_f)
        draw_matplot(df_f)
    else:
        do_request()

if __name__=="__main__":
    main()