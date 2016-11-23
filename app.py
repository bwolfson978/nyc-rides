'''
import os

from flask import Flask, render_template, request, redirect, url_for
from flask.ext.sqlalchemy import SQLAlchemy

app = Flask(__name__)

DATABASE_URL = os.environ.get('DATABASE_URL', 'sqlite:////tmp/flask_app.db')

app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
db = SQLAlchemy(app)


class User(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  name = db.Column(db.String(100))
  email = db.Column(db.String(100))

  def __init__(self, name, email):
    self.name = name
    self.email = email

db.create_all()


@app.route('/')
def index():
  return render_template('index.html', users=User.query.all())


@app.route('/user', methods=['POST'])
def user():
  if request.method == 'POST':
    u = User(request.form['name'], request.form['email'])
    db.session.add(u)
    db.session.commit()
  return redirect(url_for('index'))

if __name__ == '__main__':
  port = int(os.environ.get('PORT', 5000))
  app.run(host='0.0.0.0', port=port)

'''
import sys, csv
from flask import Flask, request, render_template, json, redirect, url_for, flash
import googlemaps
import ride_data
import decoder

gmaps = googlemaps.Client(key='AIzaSyCw_Iz7GT1vARXvUJsC1ELZ3Iyz0fa1abA')
UPLOAD_FOLDER = '/uploads'
ALLOWED_EXTENSIONS = set(['csv'])

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['SECRET_KEY'] = 'super secret key'


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS


#@app.route("/", methods=['GET','POST'])
@app.route("/", methods=['GET'])
def upload_file():
    rides = ride_data.rides
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
            # invoke directions api and set a value to all legs of trip
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

    ride_json = json.dumps(ride_data.rides)
    return render_template('format.html', files = ride_data.rides, data = ride_json)


if __name__ == '__main__':
    app.run()
