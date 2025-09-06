# Phase 2 Implementation Roadmap: Immich Integration

## Project Overview

This document provides the comprehensive technical implementation plan for Phase 2A of PhotoFrame's Immich integration, created by the chief-python-architect. The plan focuses on implementing core album discovery functionality while maintaining strict architectural integrity.

## Phase 2A: Core Album Discovery (Tasks 1-8)

### Executive Summary

Phase 2A implements the foundational album discovery functionality for Immich integration. This includes connecting to Immich APIs, discovering albums, retrieving album metadata, and integrating with PhotoFrame's existing BaseService architecture without modifying core PhotoFrame systems.

### Current Status
- ✅ Phase 1: Configuration system complete
- 🔄 Phase 2A: Core Album Discovery (in planning)
- ⏳ Phase 2B: Asset Retrieval (pending)
- ⏳ Phase 2C: Error Handling & Polish (pending)

## Technical Architecture

### API Integration Strategy

**Primary Immich API Endpoints:**
1. `GET /api/albums` - Retrieve all user albums
2. `GET /api/albums/{id}` - Get specific album details and assets
3. `GET /api/assets/{id}` - Get individual asset metadata and download URLs

**Authentication Pattern:**
```
Headers: {
  'x-api-key': {user_api_key},
  'Content-Type': 'application/json'
}
```

**Connection Validation:**
- Test connectivity during `validateImmichConfiguration()`
- Use `/api/albums?pageSize=1` for validation
- Return specific error messages for common issues

### BaseService Integration

**Files Modified:**
- `G:\repos\photoframe\services\svc_immich.py` (primary implementation)

**Files NOT Modified (Critical):**
- `services\base.py` - No changes to BaseService core
- `modules\servicemanager.py` - No changes to ServiceManager
- `modules\server.py` - No changes to error handling architecture

**Method Implementation Strategy:**
```python
def methodName(self, params):
    # Call parent for common functionality
    result = BaseService.methodName(self, params)
    
    # Add Immich-specific logic
    # Transform data to BaseService format
    
    return result
```

## Task Breakdown (Phase 2A: Tasks 1-8)

### Task 1: Enhance Configuration Validation
**Objective:** Add real connection testing to Immich server during configuration
**Methods:** `validateImmichConfiguration()`
**Implementation:**
- Test API connectivity to `/api/albums?pageSize=1`
- Validate API key permissions
- Return descriptive error messages
- Maintain Phase 1 backward compatibility

**Success Criteria:**
- Configuration validation tests actual server connectivity
- Invalid API keys detected with clear error messages
- Server unreachability handled gracefully

### Task 2: Implement Album Discovery  
**Objective:** Core album listing and search functionality
**Methods:** `translateKeywordToId()`, new helper methods
**Implementation:**
- Query `/api/albums` for all user albums
- Implement case-insensitive album name matching
- Handle shared albums discovery
- Cache album metadata for performance

**Success Criteria:**
- Albums discoverable by name through web interface
- Album names resolve to Immich album IDs
- Shared albums included in search results

### Task 3: Album Assets Retrieval
**Objective:** Get images/videos from specific albums
**Methods:** `getImagesFor()`, `parseAlbumInfo()`
**Implementation:**
- Query album assets via `/api/albums/{id}`
- Parse Immich asset format to ImageHolder objects
- Handle pagination for large albums
- Filter supported media types

**Success Criteria:**
- Album contents retrieved and cached
- ImageHolder objects created with proper metadata
- Large albums handled through pagination

### Task 4: Asset URL Resolution
**Objective:** Convert asset IDs to downloadable URLs
**Methods:** `getContentUrl()`
**Implementation:**
- Query individual asset details via `/api/assets/{id}`
- Extract download URLs from Immich responses
- Handle size optimization hints
- Support various media formats

**Success Criteria:**
- Asset IDs resolve to valid download URLs
- Size hints respected for optimization
- Multiple media formats supported

### Task 5: Query Builder Implementation
**Objective:** Parameter building for Immich API calls
**Methods:** `getQueryForKeyword()`, helper methods
**Implementation:**
- Build REST parameters for album queries
- Handle filtering options (shared albums, media type)
- Support pagination tokens
- Mirror Google Photos query patterns

**Success Criteria:**
- API queries constructed correctly
- Filtering options work as expected
- Pagination handled seamlessly

### Task 6: Caching and Persistence
**Objective:** Album data caching and state management
**Methods:** Storage integration, state management
**Implementation:**
- Cache album lists in service private directory
- Implement cache freshness checking
- Integrate with existing BaseService state patterns
- Handle cache invalidation scenarios

**Success Criteria:**
- Album data cached efficiently
- Cache freshness managed properly
- No conflicts with existing state management

### Task 7: Error Handling Integration
**Objective:** Comprehensive error handling aligned with PhotoFrame patterns
**Methods:** All API methods, error handling
**Implementation:**
- Map Immich API errors to PhotoFrame error types
- Use existing RequestResult patterns for HTTP errors
- Provide user-friendly error messages
- Integrate with BaseService error reporting

**Success Criteria:**
- Immich errors mapped to PhotoFrame error types
- User-friendly error messages displayed
- No conflicts with existing error handling

### Task 8: Testing and Validation
**Objective:** Comprehensive testing of album discovery functionality
**Methods:** All implemented methods
**Implementation:**
- Test album discovery with various configurations
- Validate error handling scenarios
- Test memory management integration
- Verify BaseService compatibility

**Success Criteria:**
- All functionality tested thoroughly
- Error scenarios handled correctly
- Memory management works properly
- Full BaseService compatibility maintained

## API Request/Response Specifications

### Album Discovery Request
```python
url = f"{server_url}/api/albums"
headers = {'x-api-key': api_key}
params = {'shared': 'true'}  # Include shared albums
```

### Expected Album Response
```json
[
  {
    "id": "album-uuid",
    "albumName": "My Vacation Photos", 
    "albumThumbnailAssetId": "asset-uuid",
    "assetCount": 150,
    "assets": [...]
  }
]
```

### Data Transformation Patterns

**Immich Album → PhotoFrame Format:**
```python
{
    'albumId': immich_album['id'],
    'sourceUrl': f"{server_url}/albums/{immich_album['id']}", 
    'albumName': immich_album['albumName']
}
```

**Immich Asset → ImageHolder Format:**
```python
self.createImageHolder()
    .setId(immich_asset['id'])
    .setMimetype(immich_asset.get('type', 'image/jpeg'))
    .setSource(f"{server_url}/photos/{immich_asset['id']}")
```

## Risk Assessment

### LOW RISK (Safe to implement)
- Album discovery and metadata fetching (read-only)
- Configuration validation and storage
- BaseService method overrides for album listing

### MEDIUM RISK (Requires careful testing)
- Image URL resolution and download processes
- Error handling integration with existing patterns
- Memory management integration

### HIGH RISK (Avoid completely)
- Modifications to BaseService or ServiceManager core
- Changes to existing error handling architecture
- Modifications to PhotoFrame's state management

## Implementation Timeline

**Week 1: Configuration and Album Discovery**
- Tasks 1-2: Enhanced config validation and album discovery
- Deliverable: Albums discoverable through web interface

**Week 2: Asset Retrieval and URL Resolution**
- Tasks 3-4: Album asset retrieval and URL resolution
- Deliverable: Image metadata cached and accessible

**Week 3: Query Building and Caching**
- Tasks 5-6: Query optimization and caching system
- Deliverable: Performance optimized album access

**Week 4: Error Handling and Testing**
- Tasks 7-8: Complete error handling and comprehensive testing
- Deliverable: Production-ready Phase 2A implementation

## Rollback Strategy

### Phase 2A Rollback
- Revert `getImagesFor()` to return empty list (Phase 1 state)
- Clear `_IMMICH_CONFIG` to force reconfiguration
- No data loss - configuration preserved

### Emergency Rollback
- Disable Immich service in ServiceManager
- Comment out service detection if needed
- Full PhotoFrame functionality preserved

## Success Criteria

**Phase 2A Complete When:**
1. ✅ Albums discoverable and listed through web interface
2. ✅ Album names resolve to actual Immich album IDs
3. ✅ Image metadata retrieved and cached properly
4. ✅ Error handling integrated with PhotoFrame patterns
5. ✅ Memory management tracks viewed images correctly
6. ✅ Service integrates seamlessly with ServiceManager
7. ✅ No regressions in existing PhotoFrame functionality
8. ✅ Comprehensive test coverage of core functionality

## Development Guidelines

### CRITICAL CONSTRAINTS
- **DO NOT** modify BaseService or ServiceManager core logic
- **DO NOT** touch PhotoFrame's existing error handling architecture
- **DO NOT** make unauthorized git commits
- **FOLLOW** strict architect → approval → developer → QA workflow
- **TEST** one change at a time with zero tolerance for regressions

### Workflow Requirements
- Product Manager (User) approval required before implementation
- All code changes reviewed by QA before deployment
- Container stability verified after each change
- Git commits only with explicit user permission

---

**Document Created:** Phase 2 Planning Session
**Architect:** chief-python-architect  
**Status:** Ready for Product Manager approval
**Next Step:** Await user approval to proceed with Task 1 implementation