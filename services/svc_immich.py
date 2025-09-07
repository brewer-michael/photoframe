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
import shutil

from modules.network import RequestResult, RequestNoNetwork
from modules.helper import helper


class ImmichAlbum:
    """Represents an Immich album."""
    def __init__(self, data, server_url):
        self.album_id = data.get('id')
        self.album_name = data.get('albumName', data.get('name', 'Unknown'))
        self.description = data.get('description', '')
        self.asset_count = data.get('assetCount', 0)
        self.created_at = data.get('createdAt', '')
        self.updated_at = data.get('updatedAt', '')
        self.server_url = server_url
        self.assets = [ImmichAsset(a, server_url) for a in data.get('assets', [])]

    def source_url(self):
        return f'{self.server_url}/albums/{self.album_id}'


class ImmichAsset:
    """Represents a single asset within an Immich album."""
    SUPPORTED_MIME_TYPES = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif',
                            'image/webp', 'image/tiff', 'image/tif', 'image/bmp']

    def __init__(self, data, server_url):
        self.asset_id = data.get('id')
        self.original_file_name = data.get('originalFileName')
        self.mime_type = data.get('type') or 'image/jpeg'
        self.exif_info = data.get('exifInfo', {})
        self.server_url = server_url

        if self.mime_type not in self.SUPPORTED_MIME_TYPES:
            self.mime_type = None

    def is_valid(self):
        return self.asset_id is not None and self.mime_type is not None

    def get_content_url(self):
        if not self.asset_id:
            return None
        return f'{self.server_url}/api/assets/{self.asset_id}/original'


class Immich(BaseService):
    SERVICE_NAME = 'Immich'
    SERVICE_ID = 10
    MAX_ITEMS = 8000

    def __init__(self, configDir, id, name):
        BaseService.__init__(self, configDir, id, name, needConfig=False, needOAuth=False, needImmichConfig=True)

    # ------------------ Configuration ------------------

    def getConfigurationFields(self):
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
        logging.info(f'Immich validateConfiguration called with config: {config}')
        if not config:
            return 'Configuration is required'
        if 'server_url' not in config or not config['server_url']:
            return 'Server URL is required'
        if 'api_key' not in config or not config['api_key']:
            return 'API Key is required'
        server_url = config['server_url'].strip()
        if not server_url.startswith(('http://', 'https://')):
            return 'Server URL must start with http:// or https://'
        if server_url.endswith('/'):
            config['server_url'] = server_url[:-1]
        logging.info('Immich configuration validated successfully (Phase 1 - format only)')
        return True

    def helpKeywords(self):
        return 'Each entry represents the name of an Immich album. Enter the exact album name as it appears in your Immich library.'

    def hasKeywordSourceUrl(self):
        return True

    def getExtras(self):
        result = BaseService.getExtras(self)
        if result is None:
            return {}
        return result

    def postSetup(self):
        extras = self.getExtras()
        if len(self.getKeywords()) == 0 and len(extras) > 0:
            logging.warning('Mismatch between keywords and extras info, corrected')
            self.setExtras({})

    def getKeywordSourceUrl(self, index):
        keys = self.getKeywords()
        if index < 0 or index >= len(keys):
            return f'Out of range, index = {index}'
        keyword = keys[index]
        extras = self.getExtras()
        if keyword not in extras:
            return 'http://your-immich-server/'
        return extras[keyword]['sourceUrl']

    def getKeywordDetails(self, index):
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
                'Real photo retrieval now available'
            ]
        }

    def hasKeywordDetails(self):
        return True

    def removeKeywords(self, index):
        keys = self.getKeywords()
        if index < 0 or index >= len(keys):
            return
        keywords = keys[index].strip()
        filename = os.path.join(self.getStoragePath(), self.hashString(keywords) + '.json')
        if os.path.exists(filename):
            os.unlink(filename)
        if BaseService.removeKeywords(self, index):
            extras = self.getExtras()
            if keywords in extras:
                del extras[keywords]
                self.setExtras(extras)
            return True
        return False

    # ------------------ Album Discovery ------------------

    def getQueryForKeyword(self, keyword):
        result = None
        extras = self.getExtras()
        if extras is None:
            extras = {}
        if keyword in extras:
            result = {'albumId': extras[keyword]['albumId']}
        return result

    def discoverAlbums(self):
        config = self.getImmichConfiguration()
        if not config or 'server_url' not in config or 'api_key' not in config:
            return {'success': False, 'albums': [], 'error': 'Immich configuration not found'}

        server_url = config['server_url']
        api_key = config['api_key']
        albums_url = f"{server_url}/api/albums"
        headers = {'x-api-key': api_key, 'Accept': 'application/json'}

        try:
            logging.debug(f'Immich discoverAlbums: calling GET {albums_url}')
            tries = 0
            response = None
            while tries < 5:
                try:
                    response = requests.get(albums_url, headers=headers, timeout=180)
                    break
                except requests.exceptions.RequestException as e:
                    logging.exception(f'Issues calling Immich albums API, attempt {tries + 1}')
                    if tries == 4:
                        raise RequestNoNetwork(f'Failed to connect to Immich server: {str(e)}')
                time.sleep(tries * 10)
                tries += 1
                logging.warning(f'Retrying Immich albums API call, attempt #{tries + 1}')

            if response.status_code == 200:
                albums_data = response.json()
                logging.info(f'Immich discoverAlbums: successfully retrieved {len(albums_data)} albums')
                return {'success': True, 'albums': albums_data, 'error': None}
            elif response.status_code == 401:
                return {'success': False, 'albums': [], 'error': 'Authentication failed. Check your API key.'}
            else:
                return {'success': False, 'albums': [], 'error': f'Server returned error {response.status_code}'}

        except RequestNoNetwork as e:
            return {'success': False, 'albums': [], 'error': f'Network error: {str(e)}'}
        except Exception as e:
            return {'success': False, 'albums': [], 'error': f'Unexpected error: {str(e)}'}

    # ------------------ Keywords / Album Lookup ------------------

    def validateKeywords(self, keywords):
        tst = BaseService.validateKeywords(self, keywords)
        if tst["error"] is not None:
            return tst

        if len(keywords) >= 2 and keywords[0] == '"' and keywords[-1] == '"':
            keywords = keywords[1:-1]
        keywords = keywords.strip()
        if not keywords:
            return {'error': 'Album name cannot be empty', 'keywords': keywords}

        discovery_result = self.discoverAlbums()
        if not discovery_result['success']:
            return {'error': f'Failed to connect to Immich server: {discovery_result["error"]}', 'keywords': keywords}

        albums = discovery_result['albums']
        if not albums:
            return {'error': 'No albums found on Immich server', 'keywords': keywords}

        matching_albums = [a for a in albums if (a.get('albumName') or a.get('name', '')).lower() == keywords.lower()]
        if len(matching_albums) == 0:
            available_names = [a.get('albumName', a.get('name', 'Unknown')) for a in albums[:10]]
            available_list = ', '.join(available_names)
            if len(albums) > 10:
                available_list += f', ... and {len(albums) - 10} more'
            return {'error': f'No album found with name "{keywords}". Available albums: {available_list}', 'keywords': keywords}

        matched_album = matching_albums[0]
        config = self.getImmichConfiguration()
        server_url = config.get('server_url', '') if config else ''

        albumInfo = {
            'albumId': matched_album.get('id'),
            'sourceUrl': f'{server_url}/albums/{matched_album.get("id")}',
            'albumName': matched_album.get('albumName', matched_album.get('name', keywords)),
            'description': matched_album.get('description', ''),
            'assetCount': matched_album.get('assetCount', 0),
            'createdAt': matched_album.get('createdAt', ''),
            'updatedAt': matched_album.get('updatedAt', '')
        }

        return {'error': None, 'keywords': keywords, 'extras': albumInfo}

    def addKeywords(self, keywords):
        result = BaseService.addKeywords(self, keywords)
        if result['error'] is None and result['extras'] is not None:
            k = result['keywords']
            extras = self.getExtras()
            extras[k] = result['extras']
            self.setExtras(extras)
        return result

    # ------------------ Image Retrieval ------------------

    def getImagesFor(self, keyword, rawReturn=False):
        """Get images for keyword, now fetching full asset info from Immich"""
        logging.warning(f'IMMICH GETIMAGESFOR CALLED: keyword="{keyword}", rawReturn={rawReturn}')
        
        # Step 1: Get query like Google Photos does
        query = self.getQueryForKeyword(keyword)
        if query is None:
            logging.error(f'Unable to create query for keyword "{keyword}"')
            return []

        # Step 2: Get Immich config
        config = self.getImmichConfiguration()
        if not config or 'server_url' not in config or 'api_key' not in config:
            logging.error('Immich configuration not found')
            return []

        headers = {'x-api-key': config['api_key']}

        # Step 3: Fetch album metadata (contains asset IDs)
        album_url = f"{config['server_url']}/api/albums/{query['albumId']}"
        try:
            response = requests.get(album_url, headers=headers, timeout=30)
            if not response.ok:
                logging.warning(f'Immich API call failed with status {response.status_code}')
                return []

            album_data = response.json()
            asset_refs = album_data.get('assets', [])
            if not asset_refs:
                logging.error(f'No assets found in album response for keyword "{keyword}"')
                return []

            # Step 4: Fetch full info for each asset
            full_assets = []
            for i, asset in enumerate(asset_refs):
                asset_id = asset.get('id')
                if not asset_id:
                    continue
                asset_url = f"{config['server_url']}/api/assets/{asset_id}"
                try:
                    asset_resp = requests.get(asset_url, headers=headers, timeout=30)
                    if asset_resp.ok:
                        full_assets.append(asset_resp.json())
                    else:
                        logging.warning(f'Failed to fetch asset {asset_id}: {asset_resp.status_code}')
                except Exception as e:
                    logging.exception(f'Error fetching asset {asset_id}: {e}')

        except Exception as e:
            logging.error(f'Failed to get images for keyword "{keyword}": {e}')
            return []

        # Step 5: Cache to JSON file
        filename = os.path.join(self.getStoragePath(), self.hashString(keyword) + '.json')
        try:
            with open(filename, 'w') as f:
                json.dump(full_assets, f)
        except Exception as e:
            logging.exception(f'Failed to save JSON cache file: {e}')

        # Step 6: Handle rawReturn
        if rawReturn:
            return full_assets

        # Step 7: Parse and return as ImageHolder objects
        return self.parseAlbumInfo(full_assets, keyword)


    def parseAlbumInfo(self, data, keyword):
        """Convert Immich assets to ImageHolder objects that BaseService can use"""
        logging.info(f'Parsing {len(data)} assets for keyword "{keyword}"')
        result = []

        # Define supported MIME types (matching what photoframe supports)
        supported_images = {
          'image/jpeg', 'image/jpg', 'image/png', 'image/gif',
          'image/webp', 'image/tiff', 'image/tif', 'image/bmp'
        }

        for i, asset in enumerate(data):
          # Get asset ID (required)
          asset_id = asset.get('id')
          if not asset_id:
            logging.warning(f'Asset {i+1} missing ID, skipping')
            continue

          # --- START: CORRECTED LOGIC ---

          # 1. Use the 'type' field to correctly identify and skip videos.
          asset_type = asset.get('type')
          if asset_type == 'VIDEO':
            logging.debug(f'Asset {i+1}: skipping video {asset_id} based on type field')
            continue
          
          # 2. Get the actual mimeType.
          mime_type = asset.get('mimeType')

          # 3. If mimeType is missing, infer it from the filename.
          if not mime_type:
            original_filename = (asset.get('originalFileName', '') or '').lower()
            if original_filename.endswith(('.jpg', '.jpeg')):
              mime_type = 'image/jpeg'
            elif original_filename.endswith('.png'):
              mime_type = 'image/png'
            elif original_filename.endswith('.gif'):
              mime_type = 'image/gif'
            elif original_filename.endswith('.webp'):
              mime_type = 'image/webp'
            elif original_filename.endswith(('.tiff', '.tif')):
              mime_type = 'image/tiff'
            elif original_filename.endswith('.bmp'):
              mime_type = 'image/bmp'
            else:
              # If we can't determine, log it and skip.
              logging.warning(f'Asset {i+1} ({asset_id}): could not determine mimeType, skipping.')
              continue

          # 4. Filter out unsupported image types.
          if mime_type not in supported_images:
            logging.debug(f'Asset {i+1}: skipping unsupported type {mime_type}')
            continue
          
          # --- END: CORRECTED LOGIC ---

          # Create ImageHolder with proper metadata
          image = self.createImageHolder()
          image.setId(asset_id)
          image.setMimetype(mime_type)

          # Add filename if available
          original_filename = asset.get('originalFileName')
          if original_filename:
            image.setFilename(original_filename)

          # Set dimensions if available from EXIF
          exif_info = asset.get('exifInfo', {}) or {}
          width = exif_info.get('exifImageWidth')
          height = exif_info.get('exifImageHeight')
          if width and height:
            try:
              image.setDimensions(int(width), int(height))
            except (ValueError, TypeError):
              pass

          # Enable caching for performance
          image.allowCache(True)

          result.append(image)
          logging.debug(f'Added asset {asset_id} ({mime_type}) to results')

        logging.info(f'Parsed {len(result)} supported images from {len(data)} total assets')
        return result

    def getContentUrl(self, image, hints):
        config = self.getImmichConfiguration()
        if not config or 'server_url' not in config:
            return None
        asset_id = image.getId()
        if not asset_id:
            return None
        return f"{config['server_url']}/api/assets/{asset_id}/original"
        #return f"{config['server_url']}/api/asset/file/{asset_id}"

    # ------------------ Misc ------------------

    def freshnessImagesFor(self, keyword):
        filename = os.path.join(self.getStoragePath(), self.hashString(keyword) + '.json')
        if not os.path.exists(filename):
            return 0
        return (time.time() - os.stat(filename).st_mtime) / 3600

    def clearImagesFor(self, keyword):
        filename = os.path.join(self.getStoragePath(), self.hashString(keyword) + '.json')
        if os.path.exists(filename):
            os.unlink(filename)
        logging.info(f'Cleared image information for {keyword}')

    def selectImageFromAlbum(self, destinationDir, supportedMimeTypes, displaySize, randomize):
        result = BaseService.selectImageFromAlbum(self, destinationDir, supportedMimeTypes, displaySize, randomize)
        if result is not None:
            return result
        return BaseService.createImageHolder(self).setError('Immich service ready.\nReal photo retrieval available for configured albums.')
    
    #Download the image files
    # def downloadContentTo(self, url, destination):
    #   """
    #   Override the download method to include Immich API authentication.
    #   This is crucial - without this, the BaseService can't download Immich images.
    #   """
    #   config = self.getImmichConfiguration()
    #   if not config or 'api_key' not in config:
    #     logging.error('Immich API key not found for download')
    #     return False

    #   headers = {
    #     'x-api-key': config['api_key'],
    #     'Accept': 'image/*'
    #   }

    #   try:
    #     # Ensure the destination directory exists before writing
    #     os.makedirs(os.path.dirname(destination), exist_ok=True)

    #     logging.info(f'Downloading Immich asset from {url} to {destination}')

    #     # Use requests to download with authentication
    #     response = requests.get(url, headers=headers, stream=True, timeout=60)

    #     if response.status_code == 200:
    #       # Write the image data to the destination file
    #       with open(destination, 'wb') as f:
    #         for chunk in response.iter_content(chunk_size=8192):
    #           if chunk:
    #             f.write(chunk)

    #       logging.info(f'Successfully downloaded Immich asset to {destination}')
    #       return True
    #     else:
    #       logging.error(f'Failed to download Immich asset: HTTP {response.status_code}')
    #       return False

    #   except requests.exceptions.RequestException as e:
    #     logging.error(f'Network error downloading Immich asset: {e}')
    #     return False
    #   except Exception as e:
    #     logging.error(f'Error downloading Immich asset: {e}')
    #     return False
    def downloadContentTo(self, url, destination):
      """
      Final override of the download method. Uses a session for auth persistence
      and shutil.copyfileobj for a robust, memory-efficient file stream.
      """
      config = self.getImmichConfiguration()
      if not config or 'api_key' not in config:
        logging.error('Immich API key not found for download')
        return False

      try:
        # Ensure the destination directory exists before writing
        os.makedirs(os.path.dirname(destination), exist_ok=True)

        logging.info(f'Attempting to download from {url} to {destination}')

        with requests.Session() as s:
            s.headers.update({
                'x-api-key': config['api_key'],
                'Accept': 'image/*'
            })
            # Start the request, but don't load the whole file in memory
            with s.get(url, stream=True, timeout=60) as r:
                # Check for errors on the response
                r.raise_for_status()
                
                # Use a temporary file to prevent corruption on failed downloads
                temp_destination = destination + ".tmp"
                
                # Open the destination file and stream the content into it
                with open(temp_destination, 'wb') as f:
                    shutil.copyfileobj(r.raw, f)
        
        # If the download was successful, move the temp file to the final destination
        os.rename(temp_destination, destination)

        logging.info(f'Successfully downloaded and saved Immich asset to {destination}')
        return True

      except requests.exceptions.HTTPError as e:
          logging.error(f'HTTP Error during download: {e.response.status_code} {e.response.reason}')
          logging.error(f'Response body: {e.response.text}')
          return False
      except Exception as e:
          # Log the full exception to get the real root cause
          logging.exception(f'An unexpected error occurred in downloadContentTo: {e}')
          return False
      
    def getMessages(self):
        msgs = BaseService.getMessages(self)
        if self.hasConfiguration():
            msgs.append({
                'level': 'INFO',
                'message': 'Immich service configured and ready. Photo retrieval available for added albums.',
                'link': None
            })
        return msgs

    def explainState(self):
        state = self.updateState()
        if state == BaseService.STATE_DO_CONFIG:
            return 'Please configure your Immich server URL and API key to connect to your Immich instance.'
        elif state == BaseService.STATE_NEED_KEYWORDS:
            return 'Add album names as keywords to specify which Immich albums to display photos from.'
        elif state == BaseService.STATE_NO_IMAGES:
            return 'Immich service configured. Add album keywords to display photos from your Immich albums.'
        elif state == BaseService.STATE_READY:
            return 'Immich service ready. Real photo retrieval available from configured albums.'
        return None
