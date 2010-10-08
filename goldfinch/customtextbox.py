# $Id: CustomTextbox.py 39 2010-08-06 19:52:19Z bourke $

import curses.textpad
import logging

class CustomTextbox(curses.textpad.Textbox):
  def __init__(self, win, handlers):
    '''Initialises a CustomTextbox.

    win      -- curses.stdscr to attach the Textbox to
    handlers -- dict of various handlers to attatch, e.g.
                {curses.ascii.ESC:esc_handler}

    '''
    curses.textpad.Textbox.__init__(self, win)
    self.handlers = handlers
    self.mode = 'edit'
    self.logger = logging.getLogger('goldfinch' +
        "." + self.__class__.__name__)

  def do_command(self, ch):
    '''Overrides curses.textpad.Textbox.do_command() in order to hook 
    KEY_RESIZE and other keys.
    The code is mostly copy-pasted with modifications.

    ''' 
    (y, x) = self.win.getyx()
    self.lastcmd = ch
    if curses.ascii.isprint(ch):
      if y < self.maxy or x < self.maxx:
        if self.mode == 'edit':
          self._insert_printable_char(ch)
    elif ch == curses.ascii.NAK:                           # ^u
      self.clear()
    elif ch == curses.ascii.SOH:                           # ^a
      self.win.move(y, 0)
    elif ch in (curses.ascii.STX,curses.KEY_LEFT, curses.ascii.BS,curses.KEY_BACKSPACE):
      if x > 0:
        self.win.move(y, x-1)
      elif y == 0:
        pass
      elif self.stripspaces:
        self.win.move(y-1, self._end_of_line(y-1))
      else:
        self.win.move(y-1, self.maxx)
      if ch in (curses.ascii.BS, curses.KEY_BACKSPACE):
        self.win.delch()
    elif ch == curses.ascii.EOT:                           # ^d
      self.win.delch()
    elif ch == curses.ascii.ENQ:                           # ^e
      if self.stripspaces:
        self.win.move(y, self._end_of_line(y))
      else:
        self.win.move(y, self.maxx)
    elif ch in (curses.ascii.ACK, curses.KEY_RIGHT):       # ^f
      if x < self.maxx:
        self.win.move(y, x+1)
      elif y == self.maxy:
        pass
      else:
        self.win.move(y+1, 0)
    elif ch == curses.ascii.BEL:                           # ^g
      if self.mode == 'edit':
        return 0
    elif ch == curses.ascii.NL:                            # ^j
      if self.mode == 'edit':
        if self.maxy == 0:
          return 0
        elif y < self.maxy:
          self.win.move(y+1, 0)
    elif ch == curses.ascii.VT:                            # ^k
      if x == 0 and self._end_of_line(y) == 0:
        self.win.deleteln()
      else:
        # first undo the effect of self._end_of_line
        self.win.move(y, x)
        self.win.clrtoeol()
    elif ch == curses.ascii.FF:                            # ^l
      self.win.refresh()
    elif ch in (curses.ascii.SO, curses.KEY_DOWN):         # ^n
      if y < self.maxy:
        self.win.move(y+1, x)
      if x > self._end_of_line(y+1):
        self.win.move(y+1, self._end_of_line(y+1))
    elif ch == curses.ascii.SI:                            # ^o
      self.win.insertln()
    elif ch in (curses.ascii.DLE, curses.KEY_UP):          # ^p
      if y > 0:
        self.win.move(y-1, x)
        if x > self._end_of_line(y-1):
          self.win.move(y-1, self._end_of_line(y-1))
    for event,handler_item in self.handlers.items():
      if ch == event:
        # unpack the handler function and any args
        handler_func = handler_item[0]
        if len(handler_item) > 1:
          handler_args = handler_item[1]
        else:
          handler_args = []
        handler_func(*handler_args)
    return 1

  def insert_printable_str(self, msg):
    '''Adds a string to the Textbox''' 
    assert len(msg) < 256, "len(msg) must be < 256"
    self.clear()
    for i in range(0, len(msg)):
      self._insert_printable_char(msg[i])

  def clear(self):
    (y, x) = self.win.getyx()
    self.win.deleteln()
    self.win.move(y, 0)
