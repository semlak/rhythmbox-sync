from gi.repository import Gio, GLib, Gtk, GObject, Peas
from gi.repository import RB
from os.path import expanduser
from time import time
import sqlite3
import math
import requests
import json
# import urllib2

# keys = ['artist', 'album', 'year', 'track_number', 'disc_number', 'track_total', 'disc_total', 'media_type', 'album_artist', 'composer', 'title', 'rating', 'play_count', 'bpm', 'genre']
# for key in keys:
# print("SELECT " + key + ", " + key + "_ch_time" + " FROM track ORDER BY " + key + " ASC;")
# print("SELECT " + key + " FROM track WHERE " + key + "_ch_time" + " Not Null ORDER BY " + key + " ASC;")

home = expanduser("~")
rbsyncdb = home + "/.local/share/rhythmbox/rbsync.db"
cloudapp = 'http://localhost:8080'
syncup_api = cloudapp + '/api/sync_up/'
new_tracks_api = cloudapp + '/api/new_tracks/'
rbsync_client_id = 1

#for convienence:
props_as_strings = ["location", "keyword", "play_count", "title", "track_number", "disc_number", "bpm", "artist", "album", "date", "track_total", "disc_total", "media_type", "album_artist", "composer", "genre", "comment", "status", "description", "subtitle", "post_time", "type", "duration", "file_size", "mountpoint", "mtime", "first_seen", "last_seen", "last_played", "bitrate", "hidden"]

props_that_are_longs = ["play_count",  "track_number", "disc_number", "date", "track_total", "disc_total","post_time", "mtime", "first_seen", "last_seen", "last_played", "bitrate", "duration", "status"]
props_that_are_double = ["rating", "bpm", "beats_per_minute"]
props_that_are_uint64 = ["file_size"]
props_that_are_strings = ["title", "artist", "album", "media_type", "album_artist", "composer", "genre", "location", "comment", "description", "subtitle", "type",  "mountpoint"]
props_that_are_other = ["keyword", "entry_type", "hidden (boolean)"]


def dict_factory(cursor, row):
	d = {}
	for idx,col in enumerate(cursor.description):
		d[col[0]] = row[idx]
	return d

class RBSync(GObject.Object, Peas.Activatable):
	__gtype_name__ = 'RBSync'
	object = GObject.property(type=GObject.Object)


	def __init__(self):
		GObject.Object.__init__(self)
		# self.connect_signals()

		# print(dir(self.shell))
		# print("self:" , dir(self))

	def get_time(self):
		return math.floor(time())



	def connect_signals(self):
		# print(shell, dir(shell))
		# db = shell.props.db
		# self.db = self.shell.props.db
		# self.db.connect ('entry-changed', self.change_notify)

		# ecs is "entry-changed signal"
		self.ecs_id = self.db.connect ('entry-changed', self.change_notify)
		# should also handle entry-added and entry-deleted

		self.lcs_id = self.db.connect ('load-complete', self.db_load_complete_notify)

	def db_load_complete_notify (self, dbtree):
		# self.sync(None, None)
		'hey'


	def rbsync_update_track (self, entry, change):
		# shell = self.object
		# db = shell.props.db
		# print(dir(db))
		switch = {
			RB.RhythmDBPropType.RATING 		: "rating",
			RB.RhythmDBPropType.PLAY_COUNT 	: "play_count",
			RB.RhythmDBPropType.TITLE 		: "title",
			RB.RhythmDBPropType.TRACK_NUMBER 	: "track_number",
			RB.RhythmDBPropType.DISC_NUMBER 	: "disc_number",
			RB.RhythmDBPropType.BEATS_PER_MINUTE : "bpm",
			RB.RhythmDBPropType.ARTIST 		: "artist",
			RB.RhythmDBPropType.ALBUM 		: "album", 
			RB.RhythmDBPropType.DATE 		: "date",
			RB.RhythmDBPropType.TRACK_TOTAL 	: "track_total",
			RB.RhythmDBPropType.DISC_TOTAL 	: "disc_total",
			RB.RhythmDBPropType.MEDIA_TYPE 	: "media_type",
			RB.RhythmDBPropType.ALBUM_ARTIST 	: "album_artist",
			RB.RhythmDBPropType.COMPOSER 		: "composer",
			RB.RhythmDBPropType.GENRE 		: "genre"
			}

		rb_entry_id = entry.get_ulong(RB.RhythmDBPropType.ENTRY_ID)
		attr_to_update = change["prop"]
		print("attr_to_update", attr_to_update)
		attr_to_update_str = switch.get(attr_to_update, None)
		new_value = change["new"]

		# artist = GObject.Value()
		# artist.init(GObject.TYPE_STRING)
		# artist.set_string("Xena")
		# attr_to_update = RB.RhythmDBPropType.ARTIST
		# new_value = artist

		# artist.set_static_string
		# print("artist", artist)

		if rb_entry_id in self.rbsync_updates_in_progress:
			if attr_to_update_str in self.rbsync_updates_in_progress[rb_entry_id]:
				print("error on attempting to update entry for the following entry: " + entry.get_string(RB.RhythmDBPropType.TITLE))
				raise ValueError('When attempting to update an entry in rbsync internal database, rbsync found that it was already being updated')
			else:
				self.rbsync_updates_in_progress[rb_entry_id[attr_to_update_str]] = new_value
				# self.rbsync_updates_in_progress[rb_entry_id[attr_to_update_str]] = None
		else:
			self.rbsync_updates_in_progress[rb_entry_id] = {attr_to_update_str : new_value}
			# self.rbsync_updates_in_progress[rb_entry_id] = {attr_to_update_str : None}
		print("rbsync_updates_in_progress just before rb update", self.rbsync_updates_in_progress)

		self.db.entry_set(entry, attr_to_update, new_value)
		self.db.commit()
		print("done with update function, although entry change may be asynchronous")


	def update_in_progress(self, rb_entry_id, attr_to_update, new_value):
		return rb_entry_id in self.rbsync_updates_in_progress and attr_to_update in self.rbsync_updates_in_progress[rb_entry_id]

	def get_string_from_RhythmDBPropType(self, prop):
		switch = {
			RB.RhythmDBPropType.RATING 		: "rating",
			RB.RhythmDBPropType.PLAY_COUNT 	: "play_count",
			RB.RhythmDBPropType.TITLE 		: "title",
			RB.RhythmDBPropType.TRACK_NUMBER 	: "track_number",
			RB.RhythmDBPropType.DISC_NUMBER 	: "disc_number",
			RB.RhythmDBPropType.LOCATION 		: "location",
			RB.RhythmDBPropType.BEATS_PER_MINUTE : "bpm",
			RB.RhythmDBPropType.ARTIST 		: "artist",
			RB.RhythmDBPropType.ALBUM 		: "album", 
			RB.RhythmDBPropType.DATE 		: "date",
			RB.RhythmDBPropType.TRACK_TOTAL 	: "track_total",
			RB.RhythmDBPropType.DISC_TOTAL 	: "disc_total",
			RB.RhythmDBPropType.MEDIA_TYPE 	: "media_type",
			RB.RhythmDBPropType.ALBUM_ARTIST 	: "album_artist",
			RB.RhythmDBPropType.COMPOSER 		: "composer",
			RB.RhythmDBPropType.GENRE 		: "genre",
			RB.RhythmDBPropType.COMMENT		: "comment",
			RB.RhythmDBPropType.STATUS		: "status",
			RB.RhythmDBPropType.DESCRIPTION	: "description",
			RB.RhythmDBPropType.SUBTITLE		: "subtitle",
			RB.RhythmDBPropType.POST_TIME		: "post_time",
			RB.RhythmDBPropType.TYPE			: "type",
			RB.RhythmDBPropType.DURATION		: "duration",
			RB.RhythmDBPropType.FILE_SIZE		: "file_size",
			RB.RhythmDBPropType.MOUNTPOINT	: "mountpoint",
			RB.RhythmDBPropType.MTIME		: "mtime",
			RB.RhythmDBPropType.FIRST_SEEN	: "first_seen",
			RB.RhythmDBPropType.LAST_SEEN		: "last_seen",
			RB.RhythmDBPropType.LAST_PLAYED	: "last_played",
			RB.RhythmDBPropType.BITRATE		: "bitrate",
			RB.RhythmDBPropType.HIDDEN		: "hidden"  	#could try taking a different action if file is hidden, 
													#like seeing if it just changed names
		}
		return(switch.get(prop))


	def get_RhythmDBPropType_from_string(self, string):
		switch = {
			"rating"		: RB.RhythmDBPropType.RATING,
			"play_count"	: RB.RhythmDBPropType.PLAY_COUNT,
			"title"		: RB.RhythmDBPropType.TITLE,
			"track_number"	: RB.RhythmDBPropType.TRACK_NUMBER,
			"disc_number"	: RB.RhythmDBPropType.DISC_NUMBER,
			"location"	: RB.RhythmDBPropType.LOCATION,
			"bpm"		: RB.RhythmDBPropType.BEATS_PER_MINUTE,
			"artist  "	: RB.RhythmDBPropType.ARTIST,
			"album"		: RB.RhythmDBPropType.ALBUM, 
			"date"		: RB.RhythmDBPropType.DATE,
			"track_total"	: RB.RhythmDBPropType.TRACK_TOTAL,
			"disc_total"	: RB.RhythmDBPropType.DISC_TOTAL,
			"media_type"	: RB.RhythmDBPropType.MEDIA_TYPE,
			"album_artist"	: RB.RhythmDBPropType.ALBUM_ARTIST,
			"composer"	: RB.RhythmDBPropType.COMPOSER,
			"genre"		: RB.RhythmDBPropType.GENRE,
			"comment"		: RB.RhythmDBPropType.COMMENT,
			"status"		: RB.RhythmDBPropType.STATUS,
			"description"	: RB.RhythmDBPropType.DESCRIPTION,
			"subtitle"	: RB.RhythmDBPropType.SUBTITLE,
			"post_time"	: RB.RhythmDBPropType.POST_TIME,
			"type"		: RB.RhythmDBPropType.TYPE,
			"duration"	: RB.RhythmDBPropType.DURATION,
			"file_size"	: RB.RhythmDBPropType.FILE_SIZE,
			"mountpoint"	: RB.RhythmDBPropType.MOUNTPOINT,
			"mtime"		: RB.RhythmDBPropType.MTIME,
			"first_seen"	: RB.RhythmDBPropType.FIRST_SEEN,
			"last_seen"	: RB.RhythmDBPropType.LAST_SEEN,
			"last_played"	: RB.RhythmDBPropType.LAST_PLAYED,
			"bitrate"		: RB.RhythmDBPropType.BITRATE,
			"hidden"		: RB.RhythmDBPropType.HIDDEN
		}
		return(switch.get(string))




	def change_notify (self, dbtree, entry, entryChanges):
	# def change_notify():
		print("Hey. Change notification!")
		for change in entryChanges:
			print(change)
			print(change.prop)
			print(change.old)
			print(change.new)
			rb_entry_id = entry.get_ulong(RB.RhythmDBPropType.ENTRY_ID)
			# print(dir(self))
			print("rb_id", entry.get_ulong(RB.RhythmDBPropType.ENTRY_ID))
			# if rb_entry_id == 82: self.rbsync_update_track(entry, change)
			# print(entry.get_object(RB.RhythmDBPropType))
			# print("count", self.db.entry_count())

			#it is possible that this signal was received due to the user updating an attribute in rhythmbox (or otherwise not using rbsync)
			#in that case, we want to proceed with updating the rbsync database, and include the ch_date attribute for that property as appropriate

			#however, if the signal might also be received after rbsync tries to update a rhythmdb entry. In that case we don't necessarily want to make all
			#the same changes to the rbsync database. Mainly, the ch_date attributes are for changes that were requested by the user locally. also, the local play
			#count shouldn't be updated if the play count is updated due to a play on another device. 
			#There is logic to detect it here and in the play_count specific update part of self.update_rbsync_db

			#We still want to update the rb attributes in rbsyncdb, but not the ch_date attributes

			#After getting the property to update, we check if this property is one of the entries in the hash self.rbsync_updates_in_progress, and then use branch logic to make changes where appropriate

			print("rbsync_updates_in_progress", self.rbsync_updates_in_progress)


			attr_to_update = None

			switch = {
				RB.RhythmDBPropType.RATING 		: "rating",
				RB.RhythmDBPropType.PLAY_COUNT 	: "play_count",
				RB.RhythmDBPropType.TITLE 		: "title",
				RB.RhythmDBPropType.TRACK_NUMBER 	: "track_number",
				RB.RhythmDBPropType.DISC_NUMBER 	: "disc_number",
				RB.RhythmDBPropType.BEATS_PER_MINUTE : "bpm",
				RB.RhythmDBPropType.ARTIST 		: "artist",
				RB.RhythmDBPropType.ALBUM 		: "album", 
				RB.RhythmDBPropType.DATE 		: "date",
				RB.RhythmDBPropType.TRACK_TOTAL 	: "track_total",
				RB.RhythmDBPropType.DISC_TOTAL 	: "disc_total",
				RB.RhythmDBPropType.MEDIA_TYPE 	: "media_type",
				RB.RhythmDBPropType.ALBUM_ARTIST 	: "album_artist",
				RB.RhythmDBPropType.COMPOSER 		: "composer",
				RB.RhythmDBPropType.GENRE 		: "genre"
				}

			attr_to_update = switch.get(change.prop, None)
			print("attr_to_update", attr_to_update)

			if attr_to_update != None:
				#check self.rbsync_updates_in_progress
				if self.update_in_progress(rb_entry_id, attr_to_update, change.new) :
					#this is a property we want to update, but no update to ch_time property
					action = [attr_to_update, change.new]
				else:
					#this is a property we want to update, but we also need to update the ch_time for the property
					action = [attr_to_update, change.new, attr_to_update+"_ch_time", self.get_time()]
				self.add_or_update_rbsyncdb(action, [[entry]])
			else:
				#these are properties we want to update in the rbsyncdb, but don't need or even have a ch_time property
				switch = {
					RB.RhythmDBPropType.COMMENT		: "comment",
					RB.RhythmDBPropType.STATUS		: "status",
					RB.RhythmDBPropType.DESCRIPTION	: "description",
					RB.RhythmDBPropType.SUBTITLE		: "subtitle",
					RB.RhythmDBPropType.POST_TIME		: "post_time",
					RB.RhythmDBPropType.TYPE			: "type",
					RB.RhythmDBPropType.DURATION		: "duration",
					RB.RhythmDBPropType.FILE_SIZE		: "file_size",
					RB.RhythmDBPropType.MOUNTPOINT	: "mountpoint",
					RB.RhythmDBPropType.MTIME		: "mtime",
					RB.RhythmDBPropType.FIRST_SEEN	: "first_seen",
					RB.RhythmDBPropType.LAST_SEEN		: "last_seen",
					RB.RhythmDBPropType.LAST_PLAYED	: "last_played",
					RB.RhythmDBPropType.BITRATE		: "bitrate",
					RB.RhythmDBPropType.HIDDEN		: "hidden"  	#could try taking a different action if file is hidden, 
															#like seeing if it just changed names
				}
				attr_to_update = switch.get(change.prop, None)
				if attr_to_update != None:
					#this is a property we want to update in the rbsyncdb, but don't need or even have a ch_time property
					action = [attr_to_update, change.new]
					self.add_or_update_rbsyncdb(action, [[entry]])
				# else: 
					#this is just a case where the property updated in rhythmbox is not one where rbsync cares about.
			if rb_entry_id in self.rbsync_updates_in_progress and attr_to_update in self.rbsync_updates_in_progress[rb_entry_id]:
				del self.rbsync_updates_in_progress[rb_entry_id][attr_to_update]
				if self.rbsync_updates_in_progress[rb_entry_id] == {}:
					del self.rbsync_updates_in_progress[rb_entry_id]
			print("rbsync_updates_in_progress after rbsync entry update", self.rbsync_updates_in_progress)


	def create_rbsyncdb_tables(self, conn):
		conn.execute('''CREATE TABLE IF NOT EXISTS track (
			ID 			integer	PRIMARY KEY NOT NULL,
			location		TEXT,
			artist		text,	
			album		text,
			year			integer,
			track_number	integer,
			disc_number	integer,
			track_total	integer,
			disc_total	integer,
			media_type	text,
			album_artist	text,
			composer		text,
			title		TEXT,
			rating		REAL,
			play_count	integer,
			bpm			REAL,
			genre		text,
			comment 		TEXT,
			status		REAL,
			description 	TEXT,
			subtitle 		TEXT,
			post_time		integer,
			entry_type	text,
			duration		REAL,
			file_size		REAL,
			mountpoint	TEXT,
			mtime		integer,
			first_seen	integer,
			last_seen		integer,
			last_played	integer,
			bitrate		REAL,
			hidden		integer,
			rbsync_id		integer,
			sync_time		integer,
			local_play_count		integer,
			artist_ch_time			integer,
			album_ch_time			integer,
			year_ch_time			integer,
			track_number_ch_time	integer,
			disc_number_ch_time		integer,
			track_total_ch_time		integer,
			disc_total_ch_time		integer,
			media_type_ch_time		integer,
			album_artist_ch_time	integer,
			composer_ch_time		integer,
			title_ch_time			integer,
			rating_ch_time			integer,
			play_count_ch_time		integer,
			bpm_ch_time			integer,
			genre_ch_time			integer
		);''')
		# print ("Tables created successfully");



	def update_rbsync_db(self, entries):
		conn = sqlite3.connect(rbsyncdb)
		cursor=conn.cursor()
		print ("Opened database successfully");

		# tables are only created if they don't exist
		self.create_rbsyncdb_tables(conn) 
		for entry in entries:
			track_id = None  #to be filled in, but not used if only inserting a track
			rb_entry_id = entry['rb_entry_id']
			# cursor.execute('''select id,title,artist,album from track where title=:t and artist=:a and album=:al;''', 
				# {"t": entry['title'], "a": entry['artist'], "al": entry['album']})
			cursor.execute('''select id,title,artist,album,local_play_count from track where location=:l;''', 
				{"l": entry['location']})
			track_result = cursor.fetchall()
			if len(track_result) == 1:
				track_id = track_result[0][0]

			action = entry["action"]
			if action != None:
				print("action:", action)
				#this is when track attribute is being updated. We are updating rbsynddb.
				#note, I would like to make sure track is there.
				# cursor.execute('''select id,title,artist,album from track where title=:t and artist=:a and album=:al;''', 
				# 	{"t": entry['title'], "a": entry['artist'], "al": entry['album']})
				#Note, I would like to consolidate this a bit so we don't search down here as well as up above
				if (track_id == None):
					#unable to look up track_id using location (file name including full path). This is likely due to filename being changed
					#try searcing by combination of title, artist, album
					cursor.execute('''select id,title,artist,album,local_play_count from track where title=:t and artist=:a and album=:al;''', 
						{"t": entry['title'], "a": entry['artist'], "al": entry['album']})
					track_result = cursor.fetchall()
					if track_result == []:
						#still unable to lookup track. I would like to add different attempts to lookup, but for now this seems enough.
						conn.close()
						print("Closed DB")
						print("error on attempting to update entry for the following entry", entry)
						raise ValueError('When attempting to update an entry in rbsync external database, rbsync was unable to look up entry ' +
							'in rbsync external database. tried looking using filename ("location" in rb), as well as combination of title, artist, and album.'
							)
					else:
						track_id = track_result[0][0]
						conn.close()
						print("Closed DB")
						print("error on attempting to update entry for the following entry", entry)
						raise ValueError('When attempting to update an entry in rbsync external database, rbsync was unable to look up entry ' +
							'using filename ("location" in rb), but did find a possible match searching with a combination of title, artist, and album.' +
							' However, this is currently not handled by RBSync.'
							)
						#filename was changed. Still working on handling this.
						# action.extend([entry])
				else:
					#should also verify that there is a valid track_id
					# cursor.execute('''UPDATE track set (?) = (?) and set (?) = (?) where id = (?);''', ("rating_ch_time", self.get_time(), "rating", entry["rating"], track_id ))
					if (len(action) == 4 and "play_count" in action and self.update_in_progress(rb_entry_id, "play_count", "") == False):
						old_local_play_count = track_result[0][4] or 0
						print("old_local_play_count:", old_local_play_count)
						new_local_play_count = old_local_play_count + 1
						sql_str = "UPDATE track SET " + action[0] + " = ?, " + action[2] + " = ?, local_play_count = ? where ID=?;"
						print("sql_str", sql_str)
						conn.execute(sql_str, (action[1], action[3], new_local_play_count, track_id, ))
					elif len(action) == 4:
						sql_str = "UPDATE track SET " + action[0] + " = ?, " + action[2] + " = ? where ID=?;"
						print("sql_str", sql_str)
						conn.execute(sql_str, (action[1], action[3], track_id, ))
					elif len(action) == 2:
						sql_str = "UPDATE track SET " + action[0] + " = ? where ID=?;"
						print("sql_str", sql_str)
						conn.execute(sql_str, (action[1], track_id, ))
					else:
						#shouldn't even get here. I just included this to help identify if I accidently coded something that gets here.
						conn.close()
						raise ValueError('I should not have encountered this else branch. The action list passed to update_rb_sync did not ' +
							'have 2 or 4 entries')
			else:
				raise ValueError("I'm not supposed to get here anymore")

				# #action is None. Right now, we assume action will be none if the point was to just insert a new entry into the rbsync database
				# # for row in track_result:
				# 	# istr = "row: " + ', '.join(map(str, row)) + "\ngenre: " + g
				# 	# print("\n\n" + istr)
				# if track_result == []:
				# 	# track_result
				# 	#we could insert all of the entry properties into the rbsynddb, but almost any entry attribute could be empty, we want to avoid unnessecary attributes
				# 	#this seems to save some space with sqlite. Will save more if using xmldb or mongodb, or something that handles sparse tables well
				# 	for key in entry:
				# 		if type(entry[key]) == type(1):
				# 			if entry[key] == 0: entry[key] = None
				# 		elif type(entry[key]) == type(1.00):
				# 			if (entry[key] <= 0.05): entry[key] = None
				# 		elif type(entry[key]) == type ("string"):
				# 			if (entry[key] == ""): entry[key] = None

				# 	if entry['title'] != None: print ("inserting new track " + (entry['title']))
				# 	cursor.execute('''INSERT INTO track (title, track_number, disc_number, track_total, disc_total, year, media_type, album_artist, 
				# 		duration, file_size, location, mountpoint, mtime, first_seen, last_seen, rating, play_count, last_played, bitrate, status, 
				# 		description, subtitle, comment, post_time, bpm, artist, composer, genre, album, hidden, local_play_count)
		 	# 		values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);''', 
		 	# 			(entry['title'], entry['track_number'], entry['disc_number'], entry['track_total'], entry['disc_total'], entry['year'], 
		 	# 			entry['media_type'], entry['album_artist'], entry['duration'], 
		 	# 			entry['file_size'], entry['location'], entry['mountpoint'], entry['mtime'], entry['first_seen'], entry['last_seen'], 
		 	# 			entry['rating'], entry['play_count'], entry['last_played'], entry['bitrate'], 
		 	# 			entry['status'], entry['description'], entry['subtitle'], entry['comment'], entry['post_time'], entry['bpm'], entry['artist'], 
		 	# 			entry['composer'], entry['genre'], entry['album'], entry['hidden'], entry['play_count'] ))
				# 	#note, local_play_count is initialized with current play_count value
				# 	track_id = cursor.lastrowid
				# else:
				# 	#if track is already in database, we don't insert a new track. But I will assign the resulting id to track_id for possible use below
				# 	track_id = track_result[0][0]

			print("committing db change")
			conn.commit()

		conn.close()
		print("Closed DB")



	def update_rbsync_db_with_new_tracks(self, action, data):
		#action and data are not expected to be used at this time. They are parameters passed when called from menu.

		#get rb_entries for all tracks.
		data = self.shell.props.library_source.props.base_query_model

		#convert the rb_entries in data (an array of arrays, with with inner array containing a hash with the rb_attributes in the first element)
		entries = self.get_rb_entries_from_data(data)

		conn = sqlite3.connect(rbsyncdb)
		cursor=conn.cursor()
		print ("Opened database successfully");
		value_for_change_time = self.get_time()

		# tables are only created if they don't exist
		self.create_rbsyncdb_tables(conn) 


		#we will not just iterate through every track. If the track already exists in the rbsync database, we will skip.
		for entry in entries:
			rb_entry_id = entry['rb_entry_id']
			# cursor.execute('''select id,title,artist,album from track where title=:t and artist=:a and album=:al;''', 
				# {"t": entry['title'], "a": entry['artist'], "al": entry['album']})
			cursor.execute('''select id,title,artist,album,local_play_count from track where location=:l;''', 
				{"l": entry['location']})
			track_result = cursor.fetchall()
			if len(track_result) != 1:
				#we could insert all of the entry properties into the rbsynddb, but almost any entry attribute could be empty, we want to avoid unnessecary attributes
				#this seems to save some space with sqlite. Will save more if using xmldb or mongodb, or something that handles sparse tables well
				attrs_to_enter = []
				if 'rb_entry_id' in entry: del (entry['rb_entry_id'])

				#would like to change this to a filter
				for key in entry:
					if key == 'play_count' or key == 'local_play_count':
						attrs_to_enter.append(key)
					elif (type(entry[key]) == type(1) and entry[key] != 0):
						attrs_to_enter.append(key)
					elif (type(entry[key]) == type(1.00) and entry[key] > 0.0):
						attrs_to_enter.append(key)
					elif (type(entry[key]) == type ("string") and entry[key] != "" and entry[key] != "Unknown"):
						attrs_to_enter.append(key)
				for key in ['artist', 'album', 'year', 'track_number', 'disc_number', 'track_total', 'disc_total', 'media_type', 'album_artist', 'composer', 'title', 'rating', 'play_count', 'bpm', 'genre']:
					if key in attrs_to_enter:
						key1 = key + "_ch_time"
						attrs_to_enter.append(key1)
						entry[key1] = value_for_change_time

				sql_query_string = 'INSERT INTO track (' + str.join(', ', attrs_to_enter) + ') VALUES (' + '?, ' * (len (attrs_to_enter) -1) + '?);'
				entries_to_enter = tuple(map (lambda attr: entry[attr], attrs_to_enter))

				print("sql_query_string", sql_query_string, entries_to_enter)
				if entry['title'] != None: print ("inserting new track " + (entry['title']))  #just for printing
				conn.execute(sql_query_string, entries_to_enter)

			# 	cursor.execute('''INSERT INTO track (title, track_number, disc_number, track_total, disc_total, year, media_type, album_artist, 
			# 		duration, file_size, location, mountpoint, mtime, first_seen, last_seen, rating, play_count, last_played, bitrate, status, 
			# 		description, subtitle, comment, post_time, bpm, artist, composer, genre, album, hidden, local_play_count)
	 	# 		values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);''', 
	 	# 			(entry['title'], entry['track_number'], entry['disc_number'], entry['track_total'], entry['disc_total'], entry['year'], 
	 	# 			entry['media_type'], entry['album_artist'], entry['duration'], 
	 	# 			entry['file_size'], entry['location'], entry['mountpoint'], entry['mtime'], entry['first_seen'], entry['last_seen'], 
	 	# 			entry['rating'], entry['play_count'], entry['last_played'], entry['bitrate'], 
	 	# 			entry['status'], entry['description'], entry['subtitle'], entry['comment'], entry['post_time'], entry['bpm'], entry['artist'], 
	 	# 			entry['composer'], entry['genre'], entry['album'], entry['hidden'], entry['play_count'] ))
			# 	#note, local_play_count is initialized with current play_count value
			# 	track_id = cursor.lastrowid
			# else:
			# 	#if track is already in database, we don't insert a new track.
			# 	#so I don't even need this else statement. That is why it is commented out.

			print("committing db change")
			conn.commit()

		conn.close()
		print("Closed DB")





	def get_local_changes_since(self, last_sync_time):
		conn = sqlite3.connect(rbsyncdb)
		# conn.row_factory = sqlite3.Row
		conn.row_factory = dict_factory

		cursor=conn.cursor()
		print ("Opened database successfully");
		data_to_upload = []
		cursor = conn.execute("SELECT * from track WHERE rbsync_id NOT NULL ORDER BY ID ASC;")
		for row in cursor:
			entry = {}
			track_sync_time = row['sync_time'] or 0
			# if track_sync_time < last_sync_time:
			if False:
				#queue entire entry, but skip if entry is NULL.
				# print (row['ID'])
				for key in row:
					if row[key] != None: entry[key] = row[key]
			else:
				#only queue data where attribute _ch_time value is > track_sync_time (or attribute _ch_time value is null)
				#NOTE, I SHOULD CONSIDER THAT SOME OTHER ATTRIBUTES, SUCH AS FILE SIZE, CHANGE.
				for key in row:
					if "_ch_time" in key and (row[key] == None or row[key] > track_sync_time) :
						attr = key[:(len(key) - 8)]
						if (row[attr] != None):
							entry[attr] = row[attr]
							if row[key] != None: entry[key] = row[key]
							#if 'play_count' has changed, we want to send that as well as 'local_play_count'
							if attr == 'play_count': entry['local_play_count'] = row['local_play_count']
			if len(entry) > 0:
				entry['rbsync_id'] = row['rbsync_id']
				data_to_upload.append(entry)


						# entry[:(key)] = 
						# print (key, attr, end='')
			# print (row['artist'])
			# string = "\nID = " + str(row["ID"]) + \
			# "\ntitle = " + row["title"] + \
			# "\nartist = " + row["artist"] + \
			# "\nalbum = " + row["album"] + "\n"
			# print(string)
			# print(entry, "\n")
		conn.close()
		print("Closed DB")
		return data_to_upload

		# return {"file": "Xena!"}


	def get_new_tracks(self):
		conn = sqlite3.connect(rbsyncdb)
		# conn.row_factory = sqlite3.Row
		conn.row_factory = dict_factory

		cursor=conn.cursor()
		print ("Opened database successfully");
		data_to_upload = []
		cursor = conn.execute("SELECT * from track where rbsync_id IS NULL ORDER BY ID ASC;")
		for row in cursor:
			entry = {}
			for key in row:
				if row[key] != None: entry[key] = row[key]
			data_to_upload.append(entry)
		conn.close()
		print("Closed DB")
		return data_to_upload



	def signal_rb_changes(self, updates):

		#need value to lookup rb entry with. location will be good.
		conn = sqlite3.connect(rbsyncdb)
		# conn.row_factory = sqlite3.Row
		conn.row_factory = dict_factory
		cursor=conn.cursor()
		print ("Opened database successfully");
		for entry in updates:
			identifier = None
			if 'ID' in entry:
				identifier = 'ID'
			elif 'rbsync_id' in entry:
				identifier = 'rbsync_id'
			else:
				print(entry)
				ValueError('Had trouble determining identifier from entry')
			# data_to_upload = []
			sql_query_string = "SELECT location from track where " + identifier + " = ?;"
			print('sql_query_string', sql_query_string, "identifier", str(entry[identifier]))
			cursor = conn.execute(sql_query_string, (entry[identifier], ) )
			#should be a single result.
			track_result = cursor.fetchall()
			if len(track_result) == 1:
				#add 'location' attr to entry
				entry['location'] = track_result[0]['location']
			else:
				print(entry)
				ValueError('Had trouble determining identifier from entry')
		conn.close()
		print("Closed DB")
		print('updates', updates)
		# return updates

		for entry in updates:		
			rb_entry = self.db.entry_lookup_by_location(entry['location'])
			title = rb_entry.get_string(RB.RhythmDBPropType.TITLE)
			old_artist = rb_entry.get_string(RB.RhythmDBPropType.ARTIST)
			print(title, old_artist)
			#assume single attr to update.
			attr_to_update = None
			for key in entry:
				if key != 'rbsync_id' and key != 'location':
					attr_to_update = key
			#handle property updates that are strings, ints, floats, whatever, separately
			new_prop = GObject.Value()
			if attr_to_update in props_that_are_longs:
				new_prop.init(GObject.TYPE_LONG)
				new_prop.set_long(entry[attr_to_update])
			elif attr_to_update in props_that_are_strings:
				new_prop.init(GObject.TYPE_STRING)
				new_prop.set_string(entry[attr_to_update])
			elif attr_to_update in props_that_are_double:
				new_prop.init(GObject.TYPE_DOUBLE)
				new_prop.set_duble(entry[attr_to_update])
			else:
				print (entry)
				raise ValueError('RBSync is not able to handle this type of RB Property Update.')

			rb_prop = self.get_RhythmDBPropType_from_string(attr_to_update)
			# artist.set_string("Xena12345")
			change = {"prop": rb_prop, 'new': new_prop}
			print("title", title)
			self.rbsync_update_track(rb_entry, change)		
		'hey'



	def write_rbsync_changes(self, updates):
		conn = sqlite3.connect(rbsyncdb)
		cursor=conn.cursor()
		print ("Opened database successfully");

		for entry in updates:
			identifier = None
			if 'ID' in entry:
				identifier = 'ID'
			elif 'rbsync_id' in entry:
				identifier = 'rbsync_id'
			else:
				print(entry)
				ValueError('Had trouble determining identifier from entry')
			# need to do something to verify that potential keys in entry are valid
			# sql_query_string = "UPDATE track SET " + action[0] + " = ?, " + action[2] + " = ?, local_play_count = ? where ID=?;"
			sql_query_string = "UPDATE track SET "
			i = 0
			fake_tuple = []
			len_entry = len(entry)
			for attr in entry:
				if attr != identifier:
					if i < len_entry - 2:
						sql_query_string+= str(attr) + " = ?,"
					else:
						# sql_query_string+= "? = ?"
						# sql_query_string+= str(attr) + " = " + str(entry[attr])
						sql_query_string+= str(attr) + " = ?"
					i+=1
					# fake_tuple.extend([attr, entry[attr]])
					# fake_tuple.append(str(attr))
					fake_tuple.append(int(entry[attr]))
			sql_query_string+= " where " + identifier + "= ?;"
			# sql_query_string+= " where ID = " + str(entry['ID']) + ";"
			fake_tuple.append(entry[identifier])
			tup = tuple(fake_tuple)
			print("sql_query_string", sql_query_string, tup)
			conn.execute(sql_query_string, tup)
			# UPDATE track SET rbsync_id = 796 where ID = 1;
			# conn.execute(sql_query_string)
			# else:
			# 	print("error on attempting to update entry for the following entry", entry)
			# 	raise ValueError('When attempting to update an entry in rbsync external database, rbsync was unable to look up entry ' +
			# 		'in rbsync external database. tried looking using ID.'
			# 		)
			print("committing db change")
			conn.commit()
		print("wrote new track data to rbsync database")
		conn.close()
		print("Closed DB")





	'''
		Sync function (sync)
		description:

			scan through entries in rbsync db
				find any entries where its last sync_time is older than any of its entry _ch_time values.
				queue those for syncing with cloud (probably json). If this is first sync, entire rb_sync db is sent to cloud
					-there are some values that don't change for entry, however, we could use these to identify files,
					 so whole db entry gets sent
					-a that has been added to the db after recent last sync is considered new data

			(if no changes queued, we still connect to cloud to see if there are changes in the cloud (from other devices))

			connect to cloud
				check if this is the first sync.
					If so, some identifiers need to be set up to associate device with particular identity for server.
					Entire rbsyncdb is sent to server.
					Server generates rbsync_id values for each entry, which prior to first sync should be empty.
						These will be sent back with its entry updates (below)
					Perhaps other tasks. 

				If not first sync: still send queued data. 

				Server then will determine if any other devices have more recent values for any attributes.
					Server sends json data back to client (such as rbsync process inside rhythmbox)
					If client is RBsync inside rhythmbox, rbsync submits updates to RB for RB to update its own db. 
						Rhthmbox DB changes signal rbsync to then write changes to rbsyncdb.

			Notes: It would be nice to change this to a streaming process.
	'''

	def sync_new_tracks(self, action, data):
		#all this does is find the tracks that have been added since the last sync and send these to server.
		#the server provides rbsync_id values that need to be saved to the rbsync db. Any other data that should be changed due to information
		#the server has will be provided in the normal sync operation.
		new_tracks = self.get_new_tracks()
		new_tracks = new_tracks[:100]
		# print("new_tracks", new_tracks)
		for entry in new_tracks:
			print ("\n\n", entry)

		#should check to see if there is any data to send, but program appears to function even if no tracks are sent
		post_request_data = {'rbsync_client_id' : rbsync_client_id, 'new_tracks' : new_tracks }

		headers = {'content-type': 'application/json'}

		r = requests.post(new_tracks_api, data=json.dumps(post_request_data), headers=headers)
		print(r.status_code, r.reason)
		print(r.text[:300] + '...')
		if r.status_code == 200:
			#thats good. #get new data. #should just be rbsync_id, which is only saved to rbsynd database, not rb database
			#should get sync_time from server, probably. Now, just use system.
			sync_time = self.get_time()
			new_data = json.loads(r.text) 
			non_rb_db_updates = []
			rb_db_updates = []
			print(new_data)
			if (new_data['changes'] != None):
				for entry in new_data['changes']:
					if 'rbsync_id' in entry and len(entry) == 2:
						non_rb_db_updates.append({'ID': entry['id'], 'rbsync_id' : entry['rbsync_id'], 'sync_time' : sync_time})
					else:
						print("error on recently added track", entry)
						raise ValueError('After sending recently added tracks to the server, an unexpected response was received. Was only expecting rbsync_id back'
							)					
				self.write_rbsync_changes(non_rb_db_updates)

		else:
			#should handle status code
			'not doing anything right now'



	def sync(self, action, data):
		last_sync_time = 1
		changes = self.get_local_changes_since(last_sync_time)
		#remove 'ID' from change entries.
		# for entry in changes:
			# print(entry)
			# del entry['ID']
		changes = changes[:2]
		# print("changes", changes)
		# for entry in changes:
		# 	print ("\n\n", entry)
		post_request_data = {'rbsync_client_id' : rbsync_client_id, 'changes' : changes }
		print('data', post_request_data)
		# r = requests.post("http://bugs.python.org", data={'number': 12524, 'type': 'issue', 'action': 'show'})
		# r = requests.post(syncup_api, data={'name': 'Xena!'})
		# r = requests.post(syncup_api, data=post_request_data)
		# print(r.status_code, r.reason)
		# print(r.text[:300] + '...')
		# # req = urllib2.Request('http://example.com/api/posts/create')
		# # req.add_header('Content-Type', 'application/json')

		# # response = urllib2.urlopen(req, json.dumps(post_request_data))
		# url = 'https://api.github.com/some/endpoint'
		# payload = {'some': 'data'}
		headers = {'content-type': 'application/json'}
		# return False



		r = requests.post(syncup_api, data=json.dumps(post_request_data), headers=headers)
		print(r.status_code, r.reason)
		print(r.text[:300] + '...')
		if r.status_code == 200:
			#thats good. #get any new data

			new_data = json.loads(r.text) 
			non_rb_db_updates = []
			rb_db_updates = []
			sync_time = self.get_time()

			#For a given track, if this is the first sync:
				#The new_data might only include the rbsync_id values, in which case there are no changes to internal rb database.
				#However, data might have rbsync_id values as well as rb database data to update. 
			#And if not the first sync for given track:
				#updates should all be rb db properties (or associated _ch_time attributes)

			print('new data from server', new_data)
			for entry in new_data['changes']:
				#entry is in form {'rbsync_id' : id, 'updates' : {...}}
				# print(json.dumps(entry))
				if 'rbsync_id' in entry:
					#update sync_time for track, even if there are no other updates
					non_rb_db_updates.append({'rbsync_id' : entry['rbsync_id'], 'sync_time' : sync_time})
					if len(entry) > 1:
						# v = {};
						# for key in entry:
						# 	if key != 'rbsync_id': 
						# 		v[key] = entry[key]
						# 		'blah'

						rb_db_updates.append(entry)
					# if len(v) > 1: v['rbsync_id'] = entry['rbsync_id']
				else:
					'problem'	

			print('rb_db_updates', rb_db_updates)
			if len(non_rb_db_updates) > 0:
				self.write_rbsync_changes(non_rb_db_updates)
			if len(rb_db_updates) > 0:
				self.signal_rb_changes(rb_db_updates)

		else:
			#should handle status code
			'not doing anything right now'


	def get_rb_entries_from_data(self, data):
		#this function takes input data (rb db data) and returns a array of hashes, each hash being all of the rb db attr of interest for rbsync

		#data is presumed to be an array of rb db entry row arrays, where entry info is in row[0] 
		#iterate using
			#for row in data:
				#entry = row[0]
				#get info from entry
		entries = []
		#iterate through all of library
		for row in data:
			#FYI: many of these values are basicall Null in the rb database. If a track has no rating, there is no <rating> entry for track in rythmdb.xml 
			#However, the line below that gets the rating will return a value of 0.00 for a track that has no rating.
			entry 		= row[0]
			artist 		= entry.get_string(RB.RhythmDBPropType.ARTIST)
			title 		= entry.get_string(RB.RhythmDBPropType.TITLE)
			album		= entry.get_string(RB.RhythmDBPropType.ALBUM)
			year			= entry.get_ulong(RB.RhythmDBPropType.DATE)
			track_total	= entry.get_ulong(RB.RhythmDBPropType.TRACK_TOTAL)
			disc_total	= entry.get_ulong(RB.RhythmDBPropType.DISC_TOTAL)
			media_type	= entry.get_string(RB.RhythmDBPropType.MEDIA_TYPE)
			album_artist	= entry.get_string(RB.RhythmDBPropType.ALBUM_ARTIST)
			keywordsRBRef	= self.db.entry_keywords_get(entry)
			keywords = []
			for a_keyword in keywordsRBRef:
				keywords.append(RB.RefString.get(a_keyword))
			composer 		= entry.get_string(RB.RhythmDBPropType.COMPOSER)
			genre 		= entry.get_string(RB.RhythmDBPropType.GENRE)
			entry_typeRB 	= entry.get_entry_type()#NOT NULL,
			entry_type	= entry_typeRB.get_name()
			rb_entry_id 	= entry.get_ulong(RB.RhythmDBPropType.ENTRY_ID)
			hidden 		= entry.get_boolean(RB.RhythmDBPropType.HIDDEN)
			track_number 	= entry.get_ulong(RB.RhythmDBPropType.TRACK_NUMBER)
			disc_number 	= entry.get_ulong(RB.RhythmDBPropType.DISC_NUMBER)
			duration 		= entry.get_ulong(RB.RhythmDBPropType.DURATION)
			file_size 	= entry.get_uint64(RB.RhythmDBPropType.FILE_SIZE)
			location 		= entry.get_string(RB.RhythmDBPropType.LOCATION)	 #NOT NULL,
			mountpoint 	= entry.get_string(RB.RhythmDBPropType.MOUNTPOINT)
			mtime 		= entry.get_ulong(RB.RhythmDBPropType.MTIME)
			first_seen 	= entry.get_ulong(RB.RhythmDBPropType.FIRST_SEEN)
			last_seen 	= entry.get_ulong(RB.RhythmDBPropType.LAST_SEEN)
			rating 		= entry.get_double(RB.RhythmDBPropType.RATING)
			play_count 	= entry.get_ulong(RB.RhythmDBPropType.PLAY_COUNT)
			last_played 	= entry.get_ulong(RB.RhythmDBPropType.LAST_PLAYED)
			bitrate 		= entry.get_ulong(RB.RhythmDBPropType.BITRATE)
			status 		= entry.get_ulong(RB.RhythmDBPropType.STATUS)
			description 	= entry.get_string(RB.RhythmDBPropType.DESCRIPTION)
			subtitle 		= entry.get_string(RB.RhythmDBPropType.SUBTITLE)
			bpm 			= entry.get_double(RB.RhythmDBPropType.BEATS_PER_MINUTE)
			comment 		= entry.get_string(RB.RhythmDBPropType.COMMENT)
			post_time 	= entry.get_ulong(RB.RhythmDBPropType.POST_TIME)

			info = {
				"artist":artist, "composer":composer, "genre":genre, "entry_type":entry_type, "title":title, "rb_entry_id":rb_entry_id, 
				"hidden":hidden, "bpm": bpm, "track_number":track_number, "disc_number":disc_number, "duration":duration, "file_size":file_size, 
				"location":location, "mountpoint":mountpoint, "mtime":mtime, "first_seen":first_seen, "last_seen":last_seen, "rating":rating, 
				"play_count":play_count, "last_played":last_played, "bitrate":bitrate, "status":status, "description":description, 
				"subtitle":subtitle, "comment":comment, "post_time":post_time, "keywords":keywords, "album":album, "year":year, 
				"track_total":track_total, "disc_total":disc_total, "media_type":media_type, "album_artist":album_artist
			}
			entries.append(info)

		#done scanning through entries from rhythmdb
		# if entries != []: print("first entry", entries[0]) 
		return(entries)

	def add_or_update_rbsyncdb(self, action, data):
		# shell = self.object
		print("action", action, "data", data)

		#when run from the db_load_complete function, action is none and data is whatever I passed, the RhythDBTree last time I edited.
		#when run from the tools menu, action is Gio.SimpleAction and data is None
		#when run after receiving an entry update signal, action is a list of size 4 and data is that single entry, wrapped in two lists: ([[entry]])

		# if type (action) == <class 'gi.types.GObjectMeta'> :
		# type (action)
		# if type (action) == type (Gio.SimpleAction):

		if type (action) == type ([]):
		# if (action) == Gio.SimpleAction :
			print ("This appears to be call to self.sync after entry property was changed")

		elif hasattr(action, 'get_name') and action.get_name() == 'rhythmbox-sync':
		# elif data == None :
			print("This appears to be general call to self.sync from tools menu")
			# blah = action.get_name()
			# print("action blah", blah)
			action = None
			data = self.shell.props.library_source.props.base_query_model

		else:
			print("This appears to be a call to self.sync upon database load")
			action = None
			data = self.shell.props.library_source.props.base_query_model
			# print("Action not Gio.SimpleAction or was not matched properly")

		# keywords = self.db.keywords_get(RB.RhythmDBPropType.KEYWORD)
		# print("Keywords", keywords)
		entries = []
		#iterate through all of library
		for row in data:
			entry 		= row[0]
			artist 		= entry.get_string(RB.RhythmDBPropType.ARTIST)
			title 		= entry.get_string(RB.RhythmDBPropType.TITLE)
			album		= entry.get_string(RB.RhythmDBPropType.ALBUM)
			year			= entry.get_ulong(RB.RhythmDBPropType.DATE)
			track_total	= entry.get_ulong(RB.RhythmDBPropType.TRACK_TOTAL)
			disc_total	= entry.get_ulong(RB.RhythmDBPropType.DISC_TOTAL)
			media_type	= entry.get_string(RB.RhythmDBPropType.MEDIA_TYPE)
			album_artist	= entry.get_string(RB.RhythmDBPropType.ALBUM_ARTIST)
			keywordsRBRef	= self.db.entry_keywords_get(entry)
			keywords = []
			for a_keyword in keywordsRBRef:
				keywords.append(RB.RefString.get(a_keyword))
			composer 		= entry.get_string(RB.RhythmDBPropType.COMPOSER)
			genre 		= entry.get_string(RB.RhythmDBPropType.GENRE)
			entry_typeRB 	= entry.get_entry_type()#NOT NULL,
			entry_type	= entry_typeRB.get_name()
			rb_entry_id 	= entry.get_ulong(RB.RhythmDBPropType.ENTRY_ID)
			hidden 		= entry.get_boolean(RB.RhythmDBPropType.HIDDEN)
			track_number 	= entry.get_ulong(RB.RhythmDBPropType.TRACK_NUMBER)
			disc_number 	= entry.get_ulong(RB.RhythmDBPropType.DISC_NUMBER)
			duration 		= entry.get_ulong(RB.RhythmDBPropType.DURATION)
			file_size 	= entry.get_uint64(RB.RhythmDBPropType.FILE_SIZE)
			location 		= entry.get_string(RB.RhythmDBPropType.LOCATION)	 #NOT NULL,
			mountpoint 	= entry.get_string(RB.RhythmDBPropType.MOUNTPOINT)
			mtime 		= entry.get_ulong(RB.RhythmDBPropType.MTIME)
			first_seen 	= entry.get_ulong(RB.RhythmDBPropType.FIRST_SEEN)
			last_seen 	= entry.get_ulong(RB.RhythmDBPropType.LAST_SEEN)
			rating 		= entry.get_double(RB.RhythmDBPropType.RATING)
			play_count 	= entry.get_ulong(RB.RhythmDBPropType.PLAY_COUNT)
			last_played 	= entry.get_ulong(RB.RhythmDBPropType.LAST_PLAYED)
			bitrate 		= entry.get_ulong(RB.RhythmDBPropType.BITRATE)
			status 		= entry.get_ulong(RB.RhythmDBPropType.STATUS)
			description 	= entry.get_string(RB.RhythmDBPropType.DESCRIPTION)
			subtitle 		= entry.get_string(RB.RhythmDBPropType.SUBTITLE)
			bpm 			= entry.get_double(RB.RhythmDBPropType.BEATS_PER_MINUTE)
			comment 		= entry.get_string(RB.RhythmDBPropType.COMMENT)
			post_time 	= entry.get_ulong(RB.RhythmDBPropType.POST_TIME)

			info = {
				"artist":artist, "composer":composer, "genre":genre, "entry_type":entry_type, "title":title, "rb_entry_id":rb_entry_id, 
				"hidden":hidden, "bpm": bpm, "track_number":track_number, "disc_number":disc_number, "duration":duration, "file_size":file_size, 
				"location":location, "mountpoint":mountpoint, "mtime":mtime, "first_seen":first_seen, "last_seen":last_seen, "rating":rating, 
				"play_count":play_count, "last_played":last_played, "bitrate":bitrate, "status":status, "description":description, 
				"subtitle":subtitle, "comment":comment, "post_time":post_time, "keywords":keywords, "album":album, "year":year, 
				"track_total":track_total, "disc_total":disc_total, "media_type":media_type, "album_artist":album_artist, "action": action
			}
			entries.append(info)

		#done scanning through entries from rhythmdb
		# if entries != []: print("first entry", entries[0]) 
		self.update_rbsync_db(entries)

		print("Hey")

	def test(self, action, data):
		print ("running self.test()")
		entry = self.db.entry_lookup_by_id(82)
		title = entry.get_string(RB.RhythmDBPropType.TITLE)
		old_artist = entry.get_string(RB.RhythmDBPropType.ARTIST)
		artist = GObject.Value()
		artist.init(GObject.TYPE_STRING)
		artist.set_string("Xena" + old_artist)
		# artist.set_string("Xena12345")
		change = {"prop": RB.RhythmDBPropType.ARTIST, 'new': artist}
		print("title", title)
		self.rbsync_update_track(entry, change)

	def do_activate(self):
		self.shell = self.object
		self.db = self.shell.props.db
		self.rbsync_updates_in_progress = {}
		action = Gio.SimpleAction(name='rhythmbox-sync')
		action.connect('activate', self.sync)
		# action.connect('activate', self.sync_new_tracks)

		# sync_new_tracks
		# action.connect('activate', self.update_rbsync_db_with_new_tracks)

		app = Gio.Application.get_default()
		app.add_action(action)

		menu_item = Gio.MenuItem()
		menu_item.set_label("Sync library with cloud")
		menu_item.set_detailed_action('app.rhythmbox-sync')

		app.add_plugin_menu_item('tools', 'sync-menu-item', menu_item)
		print("Hello World")
		self.connect_signals()


	def do_deactivate(self):
		# shell = self.object
		self.shell.disconnect (self.ecs_id)
		self.shell = None
		self.db = None
		self.rbsync_updates_in_progress = None
		del self.ecs_id
		app = Gio.Application.get_default()
		app.remove_action('rhythmbox-sync')
		app.remove_plugin_menu_item('tools', 'sync-menu-item')

GObject.type_register(RBSync)

