#!/usr/bin/env python
# LoS Map Editor
# Todd Troxell <xtat@rapidpacket.com>

import pygtk
pygtk.require('2.0')
import gtk
from struct import pack, unpack
from copy import copy

class Image(object):
    name = "blank"
    def get_path(self):
        return "%s.jpg"% (self.name)

class Tile(object):
    image = Image()
    special_function = 0
    special_param = ""
    def __str__(self):
        return "%s%s%s%s\n" % (pack("B", len(self.image.name)),
                               self.image.name,
                               pack("B", self.special_function),
                               self.special_param)
    
class Map(object):
    MAPWIDTH = 11
    MAPHEIGHT = 11

    tiles = []
    for x in range(0,11):
        tiles.append(list())
        for y in range(0,11):
            tiles[x].append(Tile())
            
    map_type = 0
    song_name = "default"
    spawn_name = ""
    enter_msg = ""
    
    north_map = "default"
    east_map = "default"
    south_map = "default"
    west_map = "default"

    def __str__(self):
        mapstr = ""
        mapstr += "%s\n" % (pack("B", self.map_type))
        mapstr += "%s\n" % (self.north_map)
        mapstr += "%s\n" % (self.east_map)        
        mapstr += "%s\n" % (self.south_map)        
        mapstr += "%s\n" % (self.west_map)
        mapstr += "%s\n" % (self.song_name)
        mapstr += "%s\n" % (self.spawn_name)
        mapstr += "%s\n" % (self.enter_msg)
        
        for row in self.tiles:
            for tile in row:
                mapstr += str(tile)
        return mapstr

    def write_to_file(self, filepath):
        f = open(filepath, 'w')
        f.write(str(self))
        f.close()

    def read_from_file(self, filepath):
        f = open(filepath, 'r')
        mapstr = f.readlines()
        self.map_type = unpack("B", mapstr[0].strip())[0]
        self.north_map = mapstr[1].strip()
        self.south_map = mapstr[2].strip()
        self.west_map = mapstr[3].strip()
        self.east_map = mapstr[4].strip()
        self.song_name = mapstr[5].strip()
        self.spawn_name = mapstr[6].strip()
        self.enter_msg = mapstr[7].strip()
        idx = 8
        for row in self.tiles:
            for tile in row:
                curstr = mapstr[idx].strip()
                print curstr
                imgnamelen = unpack("B", curstr[0])[0]
                tile.name = curstr[1:imgnamelen+1]
                tile.special_function = unpack("B", curstr[imgnamelen+1])[0]
                print tile.special_function
                tile.special_param = curstr[imgnamelen+2:]
                idx += 1
    
class MapEditor(object):        
    def __init__(self):
        self.curmap = Map()
        self.selected_tile = Tile()
        
        # create the main window, and attach delete_event
        self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        self.window.connect("delete_event", self.close_application)
        self.window.set_border_width(10)
        self.window.show()
        
        vbox = gtk.VBox()
        vbox.show()
        self.window.add(vbox)
        self.__build_menubar(vbox)
        
        # Make 11 Rows of 11 buttons
        buttongrid = []
        hboxes = []
        rowcnt = 0
        for row in self.curmap.tiles:
            # Make a an hbox, and a row of 11 buttons
            buttons = []
            hbox = gtk.HBox()
            hbox.show()
            vbox.add(hbox)
            columncnt = 0
            for tile in row:
                image = gtk.Image()
                image.set_from_file(tile.image.get_path())
                image.show()
                button = gtk.Button()
                button.set_relief(gtk.RELIEF_NONE)
                button.add(image)
                buttons.append(button)
                button.show()
                hbox.pack_start(button)
                button.connect("clicked", self.button_clicked,
                               (rowcnt,columncnt))
                               
                columncnt += 1
            hboxes.append(hbox)
            rowcnt += 1
            buttongrid.append(buttons)
        self.buttongrid = buttongrid
        sep = gtk.VSeparator()
        sep.set_size_request(200, 20)
        vbox.add(sep)
        sep.show()
        
        # make selected display button
        i = gtk.Image()
        i.set_from_file(self.selected_tile.image.get_path())
        i.show()
        b = gtk.Button()
        b.set_relief(gtk.RELIEF_NONE)
        b.add(i)
        self.selectedbutton = b
        vbox.add(b)
        b.show()
        
        self.__build_tileselector(vbox)
        
    def __change_selected(self, widget, data=None):
        for tile in self.tilebox:
            print tile.image.name
        print "change selected to: %s: %s" % (data,
                                              self.tilebox[data].image.name)
        self.selected_tile = self.tilebox[data]
        i = gtk.Image()
        i.set_from_file(self.selected_tile.image.get_path())
        i.show()
        self.selectedbutton.set_image(i)
        self.selectedbutton.show()
        
        
    # when invoked (via signal delete_event), terminates the application.
    def close_application(self, widget, event, data=None):
        gtk.main_quit()
        return False

    # is invoked when the button is clicked.  It just prints a message.
    def button_clicked(self, widget, data=None):
        x = int(data[0])
        y = int(data[1])
        print "painting tile %s, %s to %s" % (x, y,
                                              self.selected_tile.image.name)
        self.curmap.tiles[x][y] = copy(self.selected_tile)
        i = gtk.Image()
        i.set_from_file(self.selected_tile.image.get_path())
        i.show()
        self.buttongrid[x][y].set_image(i)
        self.buttongrid[x][y].show()

    def __get_main_menu(self, window):
        accel_group = gtk.AccelGroup()
        item_factory = gtk.ItemFactory(gtk.MenuBar, "<main>", accel_group)
   
        # This method generates the menu items. Pass to the item factory
        #  the list of menu items
        item_factory.create_items(self.menu_items)
   	
        # Attach the new accelerator group to the window.
        window.add_accel_group(accel_group)
   	
        # need to keep a reference to item_factory to prevent its destruction
        self.item_factory = item_factory
        # Finally, return the actual menu bar created by the item factory.
        return item_factory.get_widget("<main>")

    def __do_save_as(self, widget, data=None):
        fcd = gtk.FileChooserDialog()
        fcd.run()
    def __do_new(self, widget, data=None):
        pass

    def __do_save(self, widget, data=None):
        pass
    
    def __do_open(self, widget, data=None):
        fcd = gtk.FileChooserDialog()
        fcd.run()
    def __do_map_opts(self, widget, data=None):
        pass

    def __do_about(self, widget, data=None):
        pass
    def __do_add_tile(self, widget, data=None):
        pass
    
    def __build_menubar(self, parent_widget):
        self.menu_items = (
            ( "/_File",         None,         None, 0, "<Branch>" ),
            ( "/File/_New",     "<control>N", self.__do_new, 0, None ),
            ( "/File/_Open",    "<control>O", self.__do_open, 0, None ),
            ( "/File/_Save",    "<control>S", self.__do_save, 0, None ),
            ( "/File/Save _As", None,         self.__do_save_as, 0, None ),
            ( "/File/sep1",     None,         None, 0, "<Separator>" ),
            ( "/File/Quit",     "<control>Q", gtk.main_quit, 0, None ),
            ( "/_Map",          None,         None, 0, "<Branch>" ),
            ( "/Map/Options",  None,         self.__do_map_opts, 0, None ),
            ( "/_Tile",         None,         None, 0, "<Branch>"),
            ( "/Tile/_Add",     None,         self.__do_add_tile, 0, None),
            ( "/_Help",         None,         None, 0, "<LastBranch>" ),
            ( "/_Help/About",   None,         self.__do_about, 0, None ),
            )
        self.window.set_title("Map Editor")
        #window.set_size_request(300, 200)
  	
        main_vbox = gtk.VBox(False, 1)
        main_vbox.set_border_width(1)
        parent_widget.add(main_vbox)
        main_vbox.show()
        menubar = self.__get_main_menu(self.window)
        main_vbox.pack_start(menubar, False, True, 0)
        menubar.show()

    def __build_tileselector(self, parent_widget):
        self.tilebox = []
        buttons = []
        images = []
        scrollwindow = gtk.ScrolledWindow()
        parent_widget.add(scrollwindow)
        scrollwindow.show()
        hbox = gtk.HBox()
        scrollwindow.add_with_viewport(hbox)
        hbox.show()
        
        # add some dummy tiles to selector box
        names = ['black', 'blank', 'greenz', 'stone', 'water', 'wood']
        
        for count in range (0,len(names)):
            newtile = Tile()
            newtile.image.name = names[count]
            image = gtk.Image()
            image.set_from_file(newtile.image.get_path())
            image.show()
            button = gtk.Button()
            button.connect("clicked", self.__change_selected, count)
            hbox.add(button)
            button.add(image)
            button.show()
            self.tilebox.append(newtile)
            buttons.append(button)
            images.append(image)
            print newtile.image.name
            
        for tile in self.tilebox:
            print tile.image.name
        
def main():
    gtk.main()
    return 0

if __name__ == "__main__":
    MapEditor()
    main()
