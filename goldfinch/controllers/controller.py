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
