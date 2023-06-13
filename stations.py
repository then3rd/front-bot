import os
import json
import urllib.request
import urllib.parse
import pandas as pd
import folium
import matplotlib.pyplot as plt
import geopandas as gpd
import contextily as ctx

class StationData:
    def __init__(self, pickle_filename):
        self.pickle_filename = pickle_filename

    def read_pickle(self):
        print("read pickle")
        return pd.read_pickle(self.pickle_filename)

    def write_pickle(self, stations):
        df = pd.DataFrame(stations)
        df['LATITUDE'] = df['LATITUDE'].astype(float) 
        df['LONGITUDE'] = df['LONGITUDE'].astype(float)
        df.to_pickle(self.pickle_filename)
        print(f"Wrote dataframe: {self.pickle_filename}")
        print(df.head())
        print(df.dtypes)

    def write_json(self, data):
        json_formatted_str = json.dumps(data, indent=2)
        with open('station_metadata.json', 'w') as file:
                file.write(json_formatted_str)
        print("wrote json")

    def print_stations(self, stations):
        for station in stations:
            print(f"{station['STID']}: {station['NAME']}")
            print(f"Distance: {station['DISTANCE']}")
            print(f"Lat/Lon : {station['LATITUDE']},{station['LONGITUDE']}")
            print("-----------------------------------")

    def do_request(self):
        latlon = (40.667882, -111.924244)
        distance = 16
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
                self.write_pickle(stations)
                self.write_json(stations)
            else:
                print("Error: Failed to retrieve weather stations.")

class MapPlotter:
    def __init__(self, pickle_filename):
        self.pickle_filename = pickle_filename

    def draw_folium(self, df):
        map_center = [float(df.loc[0, 'LATITUDE']), float(df.loc[0, 'LONGITUDE'])]
        m = folium.Map(location=map_center, zoom_start=10)

        for _, row in df.iterrows():
            lat = float(row['LATITUDE'])
            lon = float(row['LONGITUDE'])
            name = row['NAME']
            stid = row['STID']
            folium.Marker(
                [lat, lon],
                popup=f"<b>{stid}</b><br>{name}"
            ).add_to(m)
        m.save('map.html')

    def draw_matplot(self, df):
        gdf = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df['LONGITUDE'], df['LATITUDE']))
        gdf.crs = 'EPSG:4326'
        gdf_wm = gdf.to_crs(epsg=3857)
        orig_map = plt.colormaps.get_cmap('viridis')
        reversed_map = orig_map.reversed()
        ax = gdf_wm.plot(
            figsize=(30, 30),
            alpha=1,
            markersize=50,
            column='DISTANCE',
            cmap=reversed_map,
            edgecolors='black',
            legend=True,
            legend_kwds={'shrink': 0.5}
        )
        ax.axis('off')
        ctx.add_basemap(ax, zoom=11)
        plt.savefig(
            'map.png',
            bbox_inches='tight',
            pad_inches=0
        )

    def main(self):
        if os.path.exists(self.pickle_filename):
            station_data = StationData(self.pickle_filename)
            df = station_data.read_pickle()
            df_f = df[['STID', 'NAME', 'DISTANCE', 'LATITUDE', 'LONGITUDE']]
            print(df_f)
            self.draw_folium(df_f)
            self.draw_matplot(df_f)
        else:
            station_data = StationData(self.pickle_filename)
            station_data.do_request()

if __name__ == "__main__":
    pickle_filename = "metadata.pickle"
    # pickle_filename = "metadata_3.pickle"
    map_plotter = MapPlotter(pickle_filename)
    map_plotter.main()
