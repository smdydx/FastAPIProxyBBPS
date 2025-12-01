# BBPS Proxy System

## Overview
A production-ready FastAPI proxy system for Bharat Bill Payment System (BBPS) operations. This system provides comprehensive BBPS integration with OAuth2 authentication, async PostgreSQL database, Redis caching, and full API proxy capabilities.

## Project Architecture

```
app/
├── __init__.py                      # Application package
├── main.py                          # FastAPI application entry point with lifespan
├── core/
│   ├── __init__.py
│   ├── config.py                    # Application settings (DB, Cache, Auth, BBPS)
│   ├── logging.py                   # Logging utilities
│   ├── database.py                  # Async SQLAlchemy with PostgreSQL
│   ├── cache.py                     # Redis cache layer
│   ├── auth.py                      # OAuth2/JWT authentication
│   └── security.py                  # Password hashing, API keys, rate limiting
├── api/
│   ├── __init__.py
│   ├── deps.py                      # Common dependencies and utilities
│   └── v1/
│       ├── __init__.py
│       ├── router.py                # Main API router
│       └── endpoints/
│           ├── __init__.py
│           ├── health.py            # Health check and config endpoints
│           ├── monitoring.py        # Monitoring, metrics, and system stats
│           ├── auth.py              # Authentication (login, token, refresh)
│           ├── admin.py             # Admin dashboard, client management
│           ├── mdm.py               # MDM (Master Data Management) endpoints
│           ├── billfetch.py         # Bill fetch endpoints
│           ├── billpayment.py       # Bill payment endpoints
│           ├── billers.py           # Biller listing and search
│           ├── complaints.py        # Complaint registration and tracking
│           ├── banks.py             # Bank and IFSC lookup
│           ├── bbps.py              # Advanced BBPS operations
│           └── biller_management.py # Biller CRUD and CSV upload
├── models/
│   ├── __init__.py
│   └── optimized_models.py          # SQLAlchemy ORM models
├── schemas/
│   ├── __init__.py
│   ├── requests.py                  # Generic request models
│   ├── responses.py                 # Response models
│   └── bbps.py                      # BBPS-specific request models
├── services/
│   ├── __init__.py
│   ├── proxy.py                     # Reusable proxy forwarder with retry logic
│   └── bbps_api_service_async.py    # BBPS API service client
├── uploads/
│   └── csv/                         # CSV upload directory
└── data/
    └── bbps_urls.yaml               # BBPS backend URL mappings
```

## Database Models

- **Client**: API clients with OAuth2 credentials
- **APIKey**: API key management for clients
- **Biller**: Biller master data
- **BillerMDM**: Biller MDM records
- **BillerInputParam**: Biller input parameters
- **Bank**: Bank master data
- **BankIFSC**: IFSC codes
- **Transaction**: Payment transactions
- **BillFetchRecord**: Bill fetch history
- **Complaint**: Customer complaints
- **AuditLog**: Audit trail
- **CSVUpload**: CSV upload tracking

## API Endpoints

### Authentication (`/api/v1/auth`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/token` | OAuth2 login (get access token) |
| POST | `/refresh` | Refresh access token |
| GET | `/me` | Get current client profile |
| PUT | `/me` | Update client profile |
| POST | `/change-password` | Change password |
| POST | `/logout` | Logout |
| GET | `/verify` | Verify authentication |

### Admin (`/api/v1/admin`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/dashboard` | Admin dashboard stats |
| GET | `/clients` | List all clients |
| POST | `/clients` | Create new client |
| PUT | `/clients/{client_id}` | Update client |
| POST | `/clients/{client_id}/api-keys` | Create API key |
| GET | `/transactions` | List all transactions |
| GET | `/audit-logs` | List audit logs |
| GET | `/csv-uploads` | List CSV uploads |

### Health & Configuration (`/api/v1`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Basic health check |
| GET | `/categories` | List available BBPS categories |
| POST | `/config/reload` | Reload configuration |

### Monitoring (`/api/v1/monitoring`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Backend health check |
| GET | `/health/detailed` | Detailed health with DB/Cache status |
| GET | `/health/ready` | Kubernetes readiness probe |
| GET | `/health/live` | Kubernetes liveness probe |
| GET | `/metrics` | Prometheus metrics |
| GET | `/stats/system` | System stats (CPU, Memory, Disk) |
| GET | `/stats/application` | Application stats (DB counts) |
| GET | `/stats/cache` | Redis cache statistics |

### BBPS Operations (`/api/v1/bbps`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/bill/fetch` | Fetch bill with DB logging |
| POST | `/bill/pay` | Pay bill with transaction record |
| GET | `/transaction/{id}` | Get transaction status |
| GET | `/transactions` | List transactions |
| POST | `/validate/consumer` | Validate consumer |
| GET | `/plans/{biller_id}` | Get biller plans |
| POST | `/recharge` | Process recharge |
| POST | `/complaints/register` | Register complaint |
| GET | `/complaints/{id}` | Get complaint status |
| GET | `/complaints` | List complaints |

### MDM - Master Data Management (`/api/v1/mdm`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/fetch/single` | Fetch MDM for single biller |
| POST | `/fetch/multiple` | Fetch MDM for multiple billers |
| POST | `/fetch/by-category` | Fetch MDM by category |
| GET | `/{biller_id}` | Get cached MDM for biller |
| GET | `/category/{category}` | Get MDM by category |
| POST | `/search` | Search MDM records |
| GET | `/stats` | Get MDM statistics |
| GET | `/sync/status` | Get sync status |
| POST | `/sync/start` | Start full MDM sync |
| POST | `/sync/category` | Sync specific category |
| GET | `/export/{category}` | Export category MDM |

### Bill Fetch (`/api/v1/billfetch`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/input-params/{biller_id}` | Get biller input parameters |
| POST | `/fetch` | Fetch bill from BBPS |
| POST | `/validate-params` | Validate input parameters |
| GET | `/history` | Get bill fetch history |
| GET | `/history/{fetch_id}` | Get specific fetch record |

### Bill Payment (`/api/v1/billpayment`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/pay` | Pay bill through BBPS |
| GET | `/status/{transaction_id}` | Get payment status |
| GET | `/history` | Get payment history |
| POST | `/refund` | Request refund |

### Biller Management (`/api/v1/management`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/billers` | Create biller |
| PUT | `/billers/{biller_id}` | Update biller |
| DELETE | `/billers/{biller_id}` | Deactivate biller |
| POST | `/billers/{biller_id}/input-params` | Add input param |
| GET | `/billers/{biller_id}/input-params` | Get input params |
| DELETE | `/billers/{id}/input-params/{param_id}` | Delete input param |
| POST | `/upload/billers` | Upload billers CSV |
| GET | `/upload/{upload_id}` | Get upload status |
| GET | `/stats` | Get biller statistics |

### Billers (`/api/v1/billers`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | List all billers |
| GET | `/categories` | Get biller categories |
| GET | `/category/{category}` | Get billers by category |
| GET | `/search` | Search billers |
| GET | `/{biller_id}` | Get biller by ID |

### Complaints (`/api/v1/complaints`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/register` | Register complaint |
| GET | `/status/{complaint_id}` | Get complaint status |
| GET | `/` | List complaints |
| PUT | `/{complaint_id}` | Update complaint |

### Banks (`/api/v1/banks`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | List all banks |
| GET | `/{bank_id}` | Get bank by ID |
| GET | `/{bank_id}/ifsc` | Get bank IFSC codes |
| GET | `/ifsc/search` | Search IFSC codes |

## Configuration

### Environment Variables

#### Core Settings
- `DEBUG` - Enable debug mode (default: false)
- `HOST` - Server host (default: 0.0.0.0)
- `PORT` - Server port (default: 5000)
- `LOG_LEVEL` - Logging level (default: INFO)

#### Database
- `DATABASE_URL` - PostgreSQL connection string
- `DATABASE_POOL_SIZE` - Connection pool size (default: 10)
- `DATABASE_MAX_OVERFLOW` - Max overflow connections (default: 20)
- `DATABASE_POOL_TIMEOUT` - Pool timeout seconds (default: 30)
- `DATABASE_ECHO` - Echo SQL queries (default: false)

#### Redis Cache
- `REDIS_URL` - Redis connection string
- `REDIS_PASSWORD` - Redis password
- `CACHE_TTL` - Default cache TTL seconds (default: 300)
- `CACHE_PREFIX` - Cache key prefix (default: bbps:)

#### Authentication
- `SECRET_KEY` - JWT secret key (change in production!)
- `ALGORITHM` - JWT algorithm (default: HS256)
- `ACCESS_TOKEN_EXPIRE_MINUTES` - Token expiry (default: 30)
- `REFRESH_TOKEN_EXPIRE_DAYS` - Refresh token expiry (default: 7)

#### BBPS API
- `BBPS_API_BASE_URL` - BBPS API base URL
- `BBPS_API_KEY` - BBPS API key
- `BBPS_API_SECRET` - BBPS API secret
- `BBPS_OU_ID` - BBPS OU ID
- `BBPS_AGENT_ID` - BBPS Agent ID

#### Rate Limiting
- `RATE_LIMIT_REQUESTS` - Max requests per period (default: 100)
- `RATE_LIMIT_PERIOD` - Rate limit period seconds (default: 60)

#### Proxy Settings
- `REQUEST_TIMEOUT` - Request timeout seconds (default: 30)
- `MAX_RETRIES` - Maximum retry attempts (default: 3)
- `RETRY_DELAY` - Delay between retries seconds (default: 1.0)

### Changing BBPS Backend URLs

1. **Via YAML Config**: Edit `app/data/bbps_urls.yaml`
2. **Via Environment Variables**: Set `BBPS_{CATEGORY}_BASE_URL`

## Running the Application

```bash
uvicorn app.main:app --host 0.0.0.0 --port 5000 --reload
```

## API Documentation
- Swagger UI: http://localhost:5000/docs
- ReDoc: http://localhost:5000/redoc

## Authentication Flow

1. **OAuth2 Token Flow**:
   ```bash
   curl -X POST "/api/v1/auth/token" \
     -d "username=client_id&password=client_secret"
   ```

2. **API Key Authentication**:
   ```bash
   curl -H "X-API-Key: bbps_your_api_key" "/api/v1/billers"
   ```

## Recent Changes
- **2025-12-01**: Major update - Full BBPS implementation
  - Added async PostgreSQL database with SQLAlchemy
  - Added Redis caching layer
  - Added OAuth2/JWT authentication
  - Added Admin endpoints (dashboard, client management)
  - Added BBPS operations (transactions, complaints, validation)
  - Added Biller management with CSV upload
  - Added comprehensive database models
  - Added rate limiting and security utilities
  - Updated all endpoints with async database support
- **2025-12-01**: Restructured to proper FastAPI folder convention
  - Created `app/` directory with core, api, schemas, services modules
  - Organized endpoints under `app/api/v1/endpoints/`
  - Moved schemas to `app/schemas/`
  - Moved services to `app/services/`
  - Updated configuration to `app/core/config.py`
- Config-based URL mapping system
- Comprehensive logging and error handling
- Response normalization with BBPSResponse schema
