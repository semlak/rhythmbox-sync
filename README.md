# Rhythmbox-Sync Plugin

#USE at your own risk.

Rhythmbox plugin for syncing Music settings accross devices, using cloud server that you need to setup. Focusing on maintaining track ratings and play counts across devices. Would also like to support any other music library and metadata changes, so that you can update track info and have it get synced. Hope to include support for some android players.

You would use this in conjuction with https://github.com/semlak/rbsync-cloud, which is also incomplete.

NOTE: THIS PLUGIN CURRENTLY IS INCOMPLETE!!!. It currently lacks even the basic desired functionality. Right now, I'm still trying to get the basic funcationality working, so this plugin is basically useless.

That being said, it does not currently write to your rhythmbox databases. As long as you don't have an existing file in your '.local/share/rhythmbox/' called rbsync.db (an SQLITE db), there will be no overwrites to any of your data, and so you should be free to use if you would like to use any of the code. 


Note, that some of the functionality will likely be provided by sepearate packages. This application is focusing on the functionality that is part of rhythmbox
  -When updating a track rating, the date the rating was updated is not normally stored by normal rhythmbox. Same for many other properties. Play count appears to be an exception, as the play-count can be assumed to be updated at the time of 'last-played'. Anyway, because of the need to store additional information (dates when updates are made), I am storing most of the extra info the plugin needs in a separate database, an sqlite database named rbsyncdb.db in ~/.local/share/rhythmbox. However, when you sync your data across the devices, actual changes to the library data are then made to your rhythmdb.xml file. If you decide to disable the plugin and remove the rbsyncdb.db file, there won't be additional changes you would need to worry about undoing.
  -When a song is last played, there is already a value that is stored in the rhythmdb.xml database, "last-seen", which indicates that last time the song was played to the end. The play count is updated at that time. So this plugin doesn't change that. However, when syncing, the playcount will be updated to include recent plays on other devices, and the last-seen value will be updated to be the date the file was last played on any device, not just the local device.
  -There is a sync function as part of the plugin, currently added to the tools menu. Eventually, I would like to add an optional autosync function that updates after any song is played (to update play count), or to update a rating change. For now, the sync will be pushed manually, which will then update any ratings or playcounts or whatever that have occurred since last sync.

Stuff that needs to happen outside of this rhythmbox plugin (or atleast would be nice):
  -One way of syncing across devices would be to have some sort of cloud server that is used to store data that can be accessed by multiple devices. Currently I plan on implementing this in Node/javascript with a simple database, possibly mongodb or sqlite. I do not plan to use the existing xml database from rhytmbox for the cloud application. 
      -A simpler way might be to just store the rbsyncdb.db file on a cloud server or wherever other devices can get access (could be securely coppied, rsynced, emailed, whatever), and then used to sync the local rbsyncdb.db of the other device, and then sync to the rhythmdb.xml file.
  -Android app, which wouldn't be the music player necessarily, but an app that reads and writes to various musicplayer databases on the device using data from the cloud app. This way a user can rate tracks on their android device and this information would get synced to rhythmbox. For example, I currently have been using rocket player, and so I plan to focus on interfacing with its database. This seems like it would require a rooted android device, unless you are just interfacing with the android's main music database, or if the music player stores its data on the sdcard (or anywhere where its access is not restricted to the app itself).

  It would be nice to have at least a simple option to make this plugin as easy to setup as possible, where the user just needs to install the plugin on each machine running rhythmbox. However, this would seem to not allow a simple way to automate the syncing across devices, which is why I'm suggesting the cloud component. I'm hoping to make it simple by only requiring that the user has cloud storgage location that they enter as part of the configuration, with the option of using a full blown cloud app that handles the database syncing. Just storing the data on the cloud would mean uploading and downloading a full database file every sync. 

Other notes:
     If you edit id3tags of tracks in your music library using an outside tool, such as easytag, this shouldn't cause problems. When rhythmbox rescans the library and notices the external changes, RhythmboxSync should still be notified of the change and should sync across the devices as long as the metadata is supported in RhythmboxSync. I currently don't support syncing of all track properties. 
     However, if you manually edit rhythmdb.xml, or if you use another program that edits it outside of rhythmbox, that might cause problems. I'm planning on adding functionality that checks the integrity of the rhythmdb database versus the rbsync database fixes rbsync accordingly, but I currently don't do that.

Track properties that I attempt to support:
     Incomplete, but includes rating and playcount.

IDENTIFYING IDENTICAL TRACKS ACROSS DEVICES:
Identifying identical songs on different devices could be tricky because their full pathnames might not
match. Their base filenames might not even match, as different devices may have different filesystems, or copying the songs
may have introduced changes in filename.
Rhythmbox appears to use the tracks absolute path as the unique identify for the DB. Which has some complications even on single system
     If a filename changes, RB marks the entry as hidden. When rescanning library, it considers the new filename a new entry
          it doesn't seem to keep the associated data
     If there is a symbolic link to a file, RB would consider the link and the actual file separate entries.
     This allows different songs to have the same base name but different paths (example: same song with different artists).
          This is good, but suggests that we can't rely on just looking at the base file name to determine if songs are identical

     RBSync tries to identify matching files between devices first by comparing paths. Thus, if you are able to use identical path structures
          across devices, that will help with matching.
          I would like to setup a feature where RBSync handles the copying of part or all of a music collection between devices
               but right now, it only syncs metadata, not the actual music/tracks. But such a feature would help with identify identical tracks
          In the likely scenario that RBSync is unable to match based on full path,
               Would like to have matching method user customizable with possible feedback 
               Try matching base filenames, artist, title.
               Try matching base filenames, filesize, bitrate, other properties.
                    None of these allow to identify identical tracks that are transcoded into different formats
                    could try matching title, artist, with possibly base filename without extension.


Installation Instructions
* [Homepage](https://github.com/semlak/rhythmbox-sync)
