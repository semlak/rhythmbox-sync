from gi.repository import Gio, GLib, Gtk, GObject, Peas
from gi.repository import RB
import sqlite3
import math
from os.path import expanduser
from time import time

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
		self.sync("fake", dbtree)

	def change_notify (self, dbtree, entry, entryChanges):
	# def change_notify():
		print("Hey. Change notification!")
		for change in entryChanges:
			print(change)
			print((change.prop))
			print(change.old)
			print(change.new)
			print(entry.get_string(RB.RhythmDBPropType.TITLE))

			if (change.prop == RB.RhythmDBPropType.RATING):
				
				# print("rating being updated")
			# print(dir(dbtree))
			# print(dir(RB))

			#this works
			# newVal = RB.RefString ("silly_keyword") 
			# dbtree.entry_keyword_add(entry, newVal)

			# dbtree.entry_keyword_add(entry, rb_refstring_new ( "date_rated")) #this doesn't work

			#these seem to work
			# hasRating 		= dbtree.entry_keyword_has(entry, RB.RefString("get_string"))
			# hasDateRated 	= dbtree.entry_keyword_has(entry, RB.RefString("date_rated"))
			# hasSillyKeyword 	= dbtree.entry_keyword_has(entry, RB.RefString("silly_keyword"))
			# print(hasRating, hasDateRated)
			# print(hasSillyKeyword)
			# dbtree.entry_set(entry, )
			# print("entry is now", dir(entry))


		# if rb.entry_equal(entry, self.entry):
			# self.emit ('lyrics-ready', self.entry, metadata)
		# self.player_cb_ids = ( self.sp.connect ('playing-changed', self.playing_changed_cb),
		# 	self.sp.connect ('playing-song-changed', self.playing_changed_cb))
		# self.tab_cb_ids = []


	def create_rbsyncdb_tables(self, conn):
		conn.execute('''CREATE TABLE IF NOT EXISTS artist (
			ID 			integer	PRIMARY KEY NOT NULL,
			artist_name	text,
			artist_name_ch_date	real
		);''')

		conn.execute('''CREATE TABLE IF NOT EXISTS album (
			ID 			integer	PRIMARY KEY	NOT NULL,
			album_name	text,
			album_date	real,
			track_total	real,
			disc_total	real,
			media_type	text,
			album_artist	text,
			album_name_ch_date		real,
			album_date_ch_date		real,
			track_total_ch_date		real,
			disc_total_ch_date		real,
			media_type_ch_date		real,
			album_artist_ch_date	real
		);''')
		conn.execute('''CREATE TABLE IF NOT EXISTS keyword (
			ID 			integer	PRIMARY KEY	NOT NULL,
			keyword_name	text
		);''')
		conn.execute('''CREATE TABLE IF NOT EXISTS composer (
			ID 			integer	PRIMARY KEY	NOT NULL,
			composer_name	text
		);''')
		conn.execute('''CREATE TABLE IF NOT EXISTS genre (
			ID 			integer	PRIMARY KEY	NOT NULL,
			genre_name	text
		);''')
		conn.execute('''CREATE TABLE IF NOT EXISTS entry_type (
			ID 			integer	PRIMARY KEY	NOT NULL,
			type			text
		);''')
		conn.execute('''CREATE TABLE IF NOT EXISTS track (
			ID 			integer	PRIMARY KEY	NOT NULL,
			rb_entry_id	integer,
			title		TEXT,
			track_number	integer,
			disc_number	integer,
			duration		REAL,
			file_size		REAL,
			location		TEXT,
			mountpoint	TEXT,
			mtime		REAL,
			first_seen	REAL,
			last_seen		REAL,
			rating		REAL,
			play_count	REAL,
			last_played	REAL,
			bitrate		REAL,
			status		REAL,
			description 	TEXT,
			subtitle 		TEXT,
			bpm			REAL,
			comment 		TEXT,
			post_time		REAL,
			artist_id 	integer,
			keyword_id 	integer,
			composer_id 	integer,
			genre_id 		integer,
			entry_type_id	integer,
			album_id		integer,
			title_ch_date			real,
			track_number_ch_date	real,
			disc_number_ch_date		real,
			rating_ch_date			REAL,
			play_count_ch_date		REAL,
			artist_id_ch_date		REAL,
			keyword_id_ch_date		REAL,
			composer_id_ch_date		REAL,
			genre_id_ch_date		REAL,
			entry_type_id_ch_date	REAL,
			album_id_ch_date		REAL,			
			FOREIGN KEY (entry_type_id) REFERENCES entry_type(id)			
			FOREIGN KEY (artist_id) REFERENCES artist(id)
			FOREIGN KEY (keyword_id) REFERENCES keword(id)
			FOREIGN KEY (composer_id) REFERENCES composer(id)
			FOREIGN KEY (genre_id) REFERENCES genre(id)
			FOREIGN KEY (album_id) REFERENCES album(id)
		);''')
		# print ("Tables created successfully");



	def update_rbsync_db(self, entries):
		conn = sqlite3.connect(rbsyncdb)
		cursor=conn.cursor()
		print ("Opened database successfully");

		# tables are only created if they don't exist
		self.create_rbsyncdb_tables(conn) 
		for entry in entries:
			entryTime = self.get_time()
			# artist=conn.execute("select id from artist where artist_name = (?)", (entry["artist"]))
			a = entry['artist']
			artist_id = None
			
			cursor.execute('''select id,artist_name from artist where artist_name = (?);''', (a,))
			artist_result = cursor.fetchall()
			# print("artist_entry", artist)
			# print (artist_result)
			# print (dir(artist))
			if artist_result != []:
				# print("found artist " + a + " in db")
				for row in artist_result:
					# print(row, row[0])
					artist_id = row[0]
			else:
				print("inserting artist " + a + " into database")
				cursor.execute('''INSERT INTO artist (artist_name, artist_name_ch_date) values (?,?);''', (a, entryTime))
				artist_id = cursor.lastrowid
			# print("artist", entry["artist"])
			# print ("artist_id:", artist_id)

			c = entry['composer']
			composer_id = None
			cursor.execute('''select id,composer_name from composer where composer_name = (?);''', (c,))
			composer_result = cursor.fetchall()
			# print("composer_entry", composer)
			# print (composer_result)
			# print (dir(composer))
			if composer_result != []:
				# print("found composer " + c + " in db")
				for row in composer_result:
					# print(row, row[0])
					composer_id = row[0]
			else:
				print("inserting composer " + c + " into database")
				cursor.execute('''INSERT INTO composer (composer_name) values (?);''', (c,))
				composer_id = cursor.lastrowid
			# print ("composer_id:", composer_id)

			g = entry['genre']
			genre_id = None
			cursor.execute('''select id,genre_name from genre where genre_name = (?);''', (g,))
			genre_result = cursor.fetchall()
			# print("genre_entry", genre)
			# print (genre_result)
			# print (dir(genre))
			if genre_result != []:
				# print("found genre " + g + " in db")
				for row in genre_result:
					# print(row, row[0])
					genre_id = row[0]
			else:
				print("inserting genre " + g + " into database")
				cursor.execute('''INSERT INTO genre (genre_name) values (?);''', (g,))
				genre_id = cursor.lastrowid
			# print ("genre_id:", genre_id)

			e = entry['entry_type']
			entry_type_id = None
			cursor.execute('''select id,type from entry_type where type = (?);''', (e,))
			entry_type_result = cursor.fetchall()
			# print("entry_type_entry", entry_type)
			# print (entry_type_result)
			# print (dir(entry_type))
			if entry_type_result != []:
				# print("found entry_type " + e + " in db")
				for row in entry_type_result:
					# print(row, row[0])
					entry_type_id = row[0]
			else:
				print("inserting entry_type " + e + " into database")
				cursor.execute('''INSERT INTO entry_type (type) values (?);''', (e,))
				entry_type_id = cursor.lastrowid
			# print("entry_type", entry["entry_type"])
			# print ("entry_type_id:", entry_type_id)

			a = entry['album']
			album_id = None
			
			cursor.execute('''select id,album_name from album where album_name = (?);''', (a,))
			album_result = cursor.fetchall()
			# print("album_entry", album)
			# print (album_result)
			# print (dir(album))
			if album_result != []:
				# print("found album " + a + " in db")
				for row in album_result:
					# print(row, row[0])
					album_id = row[0]
			else:
				print("inserting album " + a + " into database")
				cursor.execute('''INSERT INTO album (album_name, album_date, track_total, disc_total, media_type, 
					album_artist, album_name_ch_date, album_date_ch_date, track_total_ch_date, disc_total_ch_date, 
					media_type_ch_date, album_artist_ch_date) 
					values (?, ?, ?, ?, ?, ?, ? , ?, ?, ?, ?, ?);''', 
					(a, entry['album_date'], entry['track_total'], entry['disc_total'], entry['media_type'], 
					entry['album_artist'], entryTime, entryTime, entryTime, entryTime, entryTime, entryTime))
				album_id = cursor.lastrowid
			# print("album", entry["album"])
			# print ("album_id:", album_id)
# keyword_id, bpm

			# cursor.execute('''select id,title,rb_entry_id,artist_id,album_id from track where title=:t and rb_entry_id=:r and artist_id=:a and album_id=:al;''', 
				# {"t": entry['title'], "r": entry["rb_entry_id"], "a": artist_id, "al": album_id})

			cursor.execute('''select id,title,artist_id,album_id from track where title=:t and artist_id=:a and album_id=:al;''', 
				{"t": entry['title'], "a": artist_id, "al": album_id})
			track_result = cursor.fetchall()
			# for row in track_result:
				# istr = "row: " + ', '.join(map(str, row)) + "\ngenre: " + g
				# print("\n\n" + istr)
			if track_result == []:
				# track_result
				print ("inserting new track " + entry['title'])
				cursor.execute('''INSERT INTO track (title, track_number, disc_number, duration, file_size, location, mountpoint, 
					mtime, first_seen, last_seen, rating, play_count, last_played, bitrate, status, description, 
					subtitle, comment, post_time, artist_id, composer_id, genre_id,  entry_type_id, album_id, title_ch_date, track_number_ch_date, disc_number_ch_date, rating_ch_date, play_count_ch_date, artist_id_ch_date, keyword_id_ch_date, composer_id_ch_date, genre_id_ch_date, entry_type_id_ch_date, album_id_ch_date)
	 			values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);''', (entry['title'], entry['track_number'], entry['disc_number'], entry['duration'], 
	 				entry['file_size'], entry['location'], entry['mountpoint'], entry['mtime'], entry['first_seen'], entry['last_seen'], 
	 				entry['rating'], entry['play_count'], entry['last_played'], entry['bitrate'], 
	 				entry['status'], entry['description'], entry['subtitle'], entry['comment'], entry['post_time'], artist_id, 
	 				composer_id, genre_id, entry_type_id, album_id, entryTime, entryTime, entryTime, entryTime, entryTime, entryTime, entryTime, entryTime, entryTime, entryTime, entryTime ))

			# cursor.execute('''INSERT INTO track (rb_entry_id, title, location, rating, play_count, last_played, artist_id, composer_id, genre_id, album_id) values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);''', (entry['rb_entry_id'], entry['title'], entry['location'], entry['rating'], entry['play_count'], entry['last_played'], artist_id, composer_id, genre_id, album_id ))
			#cursor.execute('''INSERT INTO track (title, rating, play_count, artist_id, genre_id, album_id) values ();''', (entry['title'], entry['rating'], entry['play_count'], artist_id, genre_id, album_id ))
			# cursor.execute('''INSERT INTO track (title)      values (?);''', (entry['title'],))

			# cursor.execute('''INSERT INTO genre (genre_name) values (?);''', (g,))

# rb_entry_id, title, track_number, disc_number, duration, file_size, location, mountpoint, mtime, first_seen, last_seen, rating, rating_date, play_count,
 # play_count_date, last_played, bitrate, status, description, subtitle, bpm, comment, post_time, artist_id, keyword_id, composer_id, genre_id, 
 # entry_type_id, album_id


			conn.commit()

		conn.close()


	def sync(self, action, data):
		shell = self.object
		# keywords = shell.props.db.keywords_get(RB.RhythmDBPropType.KEYWORD)
		# print("Keywords", keywords)
		entries = []
		#iterate through all of library
		for row in shell.props.library_source.props.base_query_model:
			entry 		= row[0]
			artist 		= entry.get_string(RB.RhythmDBPropType.ARTIST)
			title 		= entry.get_string(RB.RhythmDBPropType.TITLE)
			
			#album info
			album		= entry.get_string(RB.RhythmDBPropType.ALBUM)
			album_date	= entry.get_ulong(RB.RhythmDBPropType.DATE)
			track_total	= entry.get_ulong(RB.RhythmDBPropType.TRACK_TOTAL)
			disc_total	= entry.get_ulong(RB.RhythmDBPropType.DISC_TOTAL)
			media_type	= entry.get_string(RB.RhythmDBPropType.MEDIA_TYPE)
			album_artist	= entry.get_string(RB.RhythmDBPropType.ALBUM_ARTIST)

			keywordsRBRef	= shell.props.db.entry_keywords_get(entry)
			keywords = []
			# print("keywords:")
			for a_keyword in keywordsRBRef:
				# astring = shell.rb_refstring_get(a_keyword)
				# print (RB.RefString.get(a_keyword), end="",flush=True)
				keywords.append(RB.RefString.get(a_keyword))
			# print("\n")
			# print (keyword, "\n")

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
			# rating1 = entry->rating
			# # rating_date	REAL,
			play_count 	= entry.get_ulong(RB.RhythmDBPropType.PLAY_COUNT)
			last_played 	= entry.get_ulong(RB.RhythmDBPropType.LAST_PLAYED)
			bitrate 		= entry.get_ulong(RB.RhythmDBPropType.BITRATE)
			status 		= entry.get_ulong(RB.RhythmDBPropType.STATUS)
			description 	= entry.get_string(RB.RhythmDBPropType.DESCRIPTION)
			subtitle 		= entry.get_string(RB.RhythmDBPropType.SUBTITLE)
			if title == "La Llave":
				# bpm = entry.get_double(RB.RhythmDBPropType.BPM)
				bpm = entry.get_double(RB.RhythmDBPropType.RATING)
				# print (bpm, "\n")
			comment 		= entry.get_string(RB.RhythmDBPropType.COMMENT)
			post_time 	= entry.get_ulong(RB.RhythmDBPropType.POST_TIME)
			# print("entry_type", dir(entry_type))
			# print("entry_type", (entry_type.get_name()))
			info = {
				"artist":artist, "composer":composer, "genre":genre, "entry_type":entry_type, "title":title, "rb_entry_id":rb_entry_id, 
				"hidden":hidden, "track_number":track_number, "disc_number":disc_number, "duration":duration, "file_size":file_size, 
				"location":location, "mountpoint":mountpoint, "mtime":mtime, "first_seen":first_seen, "last_seen":last_seen, "rating":rating, 
				"play_count":play_count, "last_played":last_played, "bitrate":bitrate, "status":status, "description":description, 
				"subtitle":subtitle, "comment":comment, "post_time":post_time, "keywords":keywords, "album":album, "album_date":album_date, 
				"track_total":track_total, "disc_total":disc_total, "media_type":media_type, "album_artist":album_artist
			}
			print(info,"\n\n")
			entries.append(info)
		
		#done scanning through entries from rhythmdb
		self.update_rbsync_db(entries)

		db = shell.props.db
		# print (dir (db))
		# print(db.entry_get)
		# entry_change_id = song_info.connect('notify::current-entry', self.entry_changed)

		# set_waiting_signal (G_OBJECT (db), "entry-changed")
		# set_entry_string (db, b, RHYTHMDB_PROP_ARTIST, "x")
		# rhythmdb_commit (db)
		# wait_for_signal ()
		print("Hey")

	#partial query
		# db = shell.props.db
		# query_model = RB.RhythmDBQueryModel.new_empty(db)
		# query = GLib.PtrArray()
		# query0 = GLib.PtrArray()
		# query1 = GLib.PtrArray()
		# db.do_full_query_parsed(query_model, query1)
		# db.query_append_params( query, RB.RhythmDBQueryType.EQUALS, RB.RhythmDBPropType.ARTIST, 'Van Cliburn' )
		# db.query_append_params( query0, RB.RhythmDBQueryType.EQUALS, RB.RhythmDBPropType.ARTIST, '' )
		# db.query_append_params( query1, RB.RhythmDBQueryType.NOT_EQUAL, RB.RhythmDBPropType.ARTIST, '' )
		# db.query_concatenate(query0, query1)
		# db.query_append_params( query, RB.RhythmDBQueryType.EQUALS, RB.RhythmDBPropType.TITLE, 'some song name' )   


		# for row in query_model:
		#     # print(row[0].get_string( RB.RhythmDBPropType.ARTIST ))
		#     print(row[0].get_string( RB.RhythmDBPropType.TITLE ))
		#     print(row[0].get_double( RB.RhythmDBPropType.RATING ) )
		#     print(row[0].get_string( RB.RhythmDBPropType.LOCATION))  #filename
		#     print(row[0].get_ulong( RB.RhythmDBPropType.PLAY_COUNT)) 
		    # print(row[0].NUM_PROPERTIES)
		    # print(row[0].gather_metadata( RB.RhythmDBPropType)) 
		    # print(dir( RB.RhythmDBPropType)) 
		    # print(dir( row[0]))
		    # print(dir( RB.RhythmDBPropType))
		    # print(dir( RB))
				# c = row[0].count
				# print(c)
		    # print (row[0].count)
		    # row[0].keyword_add(RB, 1465180463, "date_rated") 

		    # print (row[0])
		    # print row


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
		# entries = [{"artist":"Johnny Vasquez1", "title":"Azafata"}]
		# date = RB.g_date_time_new_now_local()
		# date1 = date.get_julian()
		print("date", self.get_time())
		# self.update_rbsync_db(entries)
		# self.sync("action", "data")
		# mySync = self.sync
		# print(mySync)
		# self.create_rbsyncdb_tables()
		# ui_manager = shell.get_ui_mfanager()
		# print(menu_item)
		# shell = self.object
		# db = shell.props.db
		# model = RB.RhythmDBQueryModel.new_empty(db)
		# print(model)




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


		# shell = self.object
		# page = shell.props.selected_page
		# query_model = page.get_query_model()

		# uris = [row[0].get_playback_uri() for row in query_model]

		# dialog = Gtk.FileChooserDialog(title="Select Folder",
		# 	parent=shell.props.window,
		# 	action=Gtk.FileChooserAction.SELECT_FOLDER,
		# 	buttons=(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_OK, Gtk.ResponseType.OK))

		# response = dialog.run()
		# if response == Gtk.ResponseType.OK:
		# 	dest_dir = Gio.File.new_for_uri(dialog.get_uri())
		# 	for uri in uris:
		# 		source_file = Gio.File.new_for_uri(uri)
		# 		fname = source_file.get_basename()
		# 		dest_file = dest_dir.get_child(fname)
		# 		source_file.copy(dest_file, Gio.FileCopyFlags.OVERWRITE)
		# dialog.destroy()







# class Blah(GObject.Object, Peas.Activatable):
# 	__gtype_name__ = 'Blah'
# 	object = GObject.property(type=GObject.Object)

# 	def __init__(self):
# 		GObject.Object.__init__(self)

# 	def on_entry_changed(self, _tree, entry):
# 		"""
# 		'entry-added' signal handler
# 		"""
# 		### place the following in an 'init' section so
# 		### it doesn't get repeated on each signal
# 		print("HI")
# 		self.type_song=self.db.entry_type_get_by_name("song")
# 		type=entry.get_entry_type()
# 		if type==self.type_song:
# 			id=self.db.entry_get(entry, RB.RhythmDBPropType.ENTRY_ID)
# 			self.song_entries.append(int(id))
# GObject.type_register(Blah)










