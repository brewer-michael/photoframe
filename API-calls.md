# Immich API Integration Documentation

This document details how to interact with the Immich API from the photoframe application.

## Configuration

The Immich service requires configuration stored in JSON format containing:
- `server_url`: Full URL to Immich server (e.g., "http://192.168.1.8:8080")
- `api_key`: Immich API key for authentication

Current configuration fields in immich-config.json:
- `hostname`: "http://192.168.1.8:8080" 
- `api-key`: "################"

**Note**: Configuration field names appear to be inconsistent between immich-config.json and the service implementation.

## API Endpoints Used

### 1. Get All Albums
**Endpoint**: `GET /api/albums`
**Purpose**: Discover available albums on the Immich server
**Headers**: 
- `x-api-key`: {api_key}
- `Accept`: application/json

**Example Request**:
```bash
curl -H "x-api-key: ################" \
     -H "Accept: application/json" \
     "http://192.168.1.8:8080/api/albums"
```

**Response**: Array of album objects containing:
- `id`: Album UUID
- `albumName` or `name`: Album display name
- `description`: Album description
- `assetCount`: Number of assets in album
- `createdAt`: Creation timestamp
- `updatedAt`: Last update timestamp

### 2. Get Album Details with Assets
**Endpoint**: `GET /api/albums/{albumId}`
**Purpose**: Get album metadata including all asset references
**Headers**: 
- `x-api-key`: {api_key}

**Example Request**:
```bash
curl -H "x-api-key: ################" \
     "http://192.168.1.8:8080/api/albums/{album-id-here}"
```

**Response**: Album object with `assets` array containing asset references with minimal info.

### 3. Get Full Asset Information
**Endpoint**: `GET /api/assets/{assetId}`
**Purpose**: Get complete metadata for a specific asset
**Headers**: 
- `x-api-key`: {api_key}

**Example Request**:
```bash
curl -H "x-api-key: ################" \
     "http://192.168.1.8:8080/api/assets/{asset-id-here}"
```

**Response**: Full asset object containing:
- `id`: Asset UUID
- `type`: "IMAGE" or "VIDEO"
- `mimeType`: MIME type (e.g., "image/jpeg")
- `originalFileName`: Original file name
- `width`, `height`: Image dimensions
- `exifInfo`: EXIF metadata including dimensions

### 4. Download Original Asset
**Endpoint**: `GET /api/assets/{assetId}/original`
**Purpose**: Download the original image file
**Headers**: 
- `x-api-key`: {api_key}

**Example Request**:
```bash
curl -H "x-api-key: ################" \
     "http://192.168.1.8:8080/api/assets/{asset-id-here}/original" \
     -o downloaded_image.jpg
```

## Implementation Flow

1. **Album Discovery**: Call `/api/albums` to get all available albums
2. **Album Matching**: Find album with name matching "Yosemite" (case-insensitive)
3. **Asset Retrieval**: Call `/api/albums/{albumId}` to get asset list
4. **Asset Details**: For each asset, call `/api/assets/{assetId}` to get full metadata
5. **Image Download**: Use `/api/assets/{assetId}/original` to download image files

## Authentication

All API calls must include the `x-api-key` header with the configured API key.

## Error Handling

- **401 Unauthorized**: Invalid or missing API key
- **404 Not Found**: Album or asset not found
- **Network errors**: Retry with exponential backoff (implemented in service)

## Issues Identified and Fixed

### 1. Configuration Field Mismatch ✅ FIXED
The original `immich-config.json` used incorrect field names:
- ❌ File had: `hostname` and `api-key`  
- ✅ Service expects: `server_url` and `api_key`
- **Fixed**: Updated immich-config.json with correct field names

### 2. Method Name Error ✅ FIXED  
The `svc_immich.py` service had an incorrect method override:
- ❌ `selectImageFromAlbum()` - This method doesn't exist in BaseService
- ✅ Should override `selectRandomImageFromAlbum()` and `selectNextImageFromAlbum()` separately
- **Fixed**: Corrected method names in svc_immich.py:485-495

### 3. API Integration Verified ✅ WORKING
Manual testing confirms all API endpoints work correctly:
- ✅ Get Albums: Successfully lists albums including "Yosemite"  
- ✅ Get Album Contents: Returns asset IDs for album contents
- ✅ Get Asset Details: Returns full metadata for individual assets
- ✅ Download Assets: Manual curl downloads work (1.07MB test image)

### Root Cause Summary
The service was failing to download images because:
1. Configuration wasn't being read due to field name mismatch
2. The service was calling a non-existent method, preventing the download flow from executing properly

Both issues have been resolved.