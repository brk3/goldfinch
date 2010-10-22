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

class Controller:
  '''Controller interface'''

  def __init__(self, max_msg_length):
    '''Initialises a new controller instance.

    max_msg_length -- the maximum length allowed for a status update.
        (twitter is 140).

    '''
    self.max_msg_length = max_msg_length

  def perform_auth(self, access_token_file):
    '''Authenticates and initialises the api using oauth.

    access_token_file -- file containing the user's oauth key and secret.
    file should be in the form: 
    
    key
    secret 
    
    '''
    raise NotImplementedError

  def get_friends(self, ret_queue):
    '''Query the api for the user's list of friends.

    ret_queue -- Queue.Queue to put the result into
    
    '''
    raise NotImplementedError
