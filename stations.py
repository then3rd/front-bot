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
    def __init__(self):
        self.metadata_filename = "metadata.pickle"
        self.data_filename = "data.pickle"

    def _read_pickle(self, kind="metadata"):
        print("read pickle")
        if kind == "metadata":
            return pd.read_pickle(self.metadata_filename)
        else:
            return pd.read_pickle(self.data_filename)

    def _write_pickle(self, df, kind="metadata"):
        if kind == "metadata":
            name = self.metadata_filename
        else:
            name = self.data_filename
        df.to_pickle(name)
        print(f"Wrote dataframe: {name}")
        print(df.head())
        print(df.dtypes)

    def _filter_df(self, df, kind="metadata"):
        if kind == "metadata":
            # Filter relevant columns
            df = df.loc[:, ['NAME', 'STID', 'LATITUDE', 'LONGITUDE']]
        else:
            # only record stations with observations
            df = df[df["OBSERVATIONS"].notnull()]
            df = df.loc[:, ['NAME', 'STID', 'LATITUDE', 'LONGITUDE', 'OBSERVATIONS']]
        # Set types
        df['LATITUDE'] = df['LATITUDE'].astype(float) 
        df['LONGITUDE'] = df['LONGITUDE'].astype(float)
        return df

    def _write_json(self, data):
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

    def _do_request(self, kind="metadata"):
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
        url = f"https://api.synopticlabs.org/v2/stations/{kind}?{encoded_params}"
        print(url)
        with urllib.request.urlopen(url) as response:
            data = json.loads(response.read().decode())
            if data["SUMMARY"]["RESPONSE_CODE"] == 1:
                stations = data['STATION']
                self._write_json(stations)
                df = pd.DataFrame(stations)
                return df
            else:
                print("Error: Failed to retrieve station metadata")
                return False

    def get_data(self, kind="metadata"):
        filename = self.metadata_filename if kind == "metadata" else self.data_filename
        if not os.path.exists(filename):
            data = self._do_request(kind=kind)
            df = pd.DataFrame(data)
            df_f = self._filter_df(df)
            self._write_pickle(df_f, kind)
            return df_f
        else:
            return self._read_pickle(kind=kind)

class MapPlotter:
    # def __init__(self):

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
            # column='DISTANCE',
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
        std = StationData()
        # df = std.get_data(kind="metadata")
        df = std.get_data(kind="latest")
        self.draw_matplot(df)

if __name__ == "__main__":
    # pd.set_option('display.max_columns', None)
    # pd.set_option('display.max_rows', None)
    # pd.set_option('display.expand_frame_repr', False)
    map_plotter = MapPlotter()
    map_plotter.main()
