import googlemaps
import requests
import os
import osmnx as ox
import numpy as np
import networkx as nx
import geopy.distance

from flask import Flask, render_template, request, jsonify
from flask_cors import CORS, cross_origin

GOOGLEMAP_API_KEY = os.environ.get('GOOGLEMAP_API_KEY')
googlemap_cli =googlemaps.Client(key = GOOGLEMAP_API_KEY) #google api key for using google services

app = Flask(__name__) #flask
app.config.from_pyfile('config.py', silent=True)
app.config['CORS_HEADERS'] = 'Content-Type'
CORS(app, headers='Content-Type', resources={r"/*": {"origins": "*"}})

@app.route('/search', methods=['POST']) 
@cross_origin()
def search():
    req = request.get_json()
    origin = req['origin']
    dest = req['destination']

    geocode_list = address_to_geocode([origin, dest])

    geo_origin = geocode_list[0]
    geo_dest = geocode_list[1]
    if len(geo_origin) == 0 or len(geo_dest) == 0: 
        return jsonify('address not found')

    dist = geopy.distance.distance(geo_origin, geo_dest).m

    G = ox.graph_from_point(geo_origin, distance=dist, network_type='walk')

    ox.elevation.add_node_elevations(G, GOOGLEMAP_API_KEY, max_locations_per_batch=350, pause_duration=0.02)
    ox.elevation.add_edge_grades(G, add_absolute=True)

    nearest_origin = ox.get_nearest_node(G, geo_origin)
    nearest_dest = ox.get_nearest_node(G, geo_dest)

    route = nx.shortest_path(G, nearest_origin, nearest_dest)
    
    waypoints = getWaypoints(G, route)

    return jsonify(waypoints)       #it should return A

def address_to_geocode(address_list): #find the geocode by address
    geocode_list = []
    for address in address_list: 
        geocode = []
        geocode_result = googlemap_cli.geocode(address)
        if len(geocode_result) == 0: 
            continue
        lat = geocode_result[0]['geometry']['location']['lat']
        lng = geocode_result[0]['geometry']['location']['lng']
        geocode.append(lat)
        geocode.append(lng)
        geocode_list.append(geocode)
    return geocode_list

def getWaypoints(G, route): 
    waypoints = []
    for node in route: 
        point = G.nodes[node]
        waypoints.append({'x': point.get('x'), 'y':point.get('y')})
    return waypoints

if __name__ == "__main__": #flask
    app.run(debug=True)
