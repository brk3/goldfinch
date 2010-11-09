import unittest

import sys
sys.path.append('../src')

from goldfinchlib.statusbar import StatusBar

class StatusBarTest(unittest.TestCase):
  def setUp(self):
    self.stdscr = Dummy_stdscr()
    self.statusbar = StatusBar(self.stdscr.getmaxyx()[0]-1, self.stdscr)

  def test_add_text(self):
    text = 'hello world'
    self.statusbar.add_text(text, 'left')
    assert self.statusbar.text_left == text

class Dummy_stdscr(object):
  def getmaxyx(self): return (119, 32)
  def addch(self, *args): pass 
  def addstr(self, *args): pass 
  def refresh(self): pass

if __name__ == '__main__':
  unittest.main()
