import unittest

import sys
sys.path.append('../src')

from goldfinch import GoldFinch

class GoldFinchTestCase(unittest.TestCase):
  def runTest(self):
    goldfinch = GoldFinch(None)

if __name__ == "__main__":
  unittest.main()


