from flask import Flask
from flask import render_template
from flask import url_for, request, redirect
from flask import jsonify
from boto.s3.connection import S3Connection
import jinja2
import pusher
import config
import string, random
import os, urllib, urllib2, json

app = Flask(__name__)

# GLOBAL VARIABLES
url_movie_mapping = {}
url_owner_mapping = {}
url_members_mapping = {}
url_password_mapping = {}
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

@app.route('/user_url_map')
def user_url_map():
	page_url = request.args.get('url')
	movie = request.args.get('movie')
	bucket_name = request.args.get('bucket')
	movie_url = "https://s3.amazonaws.com/" + bucket_name + "/" + movie
	url_movie_mapping[page_url] = movie_url
	return jsonify({'status': 'success'})

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

@app.route('/upload_to_s3',methods=['POST'])
def upload_to_s3():
	connection = S3Connection(config.s3_key,config.s3_secret)
	bucket_name = request.form.get('useridhere')+'splitscreenmoviesbucket'
	bucket = connection.get_bucket(bucket_name)
  	with open(request.files['file'].filename, 'wb+') as destination:
  		destination.write(request.files['file'].read())
	key = bucket.new_key(destination.name)
  	key.set_contents_from_file(open(destination.name))
  	key.set_acl('public-read')
  	os.remove(destination.name)
	return redirect('/fb_login')

@app.route('/set_up_bucket_for_user',methods=['POST'])
def set_up_bucket():
	connection = S3Connection(config.s3_key,config.s3_secret)
	userid = request.form.get('userID')
	videos = []
	name = json.load((urllib2.urlopen('https://graph.facebook.com/'+userid+'?fields=name')))['name']
	buckets = connection.get_all_buckets()
	for b in buckets:
		if b.name == userid+'splitscreenmoviesbucket':
			user_videos = connection.get_bucket(b.name).list()
			for v in user_videos:
				videos.append(v.name)
				return jsonify(name=name,videos=videos)
	connection.create_bucket(userid+'splitscreenmoviesbucket')
	return jsonify(name=name,videos=videos)

	
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
	chars = string.ascii_uppercase + string.ascii_lowercase
	size = 6
	passwd = ''.join(random.choice(chars) for x in range(size))
	if not url_owner_mapping.has_key(page):
		url_owner_mapping[page] = owner
		url_password_mapping[page] = passwd
	return jsonify({'owner': url_owner_mapping[page], 'password': url_password_mapping[page]})

@app.route('/change_owner',methods=['POST'])
def change_owner():
	page_id = request.form.get('page_id')
	owner = request.form.get('newOwner')
	url_owner_mapping[page_id] = owner
	chars = string.ascii_uppercase + string.ascii_lowercase
	size = 6
	passwd = ''.join(random.choice(chars) for x in range(size))
	p = pusher.Pusher(app_id=config.app_id, key=config.app_key, secret=config.app_secret)
	p['presence-splitscreen-'+page_id].trigger('splitscreen-event-'+page_id, {'ownerChange': owner, 'newPassword': passwd})
	return jsonify(status="success")

@app.route('/send_chat', methods=['POST'])
def send_chat():
	chat_message = request.form.get('chat')
	page_id = request.form.get('page_id')
	sender = request.form.get('sender')
	p = pusher.Pusher(app_id=config.app_id, key=config.app_key, secret=config.app_secret)
	p['presence-splitscreen-'+page_id].trigger('splitscreen-event-'+page_id, {'chatMessage': chat_message, 'sender': sender})
	return jsonify({'userInfo': sender})

@app.route('/fb_login')
def fb_login():
	return render_template('fb_login.html')

if __name__ == "__main__":
	app.run(debug=True)
