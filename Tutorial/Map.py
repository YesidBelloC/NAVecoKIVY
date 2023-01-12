from kivy.app import App
# from kivy.garden.mapview import MapView
from kivy_garden.mapview import MapView
import googlemaps
from pprint import pprint

GM_key = 'AIzaSyDrB16uv9NYnnT4WH4V0zcJmqvHGkxL9mE'
client = googlemaps.Client(key=GM_key)

MapClient = client
dir(MapClient)

# Place='18 Avenue Jacques Jezequel, Vanves'
Place='Intermarche vanves'
response = client.places_autocomplete(Place)
pprint(response[0]['description'])
response = client.geocode(response[0]['description'])


pprint(response)

print(len(response))

for i in range(0,len(response[0]['address_components'])):
    pprint(response[0]['address_components'][i]['long_name'])

LatUsr = response[0]['geometry']['location']['lat']
LngUsr = response[0]['geometry']['location']['lng']
# console :
# pip install mapview
# garden install mapview

class MapViewApp(App):
    def build(self):
        # Zoom: 1 Monde/ 15 Ville/ 25 Bloque
        mapview = MapView(zoom=25, lat=LatUsr, lon=LngUsr)
        return mapview


MapViewApp().run()