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
    self.pager = Pager(self.stdscr, self.scrollback)
    assert self.pager is not None
    assert self.pager.scrollback == self.scrollback
    assert self.pager.scroll_pos == 0
    assert (self.pager.term_height, self.pager.term_width) \
        == self.stdscr.getmaxyx()
    assert self.pager.scrollback == self.scrollback

  def test_add_text(self):
    msg1 = 'hello world'
    content_queue = Queue.Queue()
    self.pager.add_text(msg1)


if __name__ == '__main__':
  unittest.main()
