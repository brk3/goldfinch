# $Id$

try:
  import curses
  import curses.wrapper
  import CustomTextbox
  from oauth import oauth
  from oauthtwitter import OAuthApi
except ImportError as e:
  print(e)
  exit(1)

import os
import logging
import logging.handlers
import ConfigParser
import cPickle

class MainWindow:
  def __init__(self, stdscr, config):
    self.logger = logging.getLogger('cursetwitter' +
        "." + self.__class__.__name__)
    self.stdscr = stdscr
    self.config = config

  def draw(self):
    '''Draws the interface components to the screen'''
    (self.term_height, self.term_width) = self.stdscr.getmaxyx()
    self._draw_statusbar('cursetwitter' + ' v' + 
        CurseTwitter.__version__, 'top')
    self._draw_statusbar(self.config.get('account', 'accountname'), 'bottom')
    self._draw_inputbox()
    self._draw_timeline(None)
    self.stdscr.move(self.term_height-1, 2)  # move the cursor to the input box
    self.stdscr.refresh()

  def get_input(self):
    '''Puts the inputbox in edit mode and returns the contents on Enter or ^g 
    Note that this function is blocking.
    '''
    self.input_box.edit()
    return self.input_box.gather()

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
  
  def _draw_timeline(self, user):
    scrollback = int(self.config.get('preferences', 'Scrollback'))
    self.pager_pad = curses.newpad(scrollback, self.term_width)
    self.pager_pad.addstr(0, 0, 'hello world')
    self.pager_pad.refresh(0, 0, 1, 0, self.term_height-3, self.term_width)

  def _draw_statusbar(self, msg, pos):
    assert pos == 'top' or pos == 'bottom', 'status bar pos must be either \
        \'top\' or \'bottom\'. You gave: ' + pos
    if pos.lower() == 'top':
      ypos = 0
    elif pos.lower() == 'bottom':
      ypos = self.term_height-2
    self.stdscr.addch(ypos, 0, ' ', curses.A_REVERSE)
    self.stdscr.addstr(ypos, 1, msg, curses.A_REVERSE)
    for i in range(len(msg)+1, self.term_width):
      try:
        self.stdscr.addch(ypos, i, ' ', curses.A_REVERSE)
      except curses.error:
        pass

class Config():
  def __init__(self, validate=None):
    '''Inits a Config object and sets rc location to
    os.path.join($HOME, 'cursetwitter', 'cursetwitter'+'rc').
    '''
    self.logger = logging.getLogger(''.join(
        ['cursetwitter', '.', self.__class__.__name__]))
    self.filename = os.path.join(os.environ['HOME'], '.cursetwitter',
        'cursetwitterrc')
    self.cp = None

  def load_config(self):
    self.cp = ConfigParser.SafeConfigParser()
    ret = self.cp.read(self.filename)
    assert len(ret) > 0,\
        ''.join([self.filename, ' is empty or non existent.  ',
        'See README for examples on how to create one.'])

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
    assert self.cp is not None, 'Config.cp is None'
    return self.cp

class CurseTwitter:
  __version__ = '0.1'

  def __init__(self, stdscr):
    self.init_logger()
    self.stdscr = stdscr
    self.logger.info('Starting cursetwitter')

    self.init_config()
    self.init_main_window()
    self.init_twitter_api()

    refresh_interval = self.config.getint('preferences', 'interval')
    if refresh_interval < 60:
      self.logger.info('interval cannot be less than 60 seconds')
      refresh_interval = 60
    # ...

    while True:
      self.parse_input()

  def parse_input(self):
    input_valid = False
    input_str = self.main_window.get_input().strip()
    self.logger.debug(input_str)
    if input_str == '/quit':
      curses.endwin()
      self.logger.info("Exiting")
      exit(0)
    if input_valid is True:
      self.main_window.input_box.clear()
    else:
      # TODO: alert user in pager display
      self.main_window.input_box.clear()
      pass

  def init_logger(self):
    ''' Sets up a logging object which can be accessed from other classes '''
    self.logger = logging.getLogger('cursetwitter')
    self.logger.setLevel(logging.DEBUG)
    handler = logging.handlers.RotatingFileHandler(
        'cursetwitter.log', maxBytes=1024*100, backupCount=3)
    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - \
        %(message)s')
    handler.setFormatter(formatter)
    self.logger.addHandler(handler)

  def init_twitter_api(self):
    self.logger.info('Initialising twitter Api')
    try:
      FILE = open(os.path.join(os.environ['HOME'], 
          '.cursetwitter', 'access_token'))
      access_token = cPickle.load(FILE)
    except IOError as e:
      self.logger.error(e)
      #TODO: alert user and offer to generate one
    except cPickle.PickleError as e:
      self.logger.error(e)
      #TODO: alert user and offer to generate a new one
    consumer_key = 'BRqDtHfWWNjNm4tLKj3g'
    consumer_secret = 'RzyFiyYutvxnKBzEUG2utiCejYgkPoDLAqMNNx3o'
    self.twitter = OAuthApi(consumer_key, consumer_secret, 
        access_token['oauth_token'], access_token['oauth_token_secret'])
    self.logger.info('Twitter Api loaded')

  def update_timeline_cb(self):
    ''' Get the user's list of friends, get each of their statuses, and pass
    to main window to be drawn '''
    self.logger.info('updating timeline..')
    return True

  def init_config(self):
    self.logger.info('Initialising config file')
    self.config = Config()
    try:
      self.config.load_config()
    except ConfigParser.ParsingError as e:
      self.logger.error(e)
      curses.endwin()
      print('Error reading config file.\nSee log file for details')
      exit(1)
    except AssertionError as e:
      self.logger.error(e)
      curses.endwin()
      print('config file is empty or non existent.')
      print('Please see README for examples on creating one.')
      exit(1)
    mandatory_values = {
        'account':('accountname', 'oauthpin'),
        'preferences':('scrollback', 'ssl', 'confirmexit', 'interval')
    }
    (config_ok, reason) = self.config.ensure_config(mandatory_values)
    if not config_ok:
      self.logger.info(reason + ' is missing from config file.') 
      exit(1)
      #TODO: alert user and continue no further
    self.config = self.config.get_config()
    self.logger.info('Config file loaded')

  def init_main_window(self):
    self.logger.info('Initialising main window')
    self.main_window = MainWindow(self.stdscr, self.config)
    self.main_window.draw()
    self.logger.info('Main window loaded')

def main():
  curses.wrapper(CurseTwitter)

if __name__ == '__main__':
  main()
