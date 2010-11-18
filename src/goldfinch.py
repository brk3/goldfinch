#!/usr/bin/env python

# Copyright (C) 2010 Paul Bourke <pauldbourke@gmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

# $Id$
# ex: expandtab tabstop=2 shiftwidth=2:

try:
  import curses
  import curses.wrapper
  import goldfinchlib.config
  import goldfinchlib.controllers.twitter
  from goldfinchlib.customtextbox import CustomTextbox
  from goldfinchlib.customtextbox import InputHandler 
  from goldfinchlib.statusbar import StatusBar
  from goldfinchlib.pager import Pager
except ImportError as e:
  print(e)
  exit(1)

import os
import logging
import logging.handlers
import Queue
import threading
import cPickle

class MainWindow(object):
  '''Represents the interface on the screen (view)'''
  
  def __init__(self, stdscr, config=None):
    '''Sets up a MainWindow.

    stdscr  -- a curses WindowObject to draw to
    config  -- a ConfigParser.Config object (see docs for possible values)

    '''
    self.logger = logging.getLogger('goldfinch' +
        "." + self.__class__.__name__)
    self.stdscr = stdscr
    self.config = config
    self.mode = 'edit'
    (self.term_height, self.term_width) = self.stdscr.getmaxyx()
    self.statusbar_top = StatusBar(0, self.stdscr)
    self.statusbar_bottom = StatusBar(self.term_height-2, self.stdscr)
    self.pager = Pager(200, self.stdscr, logging.getLogger(\
        'goldfinch' + '.' + Pager.__class__.__name__)) 

  def draw(self):
    '''Draw the various interface components to the screen'''
    self._draw_statusbars()
    self._draw_pager()
    self._draw_inputbox()
    self.stdscr.move(self.term_height-1,\
        0)  # move the cursor to the input box

  def set_mode(self, mode):
    assert mode == 'edit' or mode == 'command'
    self.input_box.mode = mode
    self.statusbar_bottom.add_text('['+mode+']', 'right')
    if mode == 'command':
      curses.curs_set(0) # hide
    else:
      curses.curs_set(1)
    self.logger.debug('set mode to ' + mode)

  def _draw_inputbox(self):
    '''Draws the input box to the main window using a goldfinch.CustomTextbox.
    The input marker is drawn outside the input box.

    '''
    self.input_win = curses.newwin(1, self.term_width, self.term_height-1, 0)
    # create a list of InputHandler objects to handle key press events on the
    # input box
    handlers = []

    #TODO: resize event doesn't seem to get recognised when on a remote
    #      terminal.
    resize_handler = InputHandler(\
        curses.KEY_RESIZE,
        self.draw,
        [],
        ['edit', 'command'])
    handlers.append(resize_handler)

    command_mode = InputHandler(\
        curses.ascii.ESC,
        self.set_mode,
        ['command'],
        ['edit'])
    handlers.append(command_mode)

    edit_mode = InputHandler(\
        ord('i'),
        self.set_mode,
        ['edit'],
        ['command'])
    handlers.append(edit_mode)

    scroll_up = InputHandler(\
        ord('k'),
        self.pager.scroll,
        [-1],
        ['command'])
    handlers.append(scroll_up)

    scroll_down = InputHandler(\
        ord('j'),
        self.pager.scroll,
        [1],
        ['command'])
    handlers.append(scroll_down)

    page_down = InputHandler(\
        curses.KEY_PPAGE,
        self.pager.scroll,
        [-self.term_height-3],  # -3 for 2 status bars + inputbox
        ['edit', 'command'])
    handlers.append(page_down)

    page_up = InputHandler(\
        curses.KEY_NPAGE,
        self.pager.scroll,
        [self.term_height-3], 
        ['edit', 'command'])
    handlers.append(page_up)

    space_page_down = InputHandler(\
        curses.ascii.SP,
        self.pager.scroll,
        [self.term_height-3],
        ['command'])
    handlers.append(space_page_down)

    self.input_box = CustomTextbox(self.input_win,\
         handlers)
    self.input_win.overwrite(self.stdscr)
    self.input_win.refresh()
    self.stdscr.refresh()
  
  def _draw_pager(self):
    '''Draws the main pager area to the screen'''
    self.pager.draw()

  def _draw_statusbars(self):
    self.statusbar_top.draw()
    self.statusbar_bottom.draw()
    self.statusbar_top.add_text('goldfinch ' + GoldFinch.__version__, 'left')
    self.statusbar_bottom.add_text(''.join(['[', self.mode, ']']), 'right')

class GoldFinch(object):
  '''curses based twitter client, written in python (controller)'''

  __version__ = 'svn' + filter(str.isdigit, '$Revision$')
  __author__ = 'Paul Bourke <pauldbourke@gmail.com>'


  config_dir = os.path.join(os.environ['HOME'], '.goldfinch')
  config_file = os.path.join(config_dir, 'goldfinchrc')
  log_file = os.path.join(config_dir, 'logs', 'goldfinch.log')

  def __init__(self, stdscr=None):
    self.init_logger()
    self.logger.info('Starting goldfinch')
    self.config = self.init_config()
    self.controller = self.init_twitter_api()
    self.stdscr = stdscr
    if stdscr is not None:
      self.main_window = self.init_main_window()
      self.main_window.statusbar_bottom.add_text('Getting timeline..', 'left')
      self.init_refresh_thread()
      self.main_window.statusbar_bottom.add_text('Done.', 'left')
      while True:
        self.parse_input()

  def parse_input(self):
    input_str = self.main_window.input_box.edit().strip()
    input_valid = True
    command = input_str.split()[0].strip()
    arg_line = input_str[len(command):].strip()

    self.logger.debug('Got input: ' + input_str)

    if len(command) > 1:
      if command == ':quit' or command == ':q':
        self.cleanup()
      elif command == ':clear' or command == ':c':
        #TODO: add ctrl-L for this
        self.main_window.clear_pager()
      elif command == ':post' or command == ':p':
        if len(arg_line) <= self.controller.max_msg_length:
          self.main_window.statusbar_bottom.add_text('Posting message..', 'left')
          self.logger.info('posting msg (' + str(len(arg_line)) + ')')
          self.controller.api.update_status(arg_line)
          self.main_window.statusbar_bottom.add_text('Done!', 'left')
        else:
          warn_msg = 'msg length too long, must be < '+\
              str(self.controller.max_msg_length)
          self.main_window.statusbar_bottom.add_text(warn_msg, 'left')
          self.logger.info(warn_msg)
          pass
      elif command == ':list' or command == ':l':
        # must be one arg to this command
        if arg_line == 'friends':
          ret = self.controller.get_friends()
          self.main_window.pager.erase()
          self.main_window.pager.add_text(ret)
          #TODO: ensure these threads are not already running
          #ret_queue = Queue.Queue()
          #consumer_thread = threading.Thread(target=self.main_window.pager.\
          #    add_text, args=(ret_queue,))
          #self.logger.debug('starting consumer thread')
          #consumer_thread.start()
          #producer_thread = threading.Thread(target=self.controller.get_friends)
          #self.logger.debug('starting producer thread')
          #producer_thread.start()
      elif command == ':refresh' or command == ':r':
        #TODO: add these lines to a function
        self.main_window.statusbar_bottom.add_text('Refreshing timeline..', 'left')
        self.main_window.pager_pad.erase()
        self.main_window.pager_ypos = 0
        for screen_name, status in self.controller.get_home_timeline(30):
          self.main_window.pager.add_text(self.format_status_line(\
              screen_name, status))
        self.main_window.statusbar_bottom.add_text('Done.', 'left')
      else:
        input_valid = False

    if input_valid:
      self.main_window.statusbar_bottom.add_text('', 'left')
      self.main_window.input_box.clear()
    else:
      self.main_window.statusbar_bottom.add_text('Unknown command.  Try :help', 'left')
      self.main_window.input_box.clear()

  def init_logger(self, log_file=None):
    '''Sets up a logging object which can be accessed from other classes.
    
    log_file -- path/file to put log in.  Defaults to 
                ~/.goldfinch/logs/goldfinch.log

    '''
    if not log_file:
      log_file = self.log_file
    if not os.path.isdir(os.path.dirname(log_file)):
      os.makedirs(os.path.dirname(log_file))
    if not os.path.exists(log_file):
      try:
        open(log_file, 'w').close()
      except IOError as e:
        self.cleanup(e) 
    self.logger = logging.getLogger('goldfinch')
    self.logger.setLevel(logging.DEBUG)
    handler = logging.handlers.RotatingFileHandler(
        log_file, maxBytes=1024*100, backupCount=3)
    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s -\
        %(message)s')
    handler.setFormatter(formatter)
    self.logger.addHandler(handler)

  def init_twitter_api(self):
    api = goldfinchlib.controllers.twitter.TwitterController(GoldFinch.config_dir)
    if hasattr(self, 'main_window'):
      self.main_window.statusbar_bottom.add_text('Authenticating..', 'left')
    self.logger.info('Authenticating twitter api')
    try:
      api.perform_auth(os.path.join(self.config_dir, 'access_token'))
    except IOError as e:
      self.logger.error(e)
      if hasattr(self, 'main_window'):
        self.main_window.statusbar_bottom.add_text('Authentication error, see log for\
            info', 'left')
    if hasattr(self, 'main_window'):
      self.main_window.statusbar_bottom.add_text('Ready', 'left')
    self.logger.info('Done')
    return api
    
  def init_config(self):
    self.logger.info('Initialising config file')
    config = goldfinchlib.config.Config()
    ret = ()
    try:
      ret = config.load_config(GoldFinch.config_file)
    except ConfigParser.ParsingError as e:
      self.cleanup('Error reading config file.\nSee log file for details')
    if not ret:
      output = ''.join([self.config_file, ' is empty or non existent.  ',
              'See README for examples on how to create one.'])
      self.cleanup(output)
    mandatory_values = {
        #TODO: finalise these values
        'account':('accountname', 'oauthpin'),
        'preferences':['refresh']
    }
    (config_ok, reason) = config.ensure_config(mandatory_values)
    if not config_ok:
      self.cleanup(reason + ' is missing from config file.')
    config = config.get_config()
    self.logger.info('Done')
    return config

  def init_main_window(self):
    self.logger.info('Initialising main window')
    main_window = MainWindow(self.stdscr, self.config)
    main_window.draw()
    self.logger.info('Done')
    return main_window

  def init_refresh_thread(self):
    # TODO: may need to add synchcronisation to pager view
    # TODO: (related to above) only update screen if pager contents have changed
    self.main_window.pager.erase()
    self.main_window.pager_ypos = 0
    for screen_name, status in self.controller.get_home_timeline(30):
      self.main_window.pager.add_text(self.format_status_line(screen_name, status))
    interval = int(self.config.get('preferences', 'refresh'))
    threading.Timer(interval, self.init_refresh_thread).start()

  def format_status_line(self, screen_name, message):
    '''Formats a status line for the pager, so everything aligns nicely.  A status line
    consists of screen_name and the message posted by that screen_name.

    screen_name -- user name or screen name of the tweeter
    message -- message content
    '''
    screen_name_padding = 20
    the_content = []
    max_chunk_size = self.main_window.term_width - screen_name_padding

    # add the first chunk of content, right justified
    the_content.append(''.join([screen_name.ljust(screen_name_padding-1), 
        message[0:max_chunk_size]]))

    # if there are more chunks, break onto subsequent lines
    # chunk_size*2 to start at the second chunk in line
    if max_chunk_size < len(message):
      for i in range(max_chunk_size*2, len(message)+max_chunk_size, max_chunk_size):
        this_chunk_size = len(message[i-max_chunk_size:i])
        the_content.append(message[i-max_chunk_size:i]\
            .rjust(screen_name_padding+this_chunk_size-1))

    # add a new line 
    the_content.append('')

    return the_content

  def cleanup(self, error_msg=None):
    '''Clean up, write out an optional error message and exit.  (No error
    message implies a normal exit.
    
    '''
    ret = 0
    if hasattr(self, 'stdscr'):
      curses.endwin() 
    if error_msg:
      ret = 1
      print(error_msg)
    self.logger.info('exiting..')
    exit(ret)

def main():
  # this env variable reduces the delay from the ESC key
  # (see http://en.chys.info/2009/09/esdelay-ncurses/)
  if not 'ESCDELAY' in os.environ:
    os.environ['ESCDELAY'] = '25'
  curses.wrapper(GoldFinch)

if __name__ == '__main__':
  main()
