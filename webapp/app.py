import googlemaps
import requests
import os
import osmnx as ox
import networkx as nx
import geopy.distance

from flask import Flask, render_template, request, jsonify
from flask_cors import CORS, cross_origin

GOOGLEMAP_API_KEY = os.environ.get('GOOGLEMAP_API_KEY')
googlemap_cli = googlemaps.Client(key=GOOGLEMAP_API_KEY) # google api key for using google services

app = Flask(__name__)  # flask
CORS(app)

origin = None
dest = None
G = None
ratio = None
nearest_origin = None
nearest_dest = None
route = None
ret = None

@app.route('/search', methods=['POST'])
def search():
    global origin, dest, G, ratio, nearest_origin, nearest_dest, route, ret
    
    req = request.get_json()

    if origin == req['origin'] and dest == req['destination']: 
        if ratio != req['ratio']: 
            ratio = req['ratio']
            route = hybrid_path(G, nearest_origin, nearest_dest, ratio)

            waypoints = getWaypoints(G, route)
            dist, elev = get_stats(G, route)

            ret = {
                'waypoints': waypoints,
                'route_distance': dist,
                'route_elevation': elev
            }
    else: 
        origin = req['origin']
        dest = req['destination']

        geocode_list = address_to_geocode([origin, dest])

        geo_origin = geocode_list[0]
        geo_dest = geocode_list[1]

        if len(geo_origin) == 0 or len(geo_dest) == 0:
            return jsonify('address not found')

        dist = geopy.distance.distance(geo_origin, geo_dest).m
        if dist == 0 or dist > 10000:
            return jsonify([{'x': geo_origin[1], 'y': geo_origin[0]}, {'x': geo_dest[1], 'y': geo_dest[0]}])

        G = ox.graph_from_point(geo_origin, distance=dist, network_type='walk')

        ox.elevation.add_node_elevations(G, GOOGLEMAP_API_KEY, max_locations_per_batch=350, pause_duration=0.02)

        nearest_origin = ox.get_nearest_node(G, geo_origin)
        nearest_dest = ox.get_nearest_node(G, geo_dest)

        ratio = req['ratio']
        route = hybrid_path(G, nearest_origin, nearest_dest, ratio)

        waypoints = getWaypoints(G, route)
        dist, elev = get_stats(G, route)

        ret = {
            'waypoints': waypoints,
            'route_distance': dist,
            'route_elevation': elev
        }

    return jsonify(ret)


def hybrid_path(G, node_a, node_b, ratio, elev_mult=0.005):
    def score(id_a, id_b, edge_data):
        a = G.nodes[id_a]
        b = G.nodes[id_b]
        dist = ox.utils.euclidean_dist_vec(a['y'], a['x'], b['y'], b['x'])
        elev = max(b['elevation'] - a['elevation'], 0)  # Only count increases in elevation
        elev *= elev_mult
        ret = (1 - ratio) * dist + ratio * elev
        return ret

    p = nx.algorithms.shortest_paths.weighted.dijkstra_path(G, node_a, node_b, score)
    return p


def get_stats(G, route):
    dist = 0
    elev = 0
    last_id = None
    for curr_id in route:
        if last_id is not None:
            a = G.nodes[last_id]
            b = G.nodes[curr_id]
            d = ox.utils.euclidean_dist_vec(a['y'], a['x'], b['y'], b['x'])
            e = max(b['elevation'] - a['elevation'], 0)  # Only count increases in elevation
            dist += d
            elev += e
        last_id = curr_id
    dist *= 68.703 # to miles
    elev *= 3.281 # to feet
    return dist, elev


def address_to_geocode(address_list):  # find the geocode by address
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
        waypoints.append({'x': point.get('x'), 'y': point.get('y')})
    return waypoints


if __name__ == '__main__':
    app.run(host='0.0.0.0')
