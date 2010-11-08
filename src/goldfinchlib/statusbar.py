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
  def __init__(self, ):
    self.text_left = ''
    self.text_right = ''
    self.position = ''

  def draw(self, position, stdscr):
    assert position == 'top' or position == 'bottom'
    (self.term_height, self.term_width) = stdscr.getmaxyx()
    self.position = position
    if self.position == 'top':
      ypos = 0
    elif self.position == 'bottom':
      ypos = self.term_height-2
    for i in range(0, self.term_width):
      try:
        stdscr.addch(ypos, i, ' ', curses.A_REVERSE)
      except curses.error as e:
        pass
    stdscr.refresh()


