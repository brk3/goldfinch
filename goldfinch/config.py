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

import logging
import ConfigParser

class Config:
  '''Provides convenience methods for loading a config file and validating
  it's contents.

  '''
  
  def __init__(self):
    self.logger = logging.getLogger(''.join(\
        ['goldfinch', '.', self.__class__.__name__]))
    self.cp = None

  def load_config(self, filename):
    '''Loads a config file using the ConfigParser module.

    filename -- fully qualified path to file containing config
    
    '''
    assert filename, 'filename is empty in call to Config.load_config'
    self.cp = ConfigParser.SafeConfigParser()
    ret = self.cp.read(filename)
    return ret

  def ensure_config(self, mandatory_values):
    '''Ensure config contains certain section:options.''' 
    for section,opt_list in mandatory_values.items():
      if not self.cp.has_section(section):
        return (False, section)
      for opt in opt_list:
        if not opt in self.cp.options(section):
          return (False, opt)
    return (True, None)

  def get_config(self):
    '''Convenience method to return a copy of the loaded config.'''
    assert self.cp, 'Config.cp is None, try Config.load_config first'
    return self.cp

