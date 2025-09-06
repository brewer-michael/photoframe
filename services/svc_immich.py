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
import requests

from modules.network import RequestResult, RequestNoNetwork
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
    # Enhanced to show real album details
    keys = self.getKeywords()
    if index < 0 or index >= len(keys):
      return f'Out of range, index = {index}'
    keyword = keys[index]
    extras = self.getExtras()
    
    if keyword not in extras:
      return {
        'short': f'Album "{keyword}" not found in extras',
        'long': ['Album information missing', 'Try removing and re-adding this album']
      }
    
    album_info = extras[keyword]
    asset_count = album_info.get('assetCount', 0)
    created_at = album_info.get('createdAt', 'Unknown')
    description = album_info.get('description', 'No description')
    
    return {
      'short': f'Album "{keyword}" - {asset_count} assets',
      'long': [
        f'Album ID: {album_info.get("albumId", "Unknown")}',
        f'Assets: {asset_count}',
        f'Created: {created_at[:10] if created_at != "Unknown" else "Unknown"}',
        f'Description: {description if description else "No description"}',
        'Phase 1: Photo retrieval will be implemented in Phase 2'
      ]
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

  def discoverAlbums(self):
    """
    Discover albums from Immich server by calling GET /api/albums.
    Returns dict with 'success', 'albums', and 'error' keys.
    Albums list contains dicts with 'id', 'albumName', etc.
    """
    config = self.getImmichConfiguration()
    if not config or 'server_url' not in config or 'api_key' not in config:
      return {'success': False, 'albums': [], 'error': 'Immich configuration not found'}
    
    server_url = config['server_url']
    api_key = config['api_key']
    
    # Construct the albums API endpoint
    albums_url = f"{server_url}/api/albums"
    
    # Set up headers with API key authentication
    headers = {
      'x-api-key': api_key,
      'Accept': 'application/json'
    }
    
    try:
      logging.debug(f'Immich discoverAlbums: calling GET {albums_url}')
      
      # Use the same retry logic as BaseService.requestUrl
      tries = 0
      response = None
      while tries < 5:
        try:
          response = requests.get(albums_url, headers=headers, timeout=180)
          break
        except requests.exceptions.RequestException as e:
          logging.exception(f'Issues calling Immich albums API, attempt {tries + 1}')
          if tries == 4:  # Last attempt
            raise RequestNoNetwork(f'Failed to connect to Immich server: {str(e)}')
        
        time.sleep(tries * 10)  # Back off 10, 20, ... depending on tries
        tries += 1
        logging.warning(f'Retrying Immich albums API call, attempt #{tries + 1}')
      
      if response.status_code == 200:
        albums_data = response.json()
        logging.info(f'Immich discoverAlbums: successfully retrieved {len(albums_data)} albums')
        return {'success': True, 'albums': albums_data, 'error': None}
      elif response.status_code == 401:
        logging.error(f'Immich API authentication failed: {response.status_code}')
        return {'success': False, 'albums': [], 'error': 'Authentication failed. Please check your API key.'}
      else:
        logging.error(f'Immich albums API returned error: {response.status_code} - {response.text}')
        return {'success': False, 'albums': [], 'error': f'Server returned error {response.status_code}'}
        
    except RequestNoNetwork as e:
      logging.error(f'Immich discoverAlbums network error: {str(e)}')
      return {'success': False, 'albums': [], 'error': f'Network error: {str(e)}'}
    except Exception as e:
      logging.exception('Unexpected error in discoverAlbums')
      return {'success': False, 'albums': [], 'error': f'Unexpected error: {str(e)}'}

  def validateKeywords(self, keywords):
    # Follow BaseService pattern for validation
    tst = BaseService.validateKeywords(self, keywords)
    if tst["error"] is not None:
      return tst

    # Remove quotes and normalize
    if len(keywords) >= 2 and keywords[0] == '"' and keywords[-1] == '"':
      keywords = keywords[1:-1]
    keywords = keywords.strip()

    # Basic validation
    if not keywords:
      return {'error': 'Album name cannot be empty', 'keywords': keywords}

    # Discover albums from Immich server
    discovery_result = self.discoverAlbums()
    if not discovery_result['success']:
      logging.error(f'Immich album discovery failed: {discovery_result["error"]}')
      return {'error': f'Failed to connect to Immich server: {discovery_result["error"]}', 'keywords': keywords}
    
    albums = discovery_result['albums']
    if not albums:
      return {'error': 'No albums found on Immich server', 'keywords': keywords}
    
    # Find matching album(s) - case insensitive search
    matching_albums = []
    keyword_lower = keywords.lower()
    
    for album in albums:
      # Handle both 'albumName' and 'name' fields for robustness
      album_name = album.get('albumName', album.get('name', ''))
      if album_name and album_name.lower() == keyword_lower:
        matching_albums.append(album)
    
    # Handle matching results
    if len(matching_albums) == 0:
      available_names = [album.get('albumName', album.get('name', 'Unknown')) for album in albums[:10]]
      available_list = ', '.join(available_names)
      if len(albums) > 10:
        available_list += f', ... and {len(albums) - 10} more'
      return {'error': f'No album found with name "{keywords}". Available albums: {available_list}', 'keywords': keywords}
    
    if len(matching_albums) > 1:
      logging.warning(f'Multiple albums found with name "{keywords}", using the first one')
    
    # Use the first matching album
    matched_album = matching_albums[0]
    
    # Construct album info with real data
    config = self.getImmichConfiguration()
    server_url = config.get('server_url', '')
    
    albumInfo = {
      'albumId': matched_album.get('id'),
      'sourceUrl': f'{server_url}/albums/{matched_album.get("id")}',
      'albumName': matched_album.get('albumName', matched_album.get('name', keywords)),
      'description': matched_album.get('description', ''),
      'assetCount': matched_album.get('assetCount', 0),
      'createdAt': matched_album.get('createdAt', ''),
      'updatedAt': matched_album.get('updatedAt', '')
    }
    
    logging.info(f'Immich album discovered: "{keywords}" -> ID: {albumInfo["albumId"]}, Assets: {albumInfo["assetCount"]}')
    
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