from flask import Flask
from flask import render_template
from flask import url_for, request, redirect
from flask import jsonify
from boto.s3.connection import S3Connection
import jinja2
import pusher
import config
import string, random
import os, urllib

app = Flask(__name__)

# GLOBAL VARIABLES
url_movie_mapping = {}
url_owner_mapping = {}
bucket_name = "splitscreenmoviesbucket"

@app.route('/')
def index():
	connection = S3Connection(config.s3_key,config.s3_secret)
	bucket = connection.get_bucket(bucket_name)
	result = bucket.list()
	movies = []
	for r in result:
		movies.append(r.name.split(".mp4")[0])
	return render_template('index.html',movies=movies)

@app.route('/theater', methods=['GET','POST'])
def create_theater_url():
	chars = string.ascii_uppercase + string.digits
	size = 15
	url_id = ''.join(random.choice(chars) for x in range(size))
	return redirect('/theater/'+url_id)

@app.route('/theater/<theater_id>')
def theater(theater_id):
	if not url_movie_mapping.has_key(theater_id):
		error = "No such URL"
		return render_template('error.html',error=error)
	movie_url = url_movie_mapping[theater_id]
	return render_template('theater.html',movie_url=movie_url)

@app.route('/event')
def event_seek():
	page_id = request.args.get('page_id')
	p = pusher.Pusher(app_id=config.app_id, key=config.app_key, secret=config.app_secret)
	p['presence-splitscreen-'+page_id].trigger('splitscreen-event-'+page_id, { 'userId': request.args.get('member_id'), 'currentTime': request.args.get('currentTime') })
	return render_template('theater.html')

@app.route('/create_url')
def create_url():
	chars = string.ascii_uppercase + string.digits
	size = 15
	url_id = ''.join(random.choice(chars) for x in range(size))
	return jsonify({'url': url_id})

@app.route('/url_movie_map')
def url_movie_mapper():
	page_url = request.args.get('url')
	movie = request.args.get('movie')
	connection = S3Connection(config.s3_key,config.s3_secret)
	bucket = connection.get_bucket(bucket_name)
	key = bucket.get_key(movie+'.mp4')
	movie_url = key.generate_url(18000) # url is available for 18000 seconds i.e. 5 hours
	url_movie_mapping[page_url] = movie_url
	return jsonify({'status': 'success'})

@app.route('/pusher/presence_auth',methods=['POST'])
def auth():
	channel_name = request.form.get('channel_name')
	socket_id = request.form.get('socket_id')
	channel_data = {'user_id': socket_id}
	channel_data['user_info'] = {'name' : "Name"}

	p = pusher.Pusher(app_id=config.app_id, key=config.app_key, secret=config.app_secret)

	auth = p[channel_name].authenticate(socket_id, channel_data)
	return jsonify(auth)

@app.route('/set_name',methods=['POST'])
def set_name():
	member_name = request.form.get('name')
	return jsonify({'name' : member_name})

@app.route('/set_theater_owner')
def set_theater_owner():
	page = request.args.get('page_id');
	owner = request.args.get('owner')
	if not url_owner_mapping.has_key(page):
		url_owner_mapping[page] = owner
	return jsonify({'owner': url_owner_mapping[page]})

if __name__ == "__main__":
	app.run(debug=True)
