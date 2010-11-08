import unittest

import sys
sys.path.append('../src')

import string
import random
import os

from goldfinch import GoldFinch

class GoldFinchTestCase(unittest.TestCase):
  def setUp(self):
    self.goldfinch = GoldFinch(None)

  def tearDown(self):
    try:
      self.goldfinch.cleanup()
    except SystemExit as e:
      pass

  def test_init_logger(self):
    self.goldfinch.init_logger()
    assert self.goldfinch.logger is not None
    assert os.path.isfile(self.goldfinch.log_file)
    log_msg = 'test from GoldFinchTestCase.test_init_logger()'
    self.goldfinch.logger.debug(log_msg)
    with open(self.goldfinch.log_file) as log_file:
      assert ''.join(log_file.readlines()).find(log_msg) > -1

  def test_init_twitter_api(self):
    api = self.goldfinch.init_twitter_api()
    assert api is not None

  def test_init_config(self):
    self.goldfinch.init_config()
    assert self.goldfinch.config is not None

  def test_format_status_line(self):
    '''Create a large random tweet and ensure integrity is 
    preserved after formatting.
    '''
    self.goldfinch.main_window = Dummy_MainWindow()
    screen_name = 'timmy'
    large_tweet = ''
    for i in range(140):
      large_tweet = large_tweet + str(i)
    line = self.goldfinch.format_status_line(screen_name, large_tweet)
    assert len(line) > 0
    assert line[0].strip().startswith(screen_name)
    assert ''.join(line).replace(' ', '') == screen_name+large_tweet

class Dummy_MainWindow(object):
  def __init__(self):
    self.term_width = 32

if __name__ == '__main__':
  unittest.main()


