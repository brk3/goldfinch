import unittest

import sys
sys.path.append('../src')

import Queue

from goldfinchlib.pager import Pager
from dummy_stdscr import Dummy_stdscr

class PagerTestCase(unittest.TestCase):
  def setUp(self):
    self.scrollback = 200
    self.stdscr = Dummy_stdscr()
    self.pager = Pager(self.scrollback, self.stdscr)
    assert self.pager is not None
    assert self.pager.scrollback == self.scrollback
    assert self.pager.scroll_pos == 0
    assert self.pager.text_ypos == 0
    assert (self.pager.term_height, self.pager.term_width) \
        == self.stdscr.getmaxyx()
  
  def test_add_text(self):
    text = 'hello world'
    #TODO: make a dummy textpad
    #self.pager.pager_pad = None
    #self.pager.add_text(text)
    #assert self.pager.content_queue.get() == text

if __name__ == '__main__':
  unittest.main()
