# IMMICH ARCHITECTURE - CRITICAL REFERENCE

## FUNDAMENTAL PRINCIPLE: IMMICH-SPECIFIC ROUTES FOR EVERYTHING

**DO NOT MODIFY EXISTING ROUTES FOR IMMICH FUNCTIONALITY**

### Architecture Overview

This project implements Immich integration through **completely separate, dedicated routes** to avoid touching any existing photoframe functionality.

### Immich-Specific Components

1. **Service Implementation**: `services/svc_immich.py`
   - Implements BaseService for Immich photo service
   - Uses `needImmichConfig=True` instead of OAuth
   - Provides Immich-specific methods

2. **Immich Configuration Route**: `routes/immichconfigupload.py`
   - Handles `/service/<service>/immichconfig` endpoint
   - Uses `setImmichServiceConfiguration()` method
   - Validates Immich configs with `validateImmichServiceConfiguration()`
   - **NEVER uses existing config routes**

3. **ServiceManager Integration**:
   - `setImmichServiceConfiguration()` - Sets Immich configs
   - `validateImmichServiceConfiguration()` - Validates Immich configs
   - `getImmichServiceConfiguration()` - Gets Immich configs

### URL Structure

- **Traditional services**: `/service/<id>/config` (uses configupload.py)
- **Immich services**: `/service/<id>/immichconfig` (uses immichconfigupload.py)

### Key Rules

1. **NEVER modify existing routes** (service.py, configupload.py, etc.)
2. **ALWAYS use Immich-specific routes** for all Immich functionality
3. **SEPARATE URL endpoints** prevent conflicts with existing services
4. **Dedicated ServiceManager methods** keep Immich logic isolated

### Why This Architecture Exists

- **Zero risk** to existing Google Photos, SimpleURL, etc. services
- **Complete isolation** of Immich functionality
- **No domino effects** from touching existing error handling
- **Clean upgrade path** without breaking changes

### Testing Integration

- Phase 2a tests validate the Immich-specific routes work correctly
- Traditional service routes remain untouched and functional
- No cross-contamination between service types

## CRITICAL REMINDER FOR ALL AGENTS

**IF YOU FORGET THIS ARCHITECTURE, YOU WILL BREAK THE PROJECT**

The entire point of this implementation is to keep Immich functionality completely separate from existing photoframe routes and services.