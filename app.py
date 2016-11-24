import csv
from flask import Flask, render_template, json
import googlemaps
import decoder

# get google maps client object using API key
gmaps = googlemaps.Client(key='AIzaSyCw_Iz7GT1vARXvUJsC1ELZ3Iyz0fa1abA')

app = Flask(__name__)


@app.route("/", methods=['GET'])
def upload_file():
    rides = {}
    f = open('uber-raw-data-apr14.csv', 'r')
    i = 0
    limit = 100
    for line in csv.DictReader(f.readlines(), skipinitialspace=True):
    # ignore first line with labels of data
        if i == 0:
            i += 1
            continue
        if i > limit:
            break
        if i != limit:
            rides[i] = {
                'timestamp' : line['Date/Time'],
                'lat' : line['Lat'],
                'long' : line['Lon']
            }
        # set dropoff location of previous ride to pickup location of current ride
        if i > 1 :
            # invoke directions api and get all points in the overview path of the trip
            # these points will be used to create the heatmap google map layer
            sourceLat = rides[i-1]['lat']
            sourceLon = rides[i-1]['long']
            destLat = line['Lat']
            destLon = line['Lon']
            directions = gmaps.directions((sourceLat,sourceLon),(destLat, destLon))
            points = directions[0]['overview_polyline']['points']
            path = decoder.decode(points)
            rides[i-1] = {
                'timestamp': rides[i-1]['timestamp'],
                'lat' : sourceLat,
                'long' : sourceLon,
                'drop_lat' : destLat,
                'drop_long' : destLon,
                'path' : path,
            }
        i += 1
    ride_json = json.dumps(rides)
    return render_template('format.html', files = rides, data = ride_json)


if __name__ == '__main__':
    app.run()
