# This file is part of photoframe (https://github.com/mrworf/photoframe).
#
# photoframe is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# photoframe is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with photoframe.  If not, see <http://www.gnu.org/licenses/>.
#
from services.base import BaseService
import os
import json
import logging
import time

from modules.network import RequestResult
from modules.helper import helper

class Immich(BaseService):
  SERVICE_NAME = 'Immich'
  SERVICE_ID = 10
  MAX_ITEMS = 8000

  def __init__(self, configDir, id, name):
    # Copy Google Photos pattern exactly, just use needImmichConfig instead of needOAuth
    BaseService.__init__(self, configDir, id, name, needConfig=False, needOAuth=False, needImmichConfig=True)

  # Replace OAuth methods with Config methods
  def getConfigurationFields(self):
    """
    Returns configuration fields needed for Immich connection.
    This creates the form fields that users will see in the web interface.
    """
    return {
      'server_url': {
        'type': 'STR', 
        'name': 'Server URL', 
        'description': 'Full URL to your Immich server (e.g., https://immich.example.com)'
      },
      'api_key': {
        'type': 'PW', 
        'name': 'API Key', 
        'description': 'Immich API key for authentication. Generate this in Immich User Settings.'
      }
    }

  def validateImmichConfiguration(self, config):
    """
    Validates the provided configuration.
    BaseService pattern: return None for success, error string for failure.
    """
    logging.info(f'Immich validateConfiguration called with config: {config}')
    
    # Basic validation of required fields
    if not config:
      logging.error('Immich validation failed: Configuration is required')
      return 'Configuration is required'
      
    if 'server_url' not in config or not config['server_url']:
      logging.error('Immich validation failed: Server URL is required')
      return 'Server URL is required'
      
    if 'api_key' not in config or not config['api_key']:
      logging.error('Immich validation failed: API Key is required')
      return 'API Key is required'
      
    # Validate URL format
    server_url = config['server_url'].strip()
    if not server_url.startswith(('http://', 'https://')):
      logging.error('Immich validation failed: Server URL must start with http:// or https://')
      return 'Server URL must start with http:// or https://'
      
    # Remove trailing slash for consistency
    if server_url.endswith('/'):
      config['server_url'] = server_url[:-1]
    
    # For Phase 1, just validate format - don't test actual connection
    logging.info('Immich configuration validated successfully (Phase 1 - format only)')
    return True  # ServiceManager expects True for success (despite BaseService comment)

  def helpKeywords(self):
    """
    Help text explaining what keywords mean for Immich.
    Copy Google Photos pattern.
    """
    return 'Each entry represents the name of an Immich album. Enter the exact album name as it appears in your Immich library.'

  def hasKeywordSourceUrl(self):
    # Copy Google Photos pattern
    return True

  def getExtras(self):
    # Copy Google Photos pattern exactly
    result = BaseService.getExtras(self)
    if result is None:
      return {}
    return result

  def postSetup(self):
    # Copy Google Photos pattern but simplified for Phase 1
    extras = self.getExtras()
    keywords = self.getKeywords()

    # For Phase 1, just ensure extras matches keywords
    if len(self.getKeywords()) == 0:
      extras = self.getExtras()
      if len(extras) > 0:
        logging.warning('Mismatch between keywords and extras info, corrected')
        self.setExtras({})

  def getKeywordSourceUrl(self, index):
    # Copy Google Photos pattern
    keys = self.getKeywords()
    if index < 0 or index >= len(keys):
      return f'Out of range, index = {index}'
    keyword = keys[index]
    extras = self.getExtras()
    if keyword not in extras:
      return 'http://your-immich-server/'  # Default fallback
    return extras[keyword]['sourceUrl']

  def getKeywordDetails(self, index):
    # Copy Google Photos pattern but simplified for Phase 1
    keys = self.getKeywords()
    if index < 0 or index >= len(keys):
      return f'Out of range, index = {index}'
    keyword = keys[index]

    # Phase 1: Return basic info since we don't fetch images yet
    return {
      'short': f'Album "{keyword}" configured (Phase 1 - no image fetching yet)',
      'long': ['Phase 1: Configuration complete', 'Image fetching will be implemented in Phase 2']
    }

  def hasKeywordDetails(self):
    # Copy Google Photos pattern
    return True

  def removeKeywords(self, index):
    # Copy Google Photos pattern exactly
    keys = self.getKeywords()
    if index < 0 or index >= len(keys):
      return
    keywords = keys[index].strip()
    filename = os.path.join(self.getStoragePath(), self.hashString(keywords) + '.json')
    if os.path.exists(filename):
      os.unlink(filename)
    if BaseService.removeKeywords(self, index):
      # Remove any extras
      extras = self.getExtras()
      if keywords in extras:
        del extras[keywords]
        self.setExtras(extras)
      return True
    else:
      return False

  def validateKeywords(self, keywords):
    # Copy Google Photos pattern but simplified for Phase 1
    tst = BaseService.validateKeywords(self, keywords)
    if tst["error"] is not None:
      return tst

    # Remove quotes and normalize
    if keywords[0] == '"' and keywords[-1] == '"':
      keywords = keywords[1:-1]
    keywords = keywords.strip()

    # Phase 1: Accept any non-empty keyword (album name)
    if not keywords:
      return {'error': 'Album name cannot be empty', 'keywords': keywords}

    # For Phase 1, we'll store a placeholder album info
    albumInfo = {
      'albumId': f'placeholder-{keywords}',
      'sourceUrl': f'{self.getConfiguration().get("server_url", "")}/albums',
      'albumName': keywords
    }

    return {'error': None, 'keywords': keywords, 'extras': albumInfo}

  def addKeywords(self, keywords):
    # Copy Google Photos pattern exactly
    result = BaseService.addKeywords(self, keywords)
    if result['error'] is None and result['extras'] is not None:
      k = result['keywords']
      extras = self.getExtras()
      extras[k] = result['extras']
      self.setExtras(extras)
    return result

  def selectImageFromAlbum(self, destinationDir, supportedMimeTypes, displaySize, randomize):
    # Copy Google Photos pattern but return Phase 1 message
    result = BaseService.selectImageFromAlbum(self, destinationDir, supportedMimeTypes, displaySize, randomize)
    if result is not None:
      return result

    # Phase 1: Return informative message instead of actual images
    return BaseService.createImageHolder(self).setError('Phase 1: Immich configuration complete.\nPhoto retrieval will be implemented in Phase 2.')

  def freshnessImagesFor(self, keyword):
    # Copy Google Photos pattern exactly
    filename = os.path.join(self.getStoragePath(), self.hashString(keyword) + '.json')
    if not os.path.exists(filename):
      return 0 # Superfresh
    # Hours should be returned
    return (time.time() - os.stat(filename).st_mtime) / 3600

  def clearImagesFor(self, keyword):
    # Copy Google Photos pattern exactly
    filename = os.path.join(self.getStoragePath(), self.hashString(keyword) + '.json')
    if os.path.exists(filename):
      os.unlink(filename)
    logging.info(f'Cleared image information for {keyword}')

  def getImagesFor(self, keyword, rawReturn=False):
    # Copy Google Photos pattern but return empty for Phase 1
    # This ensures the service is in READY state but shows no images
    logging.debug(f'Immich getImagesFor called with keyword: {keyword} (Phase 1 - returning empty list)')
    
    # For Phase 1, return empty list to avoid errors
    # This prevents the service from claiming it has images when it doesn't
    return []

  def parseAlbumInfo(self, data, keyword):
    # Copy Google Photos pattern - will be used in Phase 2
    result = []
    for entry in data:
      logging.debug(f'Entry: {repr(entry)}')
      result.append(self.createImageHolder().setId(entry['id']).setMimetype(entry.get('mimeType', 'image/jpeg')))
    return result

  def getContentUrl(self, image, hints):
    # Copy Google Photos pattern - will be implemented in Phase 2
    logging.debug('Immich getContentUrl called (Phase 1 - not implemented yet)')
    return None

  def getMessages(self):
    """
    Override to provide Immich-specific status messages.
    Copy Google Photos pattern.
    """
    msgs = BaseService.getMessages(self)
    
    # Add Phase 1 specific message
    if self.hasConfiguration():
      msgs.append({
        'level': 'INFO',
        'message': 'Phase 1: Immich service configured. Photo retrieval coming in Phase 2.',
        'link': None
      })
    
    return msgs

  def explainState(self):
    """
    Copy Google Photos pattern.
    """
    state = self.updateState()
    
    if state == BaseService.STATE_DO_CONFIG:
      return 'Please configure your Immich server URL and API key to connect to your Immich instance.'
    elif state == BaseService.STATE_NEED_KEYWORDS:
      return 'Add album names as keywords to specify which Immich albums to display photos from.'
    elif state == BaseService.STATE_NO_IMAGES:
      return 'Phase 1: Configuration complete. Photo retrieval will be implemented in Phase 2.'
    elif state == BaseService.STATE_READY:
      return 'Phase 1: Service configured and ready. Photo functionality coming in Phase 2.'
      
    return None