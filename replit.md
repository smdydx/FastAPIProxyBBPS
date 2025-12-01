# BBPS Proxy System

## Overview

A production-ready FastAPI proxy server that acts as an intermediary between client applications and Bharat Bill Payment System (BBPS) backend services. The system provides centralized request routing, OAuth2 authentication, PostgreSQL database operations, Redis caching, and comprehensive API management for all BBPS operations including bill payments, complaints, biller management, and MDM (Master Data Management).

**Core Purpose**: Securely forward client requests to BBPS backend endpoints while hiding backend URLs, providing authentication, caching, logging, and database persistence.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### 1. Proxy-Based Request Routing

**Problem**: Need to route client requests to multiple BBPS backend endpoints without exposing backend URLs, while providing centralized monitoring and control.

**Solution**: Implemented a proxy architecture where all client requests flow through a FastAPI server that reads backend URLs from YAML configuration and forwards requests with retry logic.

**Flow Pattern**:
```
Client → FastAPI Proxy (Port 5000) → BBPS Backend Services
```

**Key Components**:
- **ProxyForwarder** (`app/services/proxy.py`): Reusable service that constructs target URLs from YAML config, forwards HTTP requests with configurable timeout and retry logic
- **Category-based routing**: Requests organized by BBPS categories (MDM, bill fetch, bill payment, complaints, banks, billers, monitoring)
- **Dynamic URL construction**: Supports path parameters, query parameters, and custom headers
- **Request/Response normalization**: Standardized response format via `BBPSResponse` schema

**Rationale**: Centralizes all BBPS communication, making it easy to update backend URLs, add monitoring, and implement security controls without changing client code.

**Pros**: Single point of control, easy configuration updates, consistent logging
**Cons**: Additional network hop adds latency, proxy becomes single point of failure

### 2. Authentication & Authorization

**Problem**: Need to secure API access, track which clients are making requests, and provide different permission levels.

**Solution**: OAuth2 + JWT token-based authentication with scope-based authorization and optional API key authentication.

**Implementation**:
- **OAuth2 password flow** for token generation (`/api/v1/auth/token`)
- **JWT tokens** with configurable expiration (access: 30 min, refresh: 7 days)
- **Scope-based permissions** for admin vs regular client access
- **API Key authentication** as alternative to OAuth2 tokens
- **Password hashing** using bcrypt via passlib
- **Token refresh** mechanism for long-lived sessions

**Key Files**:
- `app/core/auth.py`: JWT creation, verification, OAuth2 scheme
- `app/core/security.py`: Password hashing, API key generation, signature verification
- `app/api/v1/endpoints/auth.py`: Login, token refresh, password change endpoints

**Alternatives Considered**: Simple API key authentication was considered but OAuth2 provides better token lifecycle management.

**Pros**: Standard OAuth2 flow, token refresh capability, fine-grained access control
**Cons**: More complex than simple API keys, requires token management on client side

### 3. Database Architecture

**Problem**: Need to persist client data, transactions, billers, complaints, and audit logs while supporting async operations.

**Solution**: Async PostgreSQL with SQLAlchemy ORM using asyncpg driver.

**Implementation**:
- **Async SQLAlchemy engine** with connection pooling
- **Session management** via dependency injection (`get_db`)
- **ORM models** for all entities (Client, Biller, Transaction, Complaint, etc.)
- **Connection pool** with configurable size, max overflow, and timeout
- **Database initialization** during application startup via lifespan context manager

**Key Models** (`app/models/optimized_models.py`):
- **Client**: API clients with credentials and scopes
- **Biller**: Biller master data with MDM information
- **Transaction**: Bill payment transactions with status tracking
- **BillFetchRecord**: Bill fetch history
- **Complaint**: Complaint registration and tracking
- **AuditLog**: System activity logging
- **APIKey**: API key management

**Database URL**: Supports PostgreSQL with automatic conversion to asyncpg driver (`postgresql+asyncpg://`)

**Rationale**: Async operations prevent blocking during database I/O, connection pooling optimizes resource usage.

**Pros**: High concurrency, non-blocking I/O, efficient resource usage
**Cons**: More complex than sync database operations, requires async/await everywhere

### 4. Caching Layer

**Problem**: Reduce load on BBPS backend and improve response times for frequently accessed data.

**Solution**: Redis-based caching with async operations and configurable TTL.

**Implementation**:
- **Redis async client** using redis-asyncio library
- **Connection pooling** for Redis connections
- **CacheService** class with get/set/delete/exists operations
- **Configurable TTL** via environment variables (default: 300 seconds)
- **Key prefixing** to avoid collisions (`bbps:`)
- **Graceful degradation**: System works without Redis if not configured

**Key Features**:
- JSON serialization for complex objects
- Automatic expiration via TTL
- Connection pooling for efficiency
- Async operations for non-blocking I/O

**Rationale**: Caching reduces backend load and improves response times for frequently requested data like biller MDM.

**Pros**: Reduced backend load, faster response times, lower latency
**Cons**: Cache invalidation complexity, additional infrastructure dependency

### 5. Configuration Management

**Problem**: Need flexible configuration for multiple environments without code changes.

**Solution**: Environment variables with YAML configuration for BBPS backend URLs.

**Implementation**:
- **Settings class** (`app/core/config.py`) loads from environment variables
- **YAML configuration** for BBPS backend URLs (`bbps_urls.yaml`)
- **Dynamic URL construction** with path parameters and query strings
- **Configuration reload** endpoint for runtime updates

**Key Settings Categories**:
- **Application**: Name, version, debug mode
- **Server**: Host, port
- **Database**: Connection URL, pool settings
- **Redis**: Connection URL, cache TTL
- **Auth**: Secret key, token expiration
- **BBPS**: API keys, timeouts, retry logic

**Rationale**: Separates configuration from code, enables environment-specific settings, supports runtime reconfiguration.

### 6. Request/Response Lifecycle

**Problem**: Need consistent logging, error handling, and response formatting across all endpoints.

**Solution**: Centralized logging utilities and response normalization.

**Implementation**:
- **Request logging**: Captures category, endpoint, method, payload, headers
- **Response logging**: Records status, duration, response data
- **Error logging**: Captures exceptions with stack traces
- **Response normalization**: Standardizes all responses to `BBPSResponse` format
- **Request ID tracking**: Unique ID for each request for tracing

**Key Components**:
- `app/core/logging.py`: Logging utilities and BBPSLogger class
- `app/api/deps.py`: Response normalization and dependency injection
- `app/schemas/responses.py`: Standardized response models

**Rationale**: Consistent logging and response format simplifies debugging and client integration.

### 7. API Route Organization

**Problem**: Need to organize multiple BBPS categories and operations in a maintainable structure.

**Solution**: Category-based routing with dedicated endpoint modules.

**Route Categories**:
- **Health & Config**: System health, configuration management
- **Authentication**: Login, token refresh, password management
- **Admin**: Client management, dashboard, audit logs
- **Monitoring**: Health checks, metrics, system stats
- **MDM**: Master data management for billers
- **Bill Fetch**: Fetch bills, validate parameters
- **Bill Payment**: Process payments, check status
- **Billers**: List, search, categorize billers
- **Complaints**: Register, track complaints
- **Banks**: Bank and IFSC lookup
- **BBPS Operations**: Advanced BBPS features
- **Biller Management**: CRUD operations, CSV upload

**Rationale**: Modular structure improves maintainability, makes it easy to add new categories.

## External Dependencies

### Third-Party Services

1. **BBPS Backend Services**: Real BBPS API endpoints configured via `bbps_urls.yaml`
   - Purpose: Actual bill payment processing, biller data, complaints
   - Integration: HTTP requests via httpx with retry logic
   - Configuration: Base URLs and endpoint paths in YAML

### Databases

1. **PostgreSQL**: Primary data store
   - Purpose: Persist clients, billers, transactions, complaints, audit logs
   - Driver: asyncpg (async PostgreSQL driver)
   - Connection: Via SQLAlchemy async engine
   - URL format: `postgresql+asyncpg://user:pass@host:port/dbname`

2. **Redis**: Caching layer
   - Purpose: Cache frequently accessed data (biller MDM, etc.)
   - Driver: redis-asyncio
   - Connection: Connection pool with configurable size
   - Optional: System degrades gracefully if Redis unavailable

### Python Libraries

**Web Framework**:
- `fastapi`: Modern async web framework
- `uvicorn`: ASGI server for running FastAPI
- `pydantic`: Data validation and serialization

**HTTP Client**:
- `httpx`: Async HTTP client for forwarding requests to BBPS backend

**Database**:
- `sqlalchemy`: ORM and database toolkit (async mode)
- `asyncpg`: PostgreSQL async driver

**Caching**:
- `redis`: Async Redis client library

**Authentication**:
- `python-jose`: JWT token creation and verification
- `passlib`: Password hashing with bcrypt
- `bcrypt`: Password hashing algorithm

**Configuration**:
- `python-dotenv`: Environment variable loading
- `pyyaml`: YAML configuration file parsing

**File Handling**:
- `python-multipart`: Multipart form data parsing for file uploads
- `aiofiles`: Async file I/O operations

### API Integration Patterns

1. **Request Forwarding**: All BBPS requests forwarded via ProxyForwarder with retry logic
2. **Response Normalization**: All responses converted to standardized `BBPSResponse` format
3. **Error Handling**: Connection errors, timeouts, and backend errors handled gracefully
4. **Retry Logic**: Configurable retries with exponential backoff for failed requests
5. **Timeout Management**: Configurable timeout for all backend requests (default: 30s)