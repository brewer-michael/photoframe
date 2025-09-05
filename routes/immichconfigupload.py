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

import logging
import json

from .baseroute import BaseRoute

class RouteImmichConfigUpload(BaseRoute):
    def setupex(self, servicemgr, slideshow):
        self.servicemgr = servicemgr
        self.slideshow = slideshow

        self.addUrl('/service/<service>/immichconfig').clearMethods().addMethod('POST')

    def handle(self, app, **kwargs):
        service = kwargs.get('service')
        if not service:
            logging.error('No service specified for Immich config upload')
            return self.setAbort(400)

        if self.getRequest().method == 'POST':
            # Handle Immich config file upload
            if 'filename' not in self.getRequest().files:
                logging.error('No file part in Immich config upload')
                return self.setAbort(405)
            
            file = self.getRequest().files['filename']
            if file.filename == '':
                logging.error('No file selected for Immich config upload')
                return self.setAbort(405)

            try:
                # Parse JSON config data
                data = json.load(file)
                logging.info(f'Immich config upload for service {service}: {len(str(data))} bytes')
                
                # Use Immich-specific service manager method to set configuration
                if self.servicemgr.setImmichServiceConfiguration(service, data):
                    # Trigger slideshow refresh if service state changed
                    old_ready = self.servicemgr.hasReadyServices()
                    new_ready = self.servicemgr.hasReadyServices()
                    if old_ready != new_ready:
                        self.slideshow.trigger()
                    
                    return 'Immich configuration uploaded successfully', 200
                else:
                    return 'Immich configuration was invalid or could not be set', 405
                    
            except json.JSONDecodeError as e:
                logging.error(f'Invalid JSON in Immich config file: {e}')
                return 'Invalid JSON format in Immich configuration file', 405
            except Exception as e:
                logging.error(f'Error processing Immich config upload: {e}')
                return 'Error processing Immich configuration file', 500
        else:
            return self.setAbort(405)