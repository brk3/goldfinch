import unittest

import sys
sys.path.append('../src')

from goldfinchlib.statusbar import StatusBar

class StatusBarTest(unittest.TestCase):
  def setUp(self):
    self.statusbar = StatusBar()
    self.stdscr = Dummy_stdscr()

  def test_draw(self):
    self.statusbar.draw('bottom', self.stdscr)
    assert self.statusbar.position == 'bottom'
    self.statusbar.draw('top', self.stdscr)
    assert self.statusbar.position == 'top'

class Dummy_stdscr(object):
  def getmaxyx(self):
    return (119, 32)

  def addch(self, *args): pass 
  def refresh(self): pass

if __name__ == '__main__':
  unittest.main()
