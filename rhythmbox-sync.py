from gi.repository import Gio, GLib, Gtk, GObject, Peas

class ExportPlaylist(GObject.Object, Peas.Activatable):
	__gtype_name__ = 'ExportPlaylist'
	object = GObject.property(type=GObject.Object)

	def __init__(self):
		GObject.Object.__init__(self)

	def do_activate(self):
		action = Gio.SimpleAction(name='export-playlist')
		action.connect('activate', self.export)

		app = Gio.Application.get_default()
		app.add_action(action)

		menu_item = Gio.MenuItem()
		menu_item.set_label("Export Files To...")
		menu_item.set_detailed_action('app.export-playlist')

		app.add_plugin_menu_item('playlist-menu', 'export-menu-item', menu_item)

	def do_deactivate(self):
		app = Gio.Application.get_default()
		app.remove_action('export-playlist')
		app.remove_plugin_menu_item('playlist-menu', 'export-menu-item')

	def export(self, action, data):
		shell = self.object
		page = shell.props.selected_page
		query_model = page.get_query_model()

		uris = [row[0].get_playback_uri() for row in query_model]

		dialog = Gtk.FileChooserDialog(title="Select Folder",
			parent=shell.props.window,
			action=Gtk.FileChooserAction.SELECT_FOLDER,
			buttons=(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_OK, Gtk.ResponseType.OK))

		response = dialog.run()
		if response == Gtk.ResponseType.OK:
			dest_dir = Gio.File.new_for_uri(dialog.get_uri())
			for uri in uris:
				source_file = Gio.File.new_for_uri(uri)
				fname = source_file.get_basename()
				dest_file = dest_dir.get_child(fname)
				source_file.copy(dest_file, Gio.FileCopyFlags.OVERWRITE)
		dialog.destroy()



		
