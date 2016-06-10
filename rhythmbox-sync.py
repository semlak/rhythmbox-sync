from gi.repository import Gio, GLib, Gtk, GObject, Peas
from gi.repository import RB
from os.path import expanduser
from time import time
import sqlite3
import math


home = expanduser("~")
rbsyncdb = home + "/.local/share/rhythmbox/rbsync.db"


class RBSync(GObject.Object, Peas.Activatable):
	__gtype_name__ = 'RBSync'
	object = GObject.property(type=GObject.Object)


	def __init__(self):
		GObject.Object.__init__(self)
		# self.shell = self.object
		# self.connect_signals()

		# self.db = self.shell.props.db
		# print(dir(self.shell))
		# print("self:" , dir(self))

	def get_time(self):
		return math.floor(time())



	def connect_signals(self):
		shell = self.object
		# print(shell, dir(shell))
		db = shell.props.db
		# self.db = self.shell.props.db
		# self.db.connect ('entry-changed', self.change_notify)

		# ecs is "entry-changed signal"
		self.ecs_id = db.connect ('entry-changed', self.change_notify)
		# should also handle entry-added and entry-deleted

		self.lcs_id = db.connect ('load-complete', self.db_load_complete_notify)

	def db_load_complete_notify (self, dbtree):
		self.sync(None, dbtree)

	def change_notify (self, dbtree, entry, entryChanges):
	# def change_notify():
		print("Hey. Change notification!")
		for change in entryChanges:
			print(change)
			print(change.prop)
			print(change.old)
			print(change.new)
			print(entry.get_string(RB.RhythmDBPropType.TITLE))
			update = None

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

			update = switch.get(change.prop, None)
			print("update", update)

			if update != None:
				#this is a property we want to update, but we also need to update the ch_time for the property
				action = [update, change.new, update+"_ch_time", self.get_time()]
				self.sync(action, [[entry]])
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
				update = switch.get(change.prop, None)
				if update != None:
					#this is a property we want to update in the rbsyncdb, but don't need or even have a ch_time property
					action = [update, change.new]
					self.sync(action, [[entry]])
				# else: 
					#this is just a case where the property updated in rhythmbox is not one where rbsync cares about.




	def create_rbsyncdb_tables(self, conn):
		conn.execute('''CREATE TABLE IF NOT EXISTS track (
			ID 			integer	PRIMARY KEY NOT NULL,
			location		TEXT,
			artist		text,
			album		text,
			album_date	integer,
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
			hidden		integer
			rbsync_id		integer,
			local_play_count		integer,
			artist_ch_time			integer,
			album_ch_time			integer,
			album_date_ch_time		integer,
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
						print("error on attempting to update entry for the following entry", entry)
						raise ValueError('When attempting to update an entry in rbsync external database, rbsync was unable to look up entry ' +
							'in rbsync external database. tried looking using filename ("location" in rb), as well as combination of title, artist, and album.'
							)
					else:
						track_id = track_result[0][0]
						conn.close()
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
					if (len(action) == 4 and "play_count" in action ):
						old_local_play_count = track_result[0][4]
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
				#action is None. Right now, we assume action will be none if the point was to just insert a new entry into the rbsync database
				# for row in track_result:
					# istr = "row: " + ', '.join(map(str, row)) + "\ngenre: " + g
					# print("\n\n" + istr)
				if track_result == []:
					# track_result
					print ("inserting new track " + entry['title'])
					cursor.execute('''INSERT INTO track (title, track_number, disc_number, track_total, disc_total, album_date, media_type, album_artist, 
						duration, file_size, location, mountpoint, mtime, first_seen, last_seen, rating, play_count, last_played, bitrate, status, 
						description, subtitle, comment, post_time, bpm, artist, composer, genre, album, hidden, local_play_count)
		 			values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);''', 
		 				(entry['title'], entry['track_number'], entry['disc_number'], entry['track_total'], entry['disc_total'], entry['album_date'], 
		 				entry['media_type'], entry['album_artist'], entry['duration'], 
		 				entry['file_size'], entry['location'], entry['mountpoint'], entry['mtime'], entry['first_seen'], entry['last_seen'], 
		 				entry['rating'], entry['play_count'], entry['last_played'], entry['bitrate'], 
		 				entry['status'], entry['description'], entry['subtitle'], entry['comment'], entry['post_time'], entry['bpm'], entry['artist'], 
		 				entry['composer'], entry['genre'], entry['album'], entry['hidden'], entry['play_count'] ))
					#note, local_play_count is initialized with current play_count value
					track_id = cursor.lastrowid
				else:
					#if track is already in database, we don't insert a new track. But I will assign the resulting id to track_id for possible use below
					track_id = track_result[0][0]


			conn.commit()

		conn.close()




	def sync(self, action, data):
		shell = self.object
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
			data = shell.props.library_source.props.base_query_model

		else:
			print("This appears to be a call to self.sync upon database load")
			action = None
			data = shell.props.library_source.props.base_query_model
			# print("Action not Gio.SimpleAction or was not matched properly")

		# keywords = shell.props.db.keywords_get(RB.RhythmDBPropType.KEYWORD)
		# print("Keywords", keywords)
		entries = []
		#iterate through all of library
		for row in data:
			entry 		= row[0]
			artist 		= entry.get_string(RB.RhythmDBPropType.ARTIST)
			title 		= entry.get_string(RB.RhythmDBPropType.TITLE)
			album		= entry.get_string(RB.RhythmDBPropType.ALBUM)
			album_date	= entry.get_ulong(RB.RhythmDBPropType.DATE)
			track_total	= entry.get_ulong(RB.RhythmDBPropType.TRACK_TOTAL)
			disc_total	= entry.get_ulong(RB.RhythmDBPropType.DISC_TOTAL)
			media_type	= entry.get_string(RB.RhythmDBPropType.MEDIA_TYPE)
			album_artist	= entry.get_string(RB.RhythmDBPropType.ALBUM_ARTIST)
			keywordsRBRef	= shell.props.db.entry_keywords_get(entry)
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
				"subtitle":subtitle, "comment":comment, "post_time":post_time, "keywords":keywords, "album":album, "album_date":album_date, 
				"track_total":track_total, "disc_total":disc_total, "media_type":media_type, "album_artist":album_artist, "action": action
			}
			entries.append(info)
		
		#done scanning through entries from rhythmdb
		# if entries != []: print("first entry", entries[0]) 
		self.update_rbsync_db(entries)

		print("Hey")


	def do_activate(self):
		action = Gio.SimpleAction(name='rhythmbox-sync')
		action.connect('activate', self.sync)

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
		app = Gio.Application.get_default()
		app.remove_action('rhythmbox-sync')
		app.remove_plugin_menu_item('tools', 'sync-menu-item')
		self.shell = None
		self.db = None
		# shell.disconnect (self.ecs_id)
		# del self.ecs_id

GObject.type_register(RBSync)

