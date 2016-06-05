# Rhythmbox-Sync Plugin
Rhythmbox plugin for syncing Music settings accross devices, using cloud server that you need to setup. Focusing on maintaining track ratings and play counts across devices. Would also like to support any other music metadata editing, so that you can update track info and have it get synced. Hope to include support for some android players.

Note, that some of the functionality will likely be provided by sepearate packages. This application is focusing on the functionality that is part of rhythmbox
  -When updating a track rating, needs to add the date the rating was updated to normal rhythmdb.xml database. The date the rating for a track is set is not normally stored in the vanilla rhythmbox.
  -When a song is last played, there is already a value that is stored in the rhythmdb.xml database, "last-seen", which indicates that last time the song was played to the end. The play count is updated at that time. So this plugin doesn't change that. However, when syncing, the playcount will be updated to include recent plays on other devices, and the last-seen value will be updated to be the date the file was last played on any device, not just the local device.
  -There needs to be a sync function. Eventually, I would like to add an optional autosync function that updates after any song is played (to update play count), or to update a rating change. For now, the sync will be pushed manually, which will then update any ratings or playcounts or whatever that have occurred since last sync.

Stuff that needs to happen outside of this rhythmbox plugin:
  -There needs to be some sort of cloud server that is used to store data that can be accessed by multiple devices. Currently I plan on implementing this in Node/javascript with a simple database, possibly mongodb or sqlite. I do not plan to use the existing xml database from rhytmbox for the cloud application.
  -Android app, which wouldn't be the music player necessarily, but an app that reads and writes to various musicplayer databases on the device using data from the cloud app. This way a user can rate tracks on their android device and this information would get synced to rhythmbox. For example, I currently have been using rocket player, and so I plan to focus on interfacing with its database. This seems like it would require a rooted android device, unless you are just interfacing with the android's main music database, or if the music player stores its data on the sdcard (or anywhere where its access is not restricted to the app itself).

Installation Instructions
* [Homepage](https://github.com/semlak/rhythmbox-sync)
