# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Photoframe is a Raspberry Pi-based digital photo frame application written in Python 3. It automatically pulls photos from various sources (Google Photos, Immich, USB, etc.) and displays them on attached screens. The application includes a web interface for configuration and supports advanced features like ambient color temperature adjustment and power management.

## Development Commands

### Running the Application
- **Development/Debug mode**: `./frame.py --debug --emulate`
- **Production**: `./photoframe.sh` (used by systemd service)
- **Service management**: 
  - `systemctl start frame.service`
  - `systemctl stop frame.service`
  - `systemctl restart frame.service`

### Updates and Maintenance
- **Update from git**: `./update.sh`
- **Check for updates**: `./update.sh checkversion`
- **Force update on boot**: `touch /boot/forceupdate.txt`

### Dependencies
- Install: `pip3 install -r requirements.txt`
- Key Python packages: flask, requests, oauthlib, flask_httpauth

## Architecture Overview

### Core Application Structure
- **`frame.py`**: Main entry point and application orchestrator
- **`photoframe.sh`**: Production wrapper script with update logic
- **`modules/`**: Core functionality modules
- **`routes/`**: Flask web interface routes
- **`services/`**: Photo source integrations

### Key Modules
- **`settings.py`**: Configuration management
- **`display.py`**: Display control and framebuffer management
- **`slideshow.py`**: Photo rotation and display logic
- **`servicemanager.py`**: Photo source service management
- **`colormatch.py`**: Ambient color temperature adjustment
- **`timekeeper.py`**: Scheduling and power management

### Service Architecture
Photo sources are implemented as services in `services/`:
- **`svc_googlephotos.py`**: Google Photos integration
- **`svc_immich.py`**: Immich photo server integration
- **`svc_usb.py`**: USB storage support
- **`svc_simpleurl.py`**: Basic URL image fetching

### Web Interface Routes
Flask routes in `routes/` provide web UI:
- **`settings.py`**: Main settings page
- **`service.py`**: Service management
- **`keywords.py`**: Photo keyword management
- **`immichconfigupload.py`**: Immich-specific configuration (separate from main config)

## Critical Architecture Rules

### Immich Integration Pattern
**ALWAYS use Immich-specific routes for Immich functionality**:
- Immich services use `/service/<id>/immichconfig` endpoint
- Traditional services use `/service/<id>/config` endpoint
- **NEVER modify existing routes** for Immich features
- Use dedicated ServiceManager methods: `setImmichServiceConfiguration()`, `validateImmichServiceConfiguration()`

### Service Configuration
- Services that need OAuth use `needOAuth=True`
- Immich services use `needImmichConfig=True` 
- All services extend `BaseService` from `services/base.py`

## File System Locations

### Configuration
- **Production config**: `/root/photoframe_config/`
- **Development/emulation**: `/tmp/photoframe/`
- Key config files: `settings.json`, `oauth.json`, `http_auth.json`

### Web Interface
- **Default port**: 7777
- **Default auth**: username=`photoframe`, password=`password`
- **Static files**: `static/` directory

## Development Notes

### Running in Emulation Mode
Use `--emulate` flag to run on desktop systems without GPIO/framebuffer access. This creates a test environment in `/tmp/photoframe/`.

### Display Configuration  
The application auto-detects display settings on first run. Display drivers support HDMI, SPI, and DPI interfaces.

### Service Development
When adding new photo services:
1. Extend `services/base.py`
2. Implement required methods (`getAlbums()`, `getImages()`, etc.)
3. Add route handler if custom configuration needed
4. Register service in ServiceManager

### Testing Integration
No formal test framework detected. Manual testing involves running with `--debug --emulate` flags.