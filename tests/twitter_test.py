import unittest

import sys
sys.path.append('../src')

import os
import Queue

from goldfinchlib.controllers import twitter
from goldfinch import GoldFinch

class TwitterControllerTestCase(unittest.TestCase):
  def setUp(self):
    self.controller = twitter.TwitterController(GoldFinch.config_dir)
    self.controller.perform_auth(os.path.join(GoldFinch.config_dir, 'access_token')) 

  def test_get_friends(self):
    friend_queue = Queue.Queue()
    self.controller.get_friends(friend_queue)
    assert friend_queue is not None, 'this may be OK if you have no friends ;)'

  def test_get_home_timeline(self):
    timeline = self.controller.get_home_timeline(10)
    assert len(timeline) == 10
    
if __name__ == '__main__':
  unittest.main()
