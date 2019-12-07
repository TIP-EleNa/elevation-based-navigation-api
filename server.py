import googlemaps
import requests
import os
import osmnx as ox
import numpy as np
import networkx as nx
import geopy.distance

from flask import Flask, render_template, request, jsonify
from config import GOOGLEMAP_API_KEY
from flask_cors import CORS, cross_origin

googlemap_cli =googlemaps.Client(key = GOOGLEMAP_API_KEY) #google api key for using google services

app = Flask(__name__) #flask
app.config['CORS_HEADERS'] = 'Content-Type'

cors = CORS(app, resources={r"/search": {"origins": "http://localhost:5000"}})

@app.route('/search')  #flask, suppose we have url like http://127.0.0.1:5000/search?origin=A&destination=B
@cross_origin(origin='localhost',headers=['Content- Type','Authorization'])
def search():
    origin = request.args.get('origin', type=str)
    dest = request.args.get('destination', type=str)

    geocode_list = address_to_geocode([origin, dest])

    geo_origin = geocode_list[0]
    geo_dest = geocode_list[1]
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
