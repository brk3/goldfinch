class Dummy_stdscr(object):
  '''A 'dummy' class to mimic the basic model of a curses.stdscr object
  for unit testing purposes.

  '''
  def __init__(self):
    self.content = []

  def getmaxyx(self): 
    return (119, 32) # this is my default terminal size

  def addch(self, *args): 
    self.content.append(args[2])
  
  def addstr(self, *args):
    self.content.append(args[2])

  def clear(self):
    self.content = []

  def refresh(self): 
    pass
