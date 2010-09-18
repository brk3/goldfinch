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
        except (cPickle.PickleError, EOFError), e:
          self.logger.debug(traceback.format_exc())
          self.logger.info('could not unpickle friend_dict, fetching a new one')
    except IOError as e:
      self.logger.info('no cachefile present, will create one')
    latest_friend_ids = self.api.friends_ids()
    if friend_dict:
      # see whats changed
      current_friend_ids = friend_dict.keys()
      ids_added = set(latest_friend_ids) - set(current_friend_ids)
      ids_removed = set(current_friend_ids) - set(latest_friend_ids)
      for f_id in ids_added:
        friend_dict[f_id] = self.api.get_user(f_id).screen_name
      for f_id in ids_removed:
        del(friend_dict[f_id])
    else:
      # we have to fetch all ids:screen_names
      for f_id in latest_friend_ids:
        friend_dict[f_id] = self.api.get_user(f_id).screen_name
    with open(self.cachefile, 'w') as f:
      try:
        cPickle.dump(friend_dict, f)
      except cPickle.PickleError as e:
        self.logger.debug(traceback.format_exc())
        self.logger.info('error pickling friend_dict to cache file')
    ret_queue.put(friend_dict.values()) 

  def get_home_timeline(self):
    '''Gets the users 'home timeline which is their tweets along with each of
    their friends.  Screen names are padded to 20 chars for formatting.'''
    self.logger.info('fetching user home timeline')
    home_timeline = self.api.home_timeline()
    return [
        (item.user.screen_name+': ').ljust(20) +
        item.text
        for item in home_timeline
        ]
