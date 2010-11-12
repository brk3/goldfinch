import unittest

from goldfinch_test import GoldFinchTestCase
from statusbar_test import StatusBarTest
from twitter_test import TwitterControllerTestCase
from pager_test import PagerTestCase 

suite = unittest.TestSuite()
suite.addTests([unittest.makeSuite(GoldFinchTestCase)])
suite.addTests([unittest.makeSuite(StatusBarTest)])
suite.addTests([unittest.makeSuite(TwitterControllerTestCase)])
suite.addTests([unittest.makeSuite(PagerTestCase)])

if __name__ == '__main__':
  unittest.TextTestRunner(verbosity=2).run(suite)
