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

class StatusBar(object):
  def __init__(self, ypos, stdscr):
    '''Creates a single line 'statusbar' that can be placed on 
    a curses window.
    position -- The portion of the screen to place it.
                Can either be 'top or 'bottom'
    stdscr   -- Window object returned by curses.initscr()

    '''
    self.stdscr = stdscr
    (self.term_height, self.term_width) = self.stdscr.getmaxyx()
    self.ypos = ypos
    self.text_left = ''
    self.text_right = ''

  def draw(self):
    if self.text_left:
      # add left text and padding
      self.stdscr.addch(self.ypos, 0, ' ', curses.A_REVERSE)
      self.stdscr.addstr(self.ypos, 1, self.text_left, curses.A_REVERSE)
      # paint rest up to possible right text
      for i in range(len(self.text_left)+1, self.term_width-len(self.text_right)-1):
        try:
          self.stdscr.addch(self.ypos, i, ' ', curses.A_REVERSE)
        except curses.error as e: 
          pass
    else:
      # paint all the way up to possible right text
      for i in range(0, self.term_width-len(self.text_right)-1):
        try:
          self.stdscr.addch(self.ypos, i, ' ', curses.A_REVERSE)
        except curses.error as e: 
          pass
    start_text_at = self.term_width - len(self.text_right) - 1
    if self.text_right:
      # add right text and padding
      self.stdscr.addstr(self.ypos, start_text_at, self.text_right, curses.A_REVERSE)
      self.stdscr.addstr(self.ypos, 1, self.text_left, curses.A_REVERSE)
    else:
      for i in range(start_text_at, self.term_width):
        try:
          self.stdscr.addch(self.ypos, i, ' ', curses.A_REVERSE)
        except curses.error as e: 
          pass
    self.stdscr.refresh()

  def add_text(self, text, align):
    assert align == 'left' or align == 'right'
    if align == 'left':
      self.text_left = text
    elif align ==  'right':
      self.text_right = text
    self.draw()

