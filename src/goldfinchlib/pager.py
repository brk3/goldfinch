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

class Pager(object):
  def __init__(self, stdscr, scrollback):
    self.stdscr = stdscr
    self.scrollback = scrollback
    self.scroll_pos = 0
    (self.term_height, self.term_width) = self.stdscr.getmaxyx()

  def draw(self):
    '''Creates a window from curses.newpad and draws to stdscr'''
    self.pager_pad = curses.newpad(scrollback, self.term_width) 
    self.pager_pad.refresh(self.scroll_pos, 0, 1, 0, self.term_height-3, self.term_width)
    self.pager_pad.scrollok(True)
    self.pager_pad.idlok(True)
    self.stdscr.refresh()

  def add_text(self, text):
    pass
