# BBPS Proxy System

## Overview
A production-ready FastAPI proxy system for Bharat Bill Payment System (BBPS) operations. This system acts as a middleware proxy that forwards requests to actual BBPS backend services while hiding the real URLs from clients.

## Project Architecture

```
app/
├── __init__.py                      # Application package
├── main.py                          # FastAPI application entry point
├── core/
│   ├── __init__.py
│   ├── config.py                    # Application settings and configuration
│   └── logging.py                   # Logging utilities
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
│           ├── mdm.py               # MDM (Master Data Management) endpoints
│           ├── billfetch.py         # Bill fetch endpoints
│           ├── billpayment.py       # Bill payment endpoints
│           ├── billers.py           # Biller listing and search
│           ├── complaints.py        # Complaint registration and tracking
│           └── banks.py             # Bank and IFSC lookup
├── schemas/
│   ├── __init__.py
│   ├── requests.py                  # Generic request models
│   ├── responses.py                 # Response models
│   └── bbps.py                      # BBPS-specific request models
├── services/
│   ├── __init__.py
│   └── proxy.py                     # Reusable proxy forwarder with retry logic
└── data/
    └── bbps_urls.yaml               # BBPS backend URL mappings
```

## API Endpoints

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

### Changing BBPS Backend URLs

1. **Via YAML Config**: Edit `app/data/bbps_urls.yaml`
2. **Via Environment Variables**: Set `BBPS_{CATEGORY}_BASE_URL`

Example environment variables:
- `BBPS_MONITORING_BASE_URL`
- `BBPS_MDM_BASE_URL`
- `BBPS_BILLFETCH_BASE_URL`
- `BBPS_BILLPAYMENT_BASE_URL`

### Environment Variables
- `DEBUG` - Enable debug mode (default: false)
- `HOST` - Server host (default: 0.0.0.0)
- `PORT` - Server port (default: 5000)
- `LOG_LEVEL` - Logging level (default: INFO)
- `REQUEST_TIMEOUT` - Request timeout in seconds (default: 30)
- `MAX_RETRIES` - Maximum retry attempts (default: 3)
- `RETRY_DELAY` - Delay between retries in seconds (default: 1.0)

## Running the Application

```bash
uvicorn app.main:app --host 0.0.0.0 --port 5000 --reload
```

## API Documentation
- Swagger UI: http://localhost:5000/docs
- ReDoc: http://localhost:5000/redoc

## Recent Changes
- **2025-12-01**: Restructured to proper FastAPI folder convention
  - Created `app/` directory with core, api, schemas, services modules
  - Organized endpoints under `app/api/v1/endpoints/`
  - Moved schemas to `app/schemas/`
  - Moved services to `app/services/`
  - Updated configuration to `app/core/config.py`
- Config-based URL mapping system
- Comprehensive logging and error handling
- Response normalization with BBPSResponse schema
