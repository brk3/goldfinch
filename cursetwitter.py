# $Id$

import curses
import curses.wrapper

import CustomTextbox

import os
import logging
import logging.handlers
import ConfigParser

import twitter

class MainWindow:
  def __init__(self, stdscr, config):
    self.logger = logging.getLogger(CurseTwitter.progname +
        "." + self.__class__.__name__)
    self.stdscr = stdscr
    self.config = config

  def draw(self):
    """ Draws the interface components to the screen """
    (self.term_height, self.term_width) = self.stdscr.getmaxyx()
    self._draw_statusbar(CurseTwitter.progname + ' v' + 
        CurseTwitter.version, 'top')
    self._draw_statusbar(self.config.get('account', 'UserName'), 'bottom')
    self._draw_inputbox()
    self._draw_timeline(None)
    self.stdscr.move(self.term_height-1, 2)  # move the cursor to the input box
    self.stdscr.refresh()

  def get_input(self):
    """
    Puts the inputbox in edit mode and returns the contents on Enter or ^g 
    Note that this function is blocking
    """
    self.input_box.edit()
    return self.input_box.gather()

  def _draw_inputbox(self):
    """ 
    Draws the input box to the main window using a CustomTextbox.
    The input marker is drawn outside the input box.
    """
    self.stdscr.addch(self.term_height-1, 0, '>') 
    self.input_win = curses.newwin(1, self.term_width, self.term_height-1, 2)
    self.input_box = CustomTextbox.CustomTextbox(self.input_win, lambda: self.draw())
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
    """ Inits a Config object and sets rc location to $HOME/prognamerc. """
    self.logger = logging.getLogger(''.join([CurseTwitter.progname,
        '.', self.__class__.__name__]))
    self.filename = os.path.join(os.environ['HOME'], 
        '.'+CurseTwitter.progname+'rc')

  def load_config(self):
    cp = ConfigParser.SafeConfigParser()
    try:
      ret = cp.read(self.filename)
    except ConfigParser.ParsingError as e:
      self.logger.error(e)
      curses.endwin()
      print('Error reading config file at ' + self.filename)
      print('See log file for details.')
      exit(1)
    if len(ret) == 0:
      self.logger.error(self.filename + ' is empty or non existent.')
      curses.endwin()
      print(self.filename + ' is empty or non existent.')
      print('Please see README for examples on creating one.')
      exit(1)
    return cp 

class CurseTwitter:
  progname = 'cursetwitter'
  version = '0.1'

  def __init__(self, stdscr):
    self.init_logger()
    self.config = Config().load_config()
    self.logger.info('Starting ' + self.progname)
    self.main_window = MainWindow(stdscr, self.config)
    self.main_window.draw()
    self.logger.debug('MainWindow initialized')
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
    """ Sets up a logging object which can be accessed from other classes """
    self.logger = logging.getLogger(self.progname)
    self.logger.setLevel(logging.DEBUG)
    handler = logging.handlers.RotatingFileHandler(
        'cursetwitter.log', maxBytes=1024*100, backupCount=5)
    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - \
        %(message)s')
    handler.setFormatter(formatter)
    self.logger.addHandler(handler)

def main():
  curses.wrapper(CurseTwitter)

if __name__ == '__main__':
  main()
