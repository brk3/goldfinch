import unittest

import sys
sys.path.append('../src')

from goldfinchlib.statusbar import StatusBar
from dummy_stdscr import Dummy_stdscr

class StatusBarTest(unittest.TestCase):
  def setUp(self):
    self.stdscr = Dummy_stdscr()
    self.statusbar = StatusBar(self.stdscr.getmaxyx()[0]-1, self.stdscr)

  def test_add_text(self):
    text = 'hello world'
    self.statusbar.add_text(text, 'left')
    assert self.statusbar.text_left == text

if __name__ == '__main__':
  unittest.main()
