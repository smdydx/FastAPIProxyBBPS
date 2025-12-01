# BBPS Proxy System

## Overview

A production-ready FastAPI proxy server for Bharat Bill Payment System (BBPS) operations. This system acts as an intermediary between client applications and BBPS backend services, providing a centralized point for request handling, authentication, caching, and monitoring. The proxy architecture enables hiding real backend URLs, implementing security layers, and adding comprehensive logging and monitoring capabilities.

**Core Purpose**: Forward client requests to BBPS backend services while providing OAuth2 authentication, Redis caching, PostgreSQL database operations, and complete request/response lifecycle management.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### 1. Request Flow Architecture

**Problem**: Need to securely route client requests to multiple BBPS backend endpoints without exposing backend URLs.

**Solution**: Implemented a proxy-based architecture where all client requests flow through a centralized FastAPI server that forwards requests to configured backend URLs.

**Flow Pattern**:
```
Client → FastAPI Proxy (Port 5000) → BBPS Backend Services
```

**Key Components**:
- **ProxyForwarder** (`app/services/proxy.py`): Reusable service that reads YAML configuration, constructs target URLs, and forwards requests with retry logic
- **Category-based routing**: Requests are organized by BBPS categories (MDM, bill fetch, bill payment, complaints, banks, billers)
- **Dynamic URL construction**: URLs built from YAML config with support for path parameters, query parameters, and custom headers

**Rationale**: This approach centralizes all BBPS communication, making it easier to update backend URLs, add monitoring, and implement security controls without changing client code.

### 2. Authentication & Authorization

**Problem**: Need to secure API access and track which clients are making requests.

**Solution**: OAuth2 + JWT token-based authentication with scope-based authorization.

**Implementation**:
- **OAuth2 password flow** for token generation (`app/core/auth.py`)
- **JWT tokens** with configurable expiration (access tokens: 30 min, refresh tokens: 7 days)
- **Scope-based permissions** for admin vs regular client access
- **API Key authentication** as alternative to OAuth2 tokens
- **Password hashing** using bcrypt via passlib

**Alternatives Considered**: Simple API key authentication was considered but OAuth2 provides better token lifecycle management and scope control.

**Pros**: Standard OAuth2 flow, token refresh capability, fine-grained access control
**Cons**: More complex than simple API keys, requires token management on client side

### 3. Data Persistence Layer

**Problem**: Need to store client information, transactions, billers, and audit logs.

**Solution**: Async PostgreSQL with SQLAlchemy ORM and connection pooling.

**Architecture**:
- **Async SQLAlchemy** (`sqlalchemy.ext.asyncio`) for non-blocking database operations
- **Connection pooling** (pool_size: 10, max_overflow: 20) for efficient resource usage
- **Asyncpg driver** for high-performance PostgreSQL async operations
- **Automatic connection cleanup** via lifespan context manager

**Database Models** (`app/models/optimized_models.py`):
- **Client**: OAuth2 clients with credentials and scopes
- **Biller/BillerMDM**: Master data for BBPS billers
- **Transaction**: Payment transaction records
- **BillFetchRecord**: Bill fetch history
- **Complaint**: Complaint tracking
- **AuditLog**: Activity logging
- **APIKey**: API key management

**Design Decision**: Used async operations throughout to prevent blocking I/O during database queries, enabling the server to handle concurrent requests efficiently.

### 4. Caching Strategy

**Problem**: Reduce latency and backend load for frequently accessed data like biller MDM.

**Solution**: Redis-based caching layer with TTL-based expiration.

**Implementation** (`app/core/cache.py`):
- **Redis async client** with connection pooling
- **Configurable TTL** (default 300 seconds)
- **Namespace prefixing** to organize cache keys
- **JSON serialization** for complex objects
- **Graceful degradation** when Redis is unavailable

**Cache Usage Pattern**:
```python
# Try cache first
cached = await cache.get(key)
if cached:
    return cached

# Fetch from backend/DB
data = await fetch_data()

# Store in cache
await cache.set(key, data, ttl=300)
```

**Rationale**: Biller MDM data changes infrequently, making it ideal for caching. Redis provides fast in-memory storage with automatic expiration.

### 5. Configuration Management

**Problem**: Need to manage multiple backend URLs, credentials, and environment-specific settings.

**Solution**: Environment variables + YAML configuration files.

**Architecture** (`app/core/config.py`):
- **Environment variables** via python-dotenv for sensitive data (secrets, DB URLs)
- **YAML files** for BBPS backend URL mappings
- **Settings class** as single source of truth for all configuration
- **URL builder methods** for constructing full URLs with path/query parameters

**Configuration Hierarchy**:
1. Environment variables (.env file)
2. YAML configuration (bbps_urls.yaml)
3. Default values in Settings class

**Rationale**: Separating sensitive credentials (env vars) from structural config (YAML) provides better security while maintaining flexibility.

### 6. Error Handling & Logging

**Problem**: Need comprehensive logging for debugging and monitoring without exposing sensitive data.

**Solution**: Structured logging with request/response tracking and error normalization.

**Implementation** (`app/core/logging.py`):
- **BBPSLogger** wrapper around Python logging
- **Request ID tracking** for correlating logs across the request lifecycle
- **Structured log format** with timestamps, log levels, and contextual data
- **Error sanitization** to prevent sensitive data leakage

**Response Normalization** (`app/api/deps.py`):
- Standardized response format across all endpoints
- Automatic error extraction from backend responses
- Success/failure determination based on status codes

### 7. Retry & Resilience

**Problem**: Handle transient failures when communicating with BBPS backends.

**Solution**: Configurable retry logic with exponential backoff.

**Implementation** (`app/services/proxy.py`):
- **Max retries**: 3 attempts (configurable)
- **Retry delay**: 1 second base delay (configurable)
- **Timeout handling**: 30-second request timeout
- **Connection error handling**: Graceful failure with error codes

**Rationale**: Network issues and temporary backend unavailability are common in distributed systems. Retry logic improves reliability without requiring client-side changes.

### 8. API Organization

**Problem**: Managing many BBPS endpoints in a maintainable structure.

**Solution**: Modular router architecture with category-based endpoint grouping.

**Structure**:
```
app/api/v1/endpoints/
├── auth.py          # Authentication (login, token, refresh)
├── admin.py         # Admin operations (client management, dashboard)
├── mdm.py           # Master Data Management endpoints
├── billfetch.py     # Bill fetch operations
├── billpayment.py   # Bill payment operations
├── billers.py       # Biller listing and search
├── complaints.py    # Complaint registration and tracking
├── banks.py         # Bank and IFSC lookup
└── monitoring.py    # Health checks and metrics
```

**Router Registration** (`app/api/v1/router.py`):
All endpoint modules registered with consistent prefixes and tags for OpenAPI documentation.

**Rationale**: Separation by business domain makes the codebase easier to navigate and allows independent development of different BBPS features.

### 9. Application Lifecycle Management

**Problem**: Properly initialize and cleanup resources (database, Redis) during startup and shutdown.

**Solution**: FastAPI lifespan context manager.

**Implementation** (`app/main.py`):
```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await init_db()
    
    yield
    
    # Shutdown
    await close_db()
    await close_redis()
```

**Rationale**: Ensures clean resource management, preventing connection leaks and ensuring graceful shutdown.

## External Dependencies

### Required Services

1. **PostgreSQL Database**
   - **Purpose**: Persistent storage for clients, transactions, billers, and audit logs
   - **Connection**: Async via asyncpg driver
   - **Configuration**: DATABASE_URL environment variable
   - **Optional**: System works without database but with limited functionality

2. **Redis Cache**
   - **Purpose**: High-speed caching for biller MDM and frequently accessed data
   - **Connection**: Async Redis client with connection pooling
   - **Configuration**: REDIS_URL and REDIS_PASSWORD environment variables
   - **Optional**: System gracefully degrades without Redis

3. **BBPS Backend Services**
   - **Purpose**: Actual BBPS API endpoints for bill operations
   - **Configuration**: YAML-based URL mapping in configuration
   - **Categories**: MDM, bill fetch, bill payment, complaints, banks, billers, monitoring
   - **Authentication**: API key/secret (BBPS_API_KEY, BBPS_API_SECRET)

### Third-Party Python Libraries

**Core Framework**:
- **FastAPI** (>=0.122.0): Web framework with async support and OpenAPI documentation
- **Uvicorn** (>=0.38.0): ASGI server for running FastAPI

**HTTP Client**:
- **httpx** (>=0.28.1): Async HTTP client for forwarding requests to BBPS backends

**Data Validation**:
- **Pydantic** (>=2.12.5): Request/response validation and serialization

**Database**:
- **SQLAlchemy**: Async ORM for database operations
- **asyncpg**: PostgreSQL async driver

**Caching**:
- **redis**: Async Redis client

**Authentication & Security**:
- **python-jose**: JWT token creation and validation
- **passlib**: Password hashing (bcrypt)
- **bcrypt**: Secure password hashing algorithm

**Configuration**:
- **python-dotenv** (>=1.2.1): Environment variable loading
- **PyYAML** (>=6.0.3): YAML configuration file parsing

**File Handling**:
- **python-multipart**: Form data and file upload support
- **aiofiles**: Async file operations

### Environment Variables Required

**Core Application**:
- `PORT`: Server port (default: 5000)
- `HOST`: Server host (default: 0.0.0.0)
- `DEBUG`: Enable debug mode (default: false)
- `LOG_LEVEL`: Logging level (default: INFO)

**Database**:
- `DATABASE_URL`: PostgreSQL connection string (optional)
- `DATABASE_POOL_SIZE`: Connection pool size (default: 10)
- `DATABASE_MAX_OVERFLOW`: Max overflow connections (default: 20)

**Redis**:
- `REDIS_URL`: Redis connection string (default: redis://localhost:6379/0)
- `REDIS_PASSWORD`: Redis password (optional)
- `CACHE_TTL`: Cache expiration in seconds (default: 300)

**Authentication**:
- `SECRET_KEY`: JWT signing secret (required)
- `ACCESS_TOKEN_EXPIRE_MINUTES`: Access token lifetime (default: 30)
- `REFRESH_TOKEN_EXPIRE_DAYS`: Refresh token lifetime (default: 7)

**BBPS Backend**:
- `BBPS_API_BASE_URL`: Base URL for BBPS backend
- `BBPS_API_KEY`: API key for BBPS authentication
- `BBPS_API_SECRET`: API secret for BBPS authentication

**Request Configuration**:
- `REQUEST_TIMEOUT`: HTTP timeout in seconds (default: 30)
- `MAX_RETRIES`: Maximum retry attempts (default: 3)
- `RETRY_DELAY`: Delay between retries in seconds (default: 1.0)