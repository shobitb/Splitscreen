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
url_members_mapping = {}
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

""""
@app.route('/url_movie_map')
def url_movie_mapper():
	page_url = request.args.get('url')
	movie = request.args.get('movie')
	connection = S3Connection(con0fig.s3_key,config.s3_secret)
	bucket = connection.get_bucket(bucket_name)
	key = bucket.get_key(movie+'.mp4')
	movie_url = key.generate_url(18000) # url is available for 18000 seconds i.e. 5 hours
	url_movie_mapping[page_url] = movie_url
	return jsonify({'status': 'success'})
"""

@app.route('/url_map')
def url_map():
	page_url = request.args.get('url')
	movie = request.args.get('movie')
	movie_url = 'http://d8gfr27j5890z.cloudfront.net/'+movie+'.mp4'
	url_movie_mapping[page_url] = movie_url
	return jsonify({'status': 'success'})

@app.route('/youtube_url_map')
def youtube_url_map():
	page_url = request.args.get('url')
	movie = request.args.get('movie')
	movie_url = movie
	url_movie_mapping[page_url] = movie_url
	return jsonify({'status': 'success'})

<<<<<<< HEAD
@app.route('/Upload_To_S3',methods=['POST'])
def Upload_To_S3():
	connection = S3Connection("AKIAIMC67ZNDJPG4KOOA","ffrSB3O6PPd1KfPB4djBl49Ec0BRO+f9gpm8cn83")
	bucket = connection.get_bucket("splitscreenmoviesbucket")  # bucket names must be unique
  	with open(request.files['file'].filename, 'wb+') as destination:
      	    destination.write(request.files['file'].read())
	key = bucket.new_key(destination.name)
  	key.set_contents_from_file(open(destination.name))
  	key.set_acl('public-read')
	return redirect('/')
	


=======
>>>>>>> b289aec44180813f54dc8c72609e5a274de71084
@app.route('/pusher/presence_auth',methods=['POST'])
def auth():
	channel_name = request.form.get('channel_name')
	socket_id = request.form.get('socket_id')
	channel_data = {'user_id': socket_id}
	channel_data['user_info'] = {'name' : "Name"}

	p = pusher.Pusher(app_id=config.app_id, key=config.app_key, secret=config.app_secret)

	auth = p[channel_name].authenticate(socket_id, channel_data)
	return jsonify(auth)

@app.route('/add_member',methods=['POST'])
def add_member():
	b = False
	member_name = request.form.get('name')
	page_id = request.form.get('page_id')
	if not url_members_mapping.has_key(page_id):
		url_members_mapping[page_id] = []
	else:
		for x in url_members_mapping[page_id]:
			if x == member_name:
				b = True
				break
	if b == False:
		url_members_mapping[page_id].append(member_name)

	p = pusher.Pusher(app_id=config.app_id, key=config.app_key, secret=config.app_secret)
	p['presence-splitscreen-'+page_id].trigger('splitscreen-event-'+page_id, { 'urlMembers': url_members_mapping[page_id] })
	return jsonify({'userInfo': member_name})

@app.route('/set_theater_owner')
def set_theater_owner():
	page = request.args.get('page_id');
	owner = request.args.get('owner')
	if not url_owner_mapping.has_key(page):
		url_owner_mapping[page] = owner
	return jsonify({'owner': url_owner_mapping[page]})

@app.route('/send_chat', methods=['POST'])
def send_chat():
	chat_message = request.form.get('chat')
	page_id = request.form.get('page_id')
	sender = request.form.get('sender')
	p = pusher.Pusher(app_id=config.app_id, key=config.app_key, secret=config.app_secret)
	p['presence-splitscreen-'+page_id].trigger('splitscreen-event-'+page_id, {'chatMessage': chat_message, 'sender': sender})
	return jsonify({'userInfo': sender})

if __name__ == "__main__":
	app.run(debug=True)
