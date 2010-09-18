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

