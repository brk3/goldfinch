#!/usr/bin/env python

# Copyright (C) 2010 Paul Bourke <pauldbourke@gmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

# $Id$
# ex: expandtab tabstop=2 shiftwidth=2:

import curses

import Queue

class Pager(object):
  '''Creates a simple WindowObject returned by curses.newpad and 
  adds convience functions for drawing text, scrolling, etc.
  
  '''

  def __init__(self, scrollback, stdscr, logger=None):
    '''Initialises a Pager object.

    scrollback -- how many lines to hold in the scroll buffer
    stdscr -- curses window to draw to
    logger -- optional logger object mainly for debug purposes

    '''
    self.scrollback = scrollback
    self.stdscr = stdscr
    self.logger = logger
    self.scroll_pos = 0
    self.text_ypos = 0
    self.content_queue = Queue.Queue()
    (self.term_height, self.term_width) = self.stdscr.getmaxyx()

  def draw(self):
    '''Draw the pager to screen'''
    self.pager_pad = curses.newpad(self.scrollback, self.term_width) 
    self.pager_pad.refresh(self.scroll_pos, 0, 1, 0, self.term_height-3, self.term_width)
    self.pager_pad.scrollok(True)
    self.pager_pad.idlok(True)
    self.stdscr.refresh()

  def add_text(self, text):
    '''Add a line or lines of text to the pager'''
    assert hasattr(self, 'pager_pad'), 'You must call Pager.draw() ' +\
        'prior to adding text.'
    self.content_queue.put(text)
    self._draw_text()

  def _draw_text(self):
    content = self.content_queue.get()
    if type(content) is not list:
      content = [content]
    for line in content:
      try:
        self.pager_pad.addstr(self.text_ypos, 0, str(line))
        self.text_ypos = self.text_ypos + 1
      except curses.error as e:
        if self.logger:
          self.logger.error(e)
          self.logger.error(line)
      except UnicodeEncodeError as e:
        #TODO: fix unicode support (see note at top of curses howto)
        if self.logger:
          self.logger.error(e)
          self.logger.error(line)
        break
    self.pager_pad.refresh(0, 0, 1, 0, self.term_height-3,\
        self.term_width)
    self.stdscr.refresh()

  def scroll(self, lines): 
    '''Scroll the pager.  Should be able to use window.scroll for this
    but couldn't get to work for some reason.
    
    lines -- number of lines to scroll. (negative to scroll up)

    '''
    try:
      self.pager_pad.refresh(self.scroll_pos+lines, 0, 1,\
          0, self.term_height-3, self.term_width)
      if (lines < 0) and (abs(lines) - self.scroll_pos > 0):
        self.scroll_pos = 0
      else:
        self.scroll_pos = self.scroll_pos + lines
    except curses.error as e:
      self.logger.error(e)

  def erase(self):
    '''Clear the pager contents'''
    self.pager_pad.erase()
    self.text_ypos = 0
