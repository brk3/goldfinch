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
  import goldfinch.config
  import goldfinch.controllers.twitter
  from goldfinch.customtextbox import CustomTextbox
  from goldfinch.customtextbox import InputHandler 
except ImportError as e:
  print(e)
  exit(1)

import os
import logging
import logging.handlers
import Queue
import threading
import cPickle

class MainWindow:
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
    self.pager_ypos = 0

  def draw(self):
    '''Draw the various interface components to the screen'''
    (self.term_height, self.term_width) = self.stdscr.getmaxyx()
    self._draw_statusbar('top', 'goldfinch ' + GoldFinch.__version__)
    self._draw_statusbar('bottom')
    self._draw_pager()
    self._draw_inputbox()
    self.stdscr.move(self.term_height-1,\
        0)  # move the cursor to the input box

  def set_mode(self, mode):
    assert mode == 'edit' or mode == 'command'
    self.input_box.mode = mode
    self.show_notification('['+mode+']', 'right')
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
        self.scroll_pager,
        [-1],
        ['command'])
    handlers.append(scroll_up)

    scroll_down = InputHandler(\
        ord('j'),
        self.scroll_pager,
        [1],
        ['command'])
    handlers.append(scroll_down)

    page_down = InputHandler(\
        curses.KEY_PPAGE,
        self.scroll_pager,
        [-self.term_height-3],  # -3 for 2 status bars + inputbox
        ['edit', 'command'])
    handlers.append(page_down)

    page_up = InputHandler(\
        curses.KEY_NPAGE,
        self.scroll_pager,
        [self.term_height-3], 
        ['edit', 'command'])
    handlers.append(page_up)

    space_page_down = InputHandler(\
        curses.ascii.SP,
        self.scroll_pager,
        [self.term_height-3],
        ['command'])
    handlers.append(space_page_down)

    self.input_box = CustomTextbox(self.input_win,\
         handlers)
    self.input_win.overwrite(self.stdscr)
    self.input_win.refresh()
    self.stdscr.refresh()
  
  def _draw_pager(self):
    '''Draws the main 'pager' area to the screen.  Set preferences:scrollback
    in the config to adjust the scrollback buffer.
    
    '''
    #TODO: number of tweets should be < than this value to avoid drawing errors
    if self.config:
      scrollback = int(self.config.get('preferences', 'Scrollback'))
    else:
      scrollback = 200  # default
    self.pager_pad = curses.newpad(scrollback, self.term_width)
    self.scroll_pos = 0
    self.pager_pad.refresh(self.scroll_pos, 0, 1, 0, self.term_height-3, self.term_width)
    self.pager_pad.scrollok(True)
    self.pager_pad.idlok(True)
    self.stdscr.refresh()

  def _draw_statusbar(self, pos, msg=None, align='left'):
    '''Draws a status bar to the screen.

    pos -- The portion of the screen to place it.
           Can be either 'top' or 'bottom'
    msg -- Optional text to place on the status bar.

    '''
    assert pos == 'top' or pos == 'bottom'

    # TODO: add way to align text left or right
    if pos.lower() == 'top':
      ypos = 0
    elif pos.lower() == 'bottom':
      ypos = self.term_height-2
    if msg:
      self.stdscr.addch(ypos, 0, ' ', curses.A_REVERSE)
      self.stdscr.addstr(ypos, 1, msg, curses.A_REVERSE)
    left_dim = 0
    if msg:
      left_dim = len(msg)+1
    for i in range(left_dim, self.term_width):
      try:
        self.stdscr.addch(ypos, i, ' ', curses.A_REVERSE)
      except curses.error as e:
        self.logger.error(e)
    self.stdscr.refresh()

  def show_notification(self, msg, align='left'):
    '''Shows a notification in the bottom status bar.

    msg -- text to display
    '''
    self._draw_statusbar('bottom', msg, align)
    self.stdscr.refresh()

  def add_text_to_pager(self, content_queue):
    '''Draws text to the pager display.

    content_queue -- text to display which should either be a list, string,
                     or a Queue.Queue containing one of these.
    '''
    if isinstance(content_queue, Queue.Queue):
      content = content_queue.get()
    else:
      content = content_queue
    if type(content) is not list:
      content = [content]
    for line in content:
      try:
        self.pager_pad.addstr(self.pager_ypos, 0, str(line))
        self.pager_ypos = self.pager_ypos + 1
      except curses.error as e:
        self.logger.error(e)
        self.logger.error(line)
      except UnicodeEncodeError as e:
        #TODO: fix unicode support (see note at top of curses howto)
        self.logger.error(e)
        self.logger.error(line)
        break
    self.stdscr.move(self.term_height-1,\
        0) # after addstr the cursor will be at end of str so move back to input box
    self.pager_pad.refresh(0, 0, 1, 0, self.term_height-3,\
        self.term_width)
    self.stdscr.refresh()

  def scroll_pager(self, lines):
    '''Scroll the pager.  Should be able to use window.scroll for this
    but couldn't get to work for some reason.
    
    lines -- number of lines to scroll. (negative to scroll up)
    clear_before -- whether to clear the pager before updating (useful for
                    page down/up events.
    
    '''
    try:
      self.pager_pad.refresh(self.scroll_pos+lines, 0, 1,\
          0, self.term_height-3, self.term_width)
      if (lines < 0) and (abs(lines) - self.scroll_pos > 0):
        self.scroll_pos = 0
      else:
        self.scroll_pos = self.scroll_pos + lines
    except curses.error as e:
      self.logger.error(e)

  def add_status_to_pager(self, screen_name, message):
    '''Wrapper for add_text_to_pager to draw a status/tweet in a formatted
    way.

    screen_name -- user name or screen name of the tweeter
    message -- message content
    '''
    screen_name_padding = 20
    the_content = []
    max_chunk_size = self.term_width - screen_name_padding

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

    # draw the content
    self.add_text_to_pager(the_content)
 
  def clear_pager(self):
    '''Clears the pager contents'''
    self._draw_pager()

class GoldFinch:
  '''curses based twitter client, written in python (controller)'''

  __version__ = 'svn' + filter(str.isdigit, '$Revision$')
  __author__ = 'Paul Bourke <pauldbourke@gmail.com>'


  config_dir = os.path.join(os.environ['HOME'], '.goldfinch')
  config_file = os.path.join(config_dir, 'goldfinchrc')

  def __init__(self, stdscr):
    self.init_logger()
    self.stdscr = stdscr
    self.logger.info('Starting goldfinch')
    self.config = self.init_config()
    self.main_window = self.init_main_window()
    self.controller = self.init_twitter_api()
    self.main_window.show_notification('Getting timeline..')
    self.init_refresh_thread()
    self.main_window.show_notification('Done.')
    
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
          self.main_window.show_notification('Posting message..')
          self.logger.info('posting msg (' + str(len(arg_line)) + ')')
          self.controller.api.update_status(arg_line)
          self.main_window.show_notification('Done!')
        else:
          warn_msg = 'msg length too long, must be < '+\
              str(self.controller.max_msg_length)
          self.main_window.show_notification(warn_msg)
          self.logger.info(warn_msg)
          pass
      elif command == ':list' or command == ':l':
        # must be one arg to this command
        if arg_line == 'friends':
          ret_queue = Queue.Queue()
          #TODO: ensure these threads are not already running
          consumer_thread = threading.Thread(target=self.main_window.\
              add_text_to_pager, args=(ret_queue,))
          self.logger.debug('starting consumer thread')
          consumer_thread.start()
          producer_thread = threading.Thread(target=self.controller.get_friends,\
              args=(ret_queue,))
          self.logger.debug('starting producer thread')
          producer_thread.start()
      elif command == ':refresh' or command == ':r':
        #TODO: add these lines to a function
        self.main_window.show_notification('Refreshing timeline..') 
        self.main_window.pager_pad.erase()
        self.main_window.pager_ypos = 0
        for screen_name, status in self.controller.get_home_timeline(30):
          self.main_window.add_status_to_pager(screen_name, status)
        self.main_window.show_notification('Done.') 
      else:
        input_valid = False

    if input_valid:
      self.main_window.show_notification('')
      self.main_window.input_box.clear()
    else:
      self.main_window.show_notification('Unknown command.  Try :help')
      self.main_window.input_box.clear()

  def init_logger(self):
    ''' Sets up a logging object which can be accessed from other classes '''
    self.logger = logging.getLogger('goldfinch')
    self.logger.setLevel(logging.DEBUG)
    handler = logging.handlers.RotatingFileHandler(
        'goldfinch.log', maxBytes=1024*100, backupCount=3)
    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s -\
        %(message)s')
    handler.setFormatter(formatter)
    self.logger.addHandler(handler)

  def init_twitter_api(self):
    api = goldfinch.controllers.twitter.TwitterController(GoldFinch.config_dir)
    self.main_window.show_notification('Authenticating..')
    self.logger.info('Authenticating twitter api')
    try:
      api.perform_auth(os.path.join(os.environ['HOME'], 
        '.goldfinch', 'access_token'))
    except IOError as e:
      self.logger.error(e)
      self.main_window.show_notification('Authentication error, see log for\
          info')
    self.main_window.show_notification('Ready')
    self.logger.info('Done')
    return api
    
  def init_config(self):
    self.logger.info('Initialising config file')
    config = goldfinch.config.Config()
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
    self.main_window.pager_pad.erase()
    self.main_window.pager_ypos = 0
    for screen_name, status in self.controller.get_home_timeline(30):
      self.main_window.add_status_to_pager(screen_name, status)
    interval = int(self.config.get('preferences', 'refresh'))
    threading.Timer(interval, self.init_refresh_thread).start()

  def cleanup(self, error_msg=None):
    '''Clean up, write out an optional error message and exit.  (No error
    message implies a normal exit.
    
    '''
    ret = 0
    curses.endwin() 
    if error_msg:
      ret = 1
      self.logger.error(error_msg)
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