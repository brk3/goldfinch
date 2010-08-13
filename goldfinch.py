# $Id$

try:
  import curses
  import curses.wrapper
  import CustomTextbox
  import tweepy
except ImportError as e:
  print(e)
  exit(1)

import os
import logging
import logging.handlers
import ConfigParser

class MainWindow:
  '''Represents the interface on the screen (view)'''

  def __init__(self, stdscr, config=None):
    self.logger = logging.getLogger('goldfinch' +
        "." + self.__class__.__name__)
    self.stdscr = stdscr
    self.config = config

  def draw(self):
    '''Draws the interface components to the screen'''
    (self.term_height, self.term_width) = self.stdscr.getmaxyx()
    self._draw_statusbar('top', 'goldfinch ' + GoldFinch.__version__)
    self._draw_statusbar('bottom')
    self._draw_inputbox()
    self._draw_pager()
    self.stdscr.move(self.term_height-1,\
        2)  # move the cursor to the input box
    self.stdscr.refresh()

  def _draw_inputbox(self):
    '''Draws the input box to the main window using a CustomTextbox.
    The input marker is drawn outside the input box.
    '''
    self.stdscr.addch(self.term_height-1, 0, '>') 
    self.input_win = curses.newwin(1, self.term_width, self.term_height-1, 2)
    self.input_box = CustomTextbox.CustomTextbox(self.input_win, 
        lambda: self.draw())
    self.input_win.overwrite(self.stdscr)
    self.input_win.refresh()
  
  def _draw_pager(self):
    if self.config:
      scrollback = int(self.config.get('preferences', 'Scrollback'))
    else:
      scrollback = 100  # default
    self.pager_pad = curses.newpad(scrollback, self.term_width)
    self.pager_pad.refresh(0, 0, 1, 0, self.term_height-3, self.term_width)

  def _draw_statusbar(self, pos, msg=None):
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

class GoldFinchModel():
  '''Container/volatile cache for data used by the program (model)'''

  def __init__(self):
    pass

class GoldFinch:
  '''curses based twitter client, written in python (controller)'''

  __version__ = 'svn' + filter(str.isdigit, '$Revision$')

  def __init__(self, stdscr):
    self.init_logger()
    self.stdscr = stdscr
    self.logger.info('Starting goldfinch')
    self.config = self.init_config()
    self.main_window = self.init_main_window()
    self.api = self.init_twitter_api()
    while True:
      self.parse_input()

  def parse_input(self):
    input_valid = False
    input_str = self.main_window.input_box.edit().strip()
    self.logger.debug('Got input: ' + input_str)
    input_parts = input_str.split()

    # one word commands
    if len(input_parts) == 1:
      if input_parts[0] == '/quit' or '/quit'.startswith(input_parts[0]):
        self.destruct()
    # two word commands
    if len(input_parts) == 2:
      if (input_parts[0] == '/list' or '/list'.startswith(input_parts[0]))\
          and (input_parts[1] == 'friends' or\
          'friends'.startswith(input_parts[1])):
        self.api.get_friends()
        # ... display

    if input_valid:
      self.main_window.input_box.clear()
    else:
      # TODO: alert user
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
    api = TwitterController()
    self.logger.info('Authenticating twitter api')
    try:
      api.perform_auth(os.path.join(os.environ['HOME'], 
        '.goldfinch', 'access_token'))
    except IOError as e:
      self.logger.error(e)
      # TODO: alert user
    self.logger.info('Done')
    return api
    
  def init_config(self):
    self.logger.info('Initialising config file')
    config = Config()
    filename = 'goldfinchrc'
    ret = ()
    try:
      config_file = os.path.join(os.environ['HOME'], '.goldfinch',
          filename)
      ret = config.load_config(config_file)
    except ConfigParser.ParsingError as e:
      self.destruct('Error reading config file.\nSee log file for details')
    if not ret:
      output = ''.join([filename, ' is empty or non existent.  ',
              'See README for examples on how to create one.'])
      self.destruct(output)
    mandatory_values = {
        'account':('accountname', 'oauthpin'),
        'preferences':('scrollback', 'ssl', 'confirmexit')
    }
    (config_ok, reason) = config.ensure_config(mandatory_values)
    if not config_ok:
      self.destruct(reason + ' is missing from config file.')
    config = config.get_config()
    self.logger.info('Done')
    return config

  def init_main_window(self):
    self.logger.info('Initialising main window')
    main_window = MainWindow(self.stdscr, self.config)
    main_window.draw()
    self.logger.info('Done')
    return main_window

  def destruct(self, error_msg=None):
    '''Clean up, write out an optional error message and exit.  (No error
    message implies a normal exit.'''
    ret = 0
    curses.endwin() 
    if error_msg:
      ret = 1
      self.logger.error(error_msg)
      print(error_msg)
    self.logger.info('exiting..')
    exit(ret)

class TwitterController:
  '''Makes use of the twitter API through 'tweepy'
  http://github.com/joshthecoder/tweepy'''

  def __init__(self):
    self.logger = logging.getLogger(''.join(
        ['goldfinch', '.', self.__class__.__name__]))

  def perform_auth(self, access_token_file):
    '''Reads in user's oauth key and secret from access_token_file
    (one per line), and authenticates and initialises the api'''
    access_token = {}
    with open(access_token_file) as f:
      access_token['key'] = f.readline().strip()
      access_token['secret'] = f.readline().strip()
    consumer_key = 'BRqDtHfWWNjNm4tLKj3g'
    consumer_secret = 'RzyFiyYutvxnKBzEUG2utiCejYgkPoDLAqMNNx3o'
    auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_token['key'], access_token['secret'])
    self.api = tweepy.API(auth)

  def get_friends(self):
    assert self.api, 'TwitterController.api is not initialised, call\
      TwitterController.perform_auth first'
    friend_list = self.api.friends_ids()
    return [self.api.get_user(friend).screen_name for friend in friend_list]

class Config():
  '''Provides convenience methods for loading a config file and validating
  it's contents.
  '''

  def __init__(self):
    self.logger = logging.getLogger(''.join(
        ['goldfinch', '.', self.__class__.__name__]))
    self.cp = None

  def load_config(self, filename):
    assert filename, 'filename is empty in call to Config.load_config'
    self.cp = ConfigParser.SafeConfigParser()
    ret = self.cp.read(filename)
    return ret

  def ensure_config(self, mandatory_values):
    '''Ensure config contains certain section:options.''' 
    for section,opt_list in mandatory_values.items():
      if not self.cp.has_section(section):
        return (False, section)
      for opt in opt_list:
        if not opt in self.cp.options(section):
          return (False, opt)
    return (True, None)

  def get_config(self):
    assert self.cp, 'Config.cp is None, try Config.load_config first'
    return self.cp

def main():
  curses.wrapper(GoldFinch)

if __name__ == '__main__':
  main()
