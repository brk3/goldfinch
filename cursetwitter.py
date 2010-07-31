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
    self._draw_statusbar(self.config.get('account', 'UserName'), 'bottom')
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
    if pos.lower() == 'top':
      ypos = 0
    elif pos.lower() == 'bottom':
      ypos = self.term_height-2
    else:
      raise AssertionError("status bar pos must be either 'top' or 'bottom'.\
          you gave: " + pos)
    self.stdscr.addch(ypos, 0, ' ', curses.A_REVERSE)
    self.stdscr.addstr(ypos, 1, msg, curses.A_REVERSE)
    for i in range(len(msg)+1, self.term_width):
      try:
        self.stdscr.addch(ypos, i, ' ',
            curses.A_REVERSE)
      except curses.error:
        pass

class Config:
  def __init__(self):
    '''Inits a Config object and sets rc location to
    os.path.join($HOME, 'cursetwitter', 'cursetwitter'+'rc').
    '''
    self.logger = logging.getLogger(''.join(
        ['cursetwitter', '.', self.__class__.__name__]))
    self.filename = os.path.join(os.environ['HOME'], '.cursetwitter',
        'cursetwitterrc')
    self.logger.debug(self.filename)

  def load_config(self):
    cp = ConfigParser.SafeConfigParser()
    ret = cp.read(self.filename)
    assert len(ret) > 0,\
        ''.join([self.filename, ' is empty or non existent.  ',
        'See README for examples on how to create one.'])
    return cp

class CurseTwitter:
  __version__ = '0.1'
  name = 'cursetwitter'

  def __init__(self, stdscr):
    self.init_logger()
    try:
      self.config = Config().load_config()
    except ConfigParser.ParsingError as e:
      logger.error(e)
      curses.endwin()
      print('Error reading config file.\nSee log file for details')
      exit(1)
    except AssertionError as e:
      self.logger.error(e)
      curses.endwin()
      print('config file is empty or non existent.')
      print('Please see README for examples on creating one.')
      exit(1)
    self.logger.info('Starting ' + self.name)
    self.main_window = MainWindow(stdscr, self.config)
    self.main_window.draw()
    self.logger.debug('MainWindow initialized')
    self.init_twitter_api()
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
    self.logger = logging.getLogger(self.name)
    self.logger.setLevel(logging.DEBUG)
    handler = logging.handlers.RotatingFileHandler(
        'cursetwitter.log', maxBytes=1024*100, backupCount=3)
    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - \
        %(message)s')
    handler.setFormatter(formatter)
    self.logger.addHandler(handler)

  def init_twitter_api(self):
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
    twitter = OAuthApi(consumer_key, consumer_secret, 
        access_token['oauth_token'], access_token['oauth_token_secret'])
    self.logger.debug(twitter.GetUserTimeline())
    self.logger.info('Twitter API sucessfully initialized')

def main():
  curses.wrapper(CurseTwitter)

if __name__ == '__main__':
  main()
