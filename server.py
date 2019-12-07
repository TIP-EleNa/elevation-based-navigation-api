import googlemaps
import requests
from flask import Flask, render_template, request
import os
from config import GOOGLEMAP_API_KEY

gmaps_key =googlemaps.Client(key = GOOGLEMAP_API_KEY) #google api key for using google services

app = Flask(__name__) #flask

@app.route('/search')  #flask, suppose we have url like http://127.0.0.1:5000/search?start=A&destination=B
def search():
    start = request.args.get('start', type=str)
    destination = request.args.get('destination', type=str)
    return start       #it should return A

address_list = ['50 Meadow st, amherst, MA', '9 Midvale Ave, '
                'Jefferson, NY', '18 Hampten St, Worcester, MA'] #this is the example address list
geocode_list = []
def address_to_geocode(address_list): #find the geocode by address
    for address in address_list:
        geocode = {}
        geocode_result = gmaps_key.geocode(address)
        lat = geocode_result[0]['geometry']['location']['lat']
        lng = geocode_result[0]['geometry']['location']['lng']
        geocode['lat'] = lat
        geocode['lng'] = lng
        geocode_list.append(geocode)
        print(geocode_list)
    return geocode_list

def get_altitude(geocode_list): #find altitude data by geocode, since they are not together.
    for dict in geocode_list:
        lat = dict['lat']
        lng = dict['lng']
        query = f'https://maps.googleapis.com/maps/api/elevation/json?locations={lat},{lng}&key=' + api_key
        request = requests.get(query).json()
        alt = request['results'][0]['elevation']
        dict['alt'] = alt
        print(geocode_list)
    return geocode_list

if __name__ == "__main__": #flask
    app.run(debug=True)
