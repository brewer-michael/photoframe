# Phase 2B Implementation Roadmap: Asset Retrieval & Display

## Project Overview

This document provides the technical implementation plan for Phase 2B of PhotoFrame's Immich integration. Phase 2B focuses on asset retrieval, image downloading, and display optimization after Phase 2A establishes album discovery.

## Phase 2B: Asset Retrieval (Tasks 9-15)

### Executive Summary

Phase 2B implements the core photo retrieval and display functionality. This includes downloading assets from Immich, optimizing image sizes, implementing slideshow integration, and ensuring smooth photo transitions within PhotoFrame's display system.

### Prerequisites
- ✅ Phase 1: Configuration system complete
- ✅ Phase 2A: Core Album Discovery complete
- 🔄 Phase 2B: Asset Retrieval (this phase)
- ⏳ Phase 2C: Error Handling & Polish (pending)

### Phase 2B Objectives

**Primary Goals:**
1. Download and cache photos from Immich albums
2. Optimize image sizes for PhotoFrame display
3. Integrate with PhotoFrame's slideshow system
4. Implement memory-efficient image management
5. Support various image formats and orientations
6. Handle network interruptions gracefully

## Technical Architecture

### Asset Retrieval Strategy

**Primary Immich API Endpoints (Phase 2B):**
1. `GET /api/assets/{id}/original` - Download original asset for display
2. `GET /api/assets/{id}` - Get asset metadata (dimensions, format)

**Download Management:**
```python
def downloadAsset(self, asset_id):
    """
    Download original asset from Immich for direct display
    """
    config = self.getImmichConfiguration()
    url = f"{config['server_url']}/api/assets/{asset_id}/original"
    
    headers = {'x-api-key': config['api_key']}
    return self.requestUrl(url, headers=headers, binary=True)
```

### Image Processing Integration

**Size Optimization:**
- Respect PhotoFrame's display dimensions
- Download thumbnails for previews, originals for display
- Handle high-resolution images efficiently
- Support portrait/landscape orientation detection

**Format Support:**
- JPEG (primary format)
- PNG with transparency
- WEBP for newer Immich instances
- HEIC/HEIF conversion if supported

### Memory Management

**Caching Strategy:**
- Cache downloaded images in service private directory
- Implement LRU (Least Recently Used) cleanup
- Respect PhotoFrame's memory constraints
- Clear cache based on age and usage

**File Naming Pattern:**
```
{service_private_dir}/images/{asset_id}.{extension}
{service_private_dir}/images/abc123.jpg
{service_private_dir}/images/def456.png
```

## Task Breakdown (Phase 2B: Tasks 9-15)

### Task 9: Asset Download Implementation
**Objective:** Core asset downloading from Immich
**Methods:** `downloadAsset()`, `getContentUrl()` enhancement
**Implementation:**
- Implement binary asset download from Immich (original quality only)
- Add progress tracking for large downloads
- Implement download retry logic
- Handle various image formats directly

**Success Criteria:**
- Assets download successfully from Immich
- Original quality images retrieved for display
- Download failures handled gracefully
- Progress tracking functional for large files

### Task 10: Image Cache Management
**Objective:** Efficient local caching of downloaded assets
**Methods:** `cacheAsset()`, `getCachedAsset()`, `cleanupCache()`
**Implementation:**
- Cache downloaded assets locally
- Implement cache size limits and cleanup
- Handle cache corruption detection
- Support cache preloading for next images

**Success Criteria:**
- Images cached efficiently on local storage
- Cache size managed within PhotoFrame limits
- Corrupted cache files detected and removed
- Cache hit rate optimized for performance

### Task 11: Size Optimization & Scaling
**Objective:** Optimize images for PhotoFrame display
**Methods:** `optimizeImageSize()`, `scaleForDisplay()`
**Implementation:**
- Scale images to fit PhotoFrame display dimensions
- Maintain aspect ratios correctly
- Handle portrait vs landscape orientation
- Optimize for memory usage vs quality

**Success Criteria:**
- Images scaled appropriately for display
- Aspect ratios maintained correctly
- Memory usage optimized
- Quality vs size balance achieved

### Task 12: Format Conversion Support
**Objective:** Handle various image formats from Immich
**Methods:** `convertImageFormat()`, `detectImageType()`
**Implementation:**
- Support JPEG, PNG, WEBP formats
- Convert unsupported formats to JPEG
- Handle transparency in PNG files
- Detect and handle corrupted image files

**Success Criteria:**
- Multiple image formats supported
- Format conversion working correctly
- Transparency handled appropriately
- Corrupted files detected and skipped

### Task 13: Slideshow Integration
**Objective:** Integrate with PhotoFrame's slideshow system
**Methods:** `selectImageFromAlbum()` full implementation
**Implementation:**
- Replace Phase 2A placeholder with real implementation
- Implement image selection algorithm
- Support randomization and sequential display
- Handle album switching smoothly

**Success Criteria:**
- `selectImageFromAlbum()` returns real images
- Image selection algorithm works correctly
- Slideshow transitions smooth
- Album switching functional

### Task 14: Network Resilience
**Objective:** Handle network interruptions during asset retrieval
**Methods:** `handleNetworkError()`, retry mechanisms
**Implementation:**
- Implement exponential backoff for failed downloads
- Cache partial downloads for resume capability
- Fallback to cached images during outages
- Provide user feedback for network issues

**Success Criteria:**
- Network failures handled gracefully
- Download resume functionality works
- Cached images used during outages
- User receives appropriate feedback

### Task 15: Performance Optimization
**Objective:** Optimize overall asset retrieval performance
**Methods:** Background downloading, prefetching
**Implementation:**
- Implement background asset prefetching
- Optimize database queries for asset metadata
- Implement progressive loading for large albums
- Add performance metrics collection

**Success Criteria:**
- Background prefetching functional
- Asset metadata queries optimized
- Large albums load progressively
- Performance metrics available

## API Integration Details

### Asset Download Requests
```python
# Original quality download (for direct display)
GET {server_url}/api/assets/{asset_id}/original
Headers: x-api-key: {api_key}

# Asset metadata
GET {server_url}/api/assets/{asset_id}
Headers: x-api-key: {api_key}
```

### Expected Asset Response
```json
{
  "id": "asset-uuid",
  "type": "IMAGE",
  "originalPath": "/path/to/original.jpg",
  "exifInfo": {
    "exifImageWidth": 4032,
    "exifImageHeight": 3024,
    "orientation": 1
  },
  "fileSize": 2458624,
  "mimeType": "image/jpeg"
}
```

## Data Flow Architecture

### Asset Retrieval Flow
1. **Album Selection** → Phase 2A provides album assets
2. **Asset Filtering** → Filter by supported formats and size
3. **Download Management** → Queue downloads with priority
4. **Cache Storage** → Store downloaded assets locally
5. **Size Optimization** → Scale for display requirements
6. **Slideshow Integration** → Provide images to PhotoFrame

### Caching Strategy
```python
def getCachedAssetPath(self, asset_id, extension='jpg'):
    """Generate cache file path for asset"""
    cache_dir = os.path.join(self.getStoragePath(), 'images')
    if not os.path.exists(cache_dir):
        os.makedirs(cache_dir)
    return os.path.join(cache_dir, f"{asset_id}.{extension}")
```

## Integration with PhotoFrame Systems

### BaseService Integration
- Override `selectImageFromAlbum()` with real implementation
- Use existing ImageHolder objects for consistency
- Integrate with BaseService memory tracking
- Follow established error handling patterns

### Memory Management Integration
- Use PhotoFrame's existing memory tracking
- Implement LRU cache cleanup
- Respect system memory constraints
- Monitor cache size and age

### Display System Integration
- Provide properly sized images to slideshow
- Handle orientation metadata correctly
- Support PhotoFrame's display modes
- Maintain smooth transitions

## Performance Considerations

### Download Optimization
- **Concurrent Downloads:** Limit concurrent downloads to avoid overwhelming Immich
- **Bandwidth Management:** Monitor and throttle download speed if needed
- **Prefetching Strategy:** Download next images in background
- **Cache Warming:** Pre-download popular albums

### Memory Management
- **Image Compression:** Balance quality vs memory usage
- **Cache Limits:** Implement size-based cache eviction
- **Garbage Collection:** Regular cleanup of unused assets
- **Memory Monitoring:** Track memory usage patterns

### Network Efficiency
- **Resume Downloads:** Support partial download resume
- **Compression:** Use Immich's built-in compression when available
- **Batch Requests:** Optimize API calls for efficiency
- **Error Recovery:** Implement robust retry mechanisms

## Risk Assessment

### LOW RISK
- Asset downloading and caching (standard HTTP operations)
- Size optimization using existing PhotoFrame utilities
- Cache management following established patterns

### MEDIUM RISK
- Integration with slideshow system (requires careful testing)
- Memory management optimization (potential for memory leaks)
- Network resilience implementation (complex error scenarios)

### HIGH RISK
- Performance optimization changes (potential for regressions)
- Format conversion implementation (potential for crashes)
- Concurrent download management (potential for race conditions)

## Implementation Timeline

**Week 1: Core Asset Download**
- Tasks 9-10: Asset download and cache management
- Deliverable: Basic asset retrieval functional

**Week 2: Image Processing**
- Tasks 11-12: Size optimization and format conversion
- Deliverable: Images properly formatted for display

**Week 3: Slideshow Integration**
- Tasks 13-14: Full slideshow integration and network resilience
- Deliverable: Complete photo display functionality

**Week 4: Performance Optimization**
- Task 15: Performance tuning and optimization
- Deliverable: Production-ready Phase 2B implementation

## Testing Strategy

### Unit Testing
- Asset download functionality
- Cache management operations
- Size optimization algorithms
- Format conversion routines

### Integration Testing
- Slideshow system integration
- Memory management integration
- Network failure scenarios
- Large album handling

### Performance Testing
- Download speed optimization
- Memory usage profiling
- Cache efficiency measurement
- Concurrent operation testing

## Success Criteria

**Phase 2B Complete When:**
1. ✅ Assets download successfully from Immich
2. ✅ Images cached and managed efficiently
3. ✅ Size optimization works for all display modes
4. ✅ Multiple image formats supported
5. ✅ Slideshow displays real Immich photos
6. ✅ Network interruptions handled gracefully
7. ✅ Performance meets PhotoFrame standards
8. ✅ No memory leaks or resource issues

## Development Guidelines

### CRITICAL CONSTRAINTS
- **DO NOT** modify PhotoFrame's core display system
- **DO NOT** change existing slideshow architecture
- **DO NOT** alter BaseService memory management
- **FOLLOW** established PhotoFrame image processing patterns
- **TEST** memory usage thoroughly to avoid leaks

### Performance Requirements
- Download speeds appropriate for PhotoFrame hardware
- Memory usage within Raspberry Pi constraints
- Cache size management to prevent storage issues
- Smooth slideshow transitions maintained

---

**Document Created:** Phase 2B Planning
**Dependencies:** Phase 2A completion required
**Status:** Ready for implementation after Phase 2A
**Next Phase:** Phase 2C (Error Handling & Polish)