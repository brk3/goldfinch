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

from goldfinch.controllers import controller
import tweepy
import logging
import traceback
import os
import cPickle

class TwitterController(controller.Controller):
  '''Makes use of the twitter API through 'tweepy'
  http://github.com/joshthecoder/tweepy
  
  '''

  def __init__(self, cache_dir, config=None):
    controller.Controller.__init__(self, 140)
    self.logger = logging.getLogger(''.join(
        ['goldfinch', '.', self.__class__.__name__]))
    if config:
      timeout = int(config.get('preferences', 'Timeout'))
    else:
      timeout = 60  # default
    self.cachefile = os.path.join(cache_dir, 'twitter.cache')
  
  def perform_auth(self, access_token_file):
    access_token = {}
    with open(access_token_file) as f:
      access_token['key'] = f.readline().strip()
      access_token['secret'] = f.readline().strip()
    consumer_key = 'BRqDtHfWWNjNm4tLKj3g'
    consumer_secret = 'RzyFiyYutvxnKBzEUG2utiCejYgkPoDLAqMNNx3o'
    auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_token['key'], access_token['secret'])
    self.api = tweepy.API(auth)

  def get_friends(self, ret_queue):
    assert self.api, 'TwitterController.api is not initialised, call\
      TwitterController.perform_auth first'
    self.logger.debug('fetching friend ids')
    friend_dict = {} # {id:screen_name}
    try:
      with open(self.cachefile, 'r') as f:
        try:
          friend_dict = cPickle.load(f)
          self.logger.debug('found cache file')
        except (cPickle.PickleError, EOFError), e:
          self.logger.debug(traceback.format_exc())
          self.logger.info('could not unpickle friend_dict, fetching a new one')
    except IOError as e:
      self.logger.info('no cachefile present, will create one')
    self.logger.debug('fetching latest friend ids')
    latest_friend_ids = self.api.friends_ids()
    self.logger.debug('got latest friend ids')
    if friend_dict:
      # see whats changed
      current_friend_ids = friend_dict.keys()
      ids_added = set(latest_friend_ids) - set(current_friend_ids)
      ids_removed = set(current_friend_ids) - set(latest_friend_ids)
      for f_id in ids_added:
        self.logger.debug('found new friend, fetching details')
        friend_dict[f_id] = self.api.get_user(f_id).screen_name
      for f_id in ids_removed:
        self.logger.debug('found deleted friend, removing')
        del(friend_dict[f_id])
    else:
      # we have to fetch all ids:screen_names
      for f_id in latest_friend_ids:
        friend_dict[f_id] = self.api.get_user(f_id).screen_name
    with open(self.cachefile, 'w') as f:
      try:
        cPickle.dump(friend_dict, f)
        self.logger.debug('(re)wrote cache file')
      except cPickle.PickleError as e:
        self.logger.debug(traceback.format_exc())
        self.logger.info('error pickling friend_dict to cache file')
    self.logger.debug('put friend_dict.values into return queue')
    ret_queue.put(friend_dict.values()) 

  def get_home_timeline(self, count):
    '''Gets the users 'home timeline which is their tweets along with each of
    their friends.  Screen names are padded to 20 chars for formatting.
    
    count -- Specifies the number of statuses to retrieve.
    '''
    self.logger.info('fetching user home timeline')
    home_timeline = self.api.home_timeline(count=count)
    return [(item.user.screen_name, item.text) for item in home_timeline]
