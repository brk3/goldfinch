# $Id$
# ex: expandtab tabstop=2 shiftwidth=2:

try:
  import curses
  import curses.wrapper
  import goldfinch.customtextbox
  import goldfinch.config
  import goldfinch.controllers.twitter
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

  def draw(self):
    '''Draw the various interface components to the screen'''
    (self.term_height, self.term_width) = self.stdscr.getmaxyx()
    self._draw_statusbar('top', 'goldfinch ' + GoldFinch.__version__)
    self._draw_statusbar('bottom')
    self._draw_inputbox()
    self._draw_pager()
    self.stdscr.move(self.term_height-1,\
        2)  # move the cursor to the input box

  def _draw_inputbox(self):
    '''Draws the input box to the main window using a goldfinch.CustomTextbox.
    The input marker is drawn outside the input box.

    '''
    self.stdscr.addch(self.term_height-1, 0, '>') 
    self.input_win = curses.newwin(1, self.term_width, self.term_height-1, 2)
    self.input_box = goldfinch.customtextbox.CustomTextbox(self.input_win, 
        lambda: self.draw())
    self.input_win.overwrite(self.stdscr)
    self.input_win.refresh()
    self.stdscr.refresh()
  
  def _draw_pager(self):
    '''Draws the main 'pager' area to the screen.  Set preferences:scrollback
    in the config to adjust the scrollback buffer.
    
    '''
    if self.config:
      scrollback = int(self.config.get('preferences', 'Scrollback'))
    else:
      scrollback = 100  # default
    self.pager_pad = curses.newpad(scrollback, self.term_width)
    self.pager_pad.refresh(0, 0, 1, 0, self.term_height-3, self.term_width)
    self.stdscr.refresh()

  def _draw_statusbar(self, pos, msg=None):
    '''Draws a status bar to the screen.

    pos -- The portion of the screen to place it.
           Can be either 'top' or 'bottom'
    msg -- Optional text to place on the status bar.

    '''
    # TODO: add way to align text left or right
    assert pos == 'top' or pos == 'bottom', 'status bar pos must be either\
        \'top\' or \'bottom\'. You gave: ' + pos
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
      except curses.error:
        pass
    self.stdscr.refresh()

  def show_notification(self, msg):
    '''Shows a notification in the bottom status bar.

    msg -- text to display
    '''
    self._draw_statusbar('bottom', msg)
    self.stdscr.refresh()

  def add_text_to_pager(self, content_queue):
    '''Draws text to the pager display.

    content_queue -- text to display which should either be a list, string,
                     or a Queue.Queue containing one of these.
    '''
    #TODO: add wrapping depending on screen width, and look into pages
    if type(content_queue) is Queue.Queue:
      content = content_queue.get()
    else:
      content = content_queue
    if type(content) is list:
      for line in content:
        try:
          self.pager_pad.addstr(str(line)+'\n')
        except curses.error:
          pass
    elif type(content) is str:
      try:
        self.pager_pad.addstr(content)
      except curses.error:
        pass
    self.stdscr.move(self.term_height-1,\
        2)  # move the cursor to the input box
    self.pager_pad.refresh(0, 0, 1, 0, self.term_height-3,\
        self.term_width)
    self.input_win.refresh()
    self.stdscr.refresh()
 
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
    self.main_window.add_text_to_pager(self.controller.get_home_timeline())
    self.main_window.show_notification('Done.')
    while True:
      self.parse_input()

  def parse_input(self):
    input_valid = True
    input_str = self.main_window.input_box.edit().strip()
    self.logger.debug('Got input: ' + input_str)
    command = input_str.split()[0].strip()
    arg_line = input_str[len(command):].strip()

    if len(command) > 1:
      if command == '/quit' or command == '/q':
        self.cleanup()
      elif command == '/clear' or command == '/c':
        #TODO: add ctrl-L for this
        self.main_window.clear_pager()
      elif command == '/post' or command == '/p':
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
      elif command == '/list' or command == '/l':
        # must be one arg to this command
        if arg_line == 'friends':
          ret_queue = Queue.Queue()
          #TODO: ensure these threads are not already running
          consumer_thread = threading.Thread(target=self.add_text_to_pager,\
              args=(ret_queue,))
          self.logger.debug('starting consumer thread')
          consumer_thread.start()
          producer_thread = threading.Thread(target=self.controller.get_friends,\
              args=(ret_queue,))
          self.logger.debug('starting producer thread')
          producer_thread.start()
      elif command == '/refresh' or command == '/r':
        self.main_window.show_notification('Refreshing timeline..') 
        self.main_window.add_text_to_pager(self.controller.get_home_timeline())
        self.main_window.show_notification('Done.') 
      else:
        input_valid = False

    if input_valid:
      self.main_window.show_notification('')
      self.main_window.input_box.clear()
    else:
      self.main_window.show_notification('Unknown command.  Try /help')
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
      output = ''.join([config_file, ' is empty or non existent.  ',
              'See README for examples on how to create one.'])
      self.cleanup(output)
    mandatory_values = {
        #TODO: finalise these values
        'account':('accountname', 'oauthpin'),
        'preferences':['timeout']
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
  curses.wrapper(GoldFinch)

if __name__ == '__main__':
  main()
