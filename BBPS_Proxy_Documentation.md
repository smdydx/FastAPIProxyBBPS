
# BBPS Proxy System - Complete Documentation

## 📋 Table of Contents
1. [System Overview](#system-overview)
2. [Architecture Flow](#architecture-flow)
3. [Complete Request-Response Flow](#complete-request-response-flow)
4. [Route-by-Route Explanation](#route-by-route-explanation)
5. [Configuration Guide](#configuration-guide)
6. [API Usage Examples](#api-usage-examples)

---

## 1. System Overview

### Kya Hai Ye Project?

Ye ek **PROXY SERVER** hai jo CLIENT aur REAL BBPS BACKEND ke beech mein kaam karta hai:

```
CLIENT → YOUR PROXY (Port 5000) → REAL BBPS BACKEND
```

### Kyu Banaya?
- Real backend URLs ko **HIDE** karne ke liye
- Ek centralized point se saare requests handle karne ke liye
- Logging, monitoring, aur security add karne ke liye

---

## 2. Architecture Flow

```
┌──────────────────────────────────────────────────────────────┐
│                    CLIENT (Mobile/Web App)                    │
│  Request: POST /api/v1/mdm/fetch/single                      │
│  Body: {"biller_id": "TATA001"}                              │
└────────────────────────────┬─────────────────────────────────┘
                             │
                             │ HTTP POST Request
                             ▼
┌──────────────────────────────────────────────────────────────┐
│          YOUR PROXY SERVER (Port 5000)                        │
│                                                               │
│  Step 1: FastAPI receives request at /api/v1/mdm/fetch/single│
│  Step 2: Router routes to mdm.py endpoint                     │
│  Step 3: Endpoint calls forward_to_bbps() function            │
│  Step 4: ProxyForwarder reads bbps_urls.yaml                  │
│  Step 5: Constructs real URL & forwards request               │
│  Step 6: Waits for response from real backend                 │
│  Step 7: Normalizes response & sends back to client           │
│                                                               │
└────────────────────────────┬─────────────────────────────────┘
                             │
                             │ Forward to Real Backend
                             ▼
┌──────────────────────────────────────────────────────────────┐
│        REAL BBPS BACKEND (Hidden URL)                         │
│  URL: https://your-actual-lcrpay-backend.com/api/v1/mdm/...  │
│                                                               │
│  • Database Operations (PostgreSQL)                           │
│  • BBPS API Integration                                       │
│  • Business Logic                                             │
│  • Response Generation                                        │
│                                                               │
└────────────────────────────┬─────────────────────────────────┘
                             │
                             │ Response
                             ▼
                      CLIENT receives response
```

---

## 3. Complete Request-Response Flow (Step-by-Step)

### Example: MDM Single Biller Fetch

#### Step 1: Client Request Aata Hai
```http
POST http://localhost:5000/api/v1/mdm/fetch/single
Content-Type: application/json

{
    "biller_id": "TATA001"
}
```

#### Step 2: FastAPI Main App Request Receive Karta Hai
**File:** `app/main.py` (Line 89-92)

```python
# Middleware request log karta hai
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    # Logs: "Request: POST /api/v1/mdm/fetch/single"
```

#### Step 3: Router Request Ko Endpoint Tak Bhejta Hai
**File:** `app/api/v1/router.py` (Line 18)

```python
# Main router MDM router ko include karta hai
api_router.include_router(mdm.router, prefix="/mdm", tags=["MDM"])
```

**File:** `app/api/v1/endpoints/mdm.py` (Line 18-31)

```python
@router.post("/fetch/single", response_model=BBPSResponse)
async def fetch_single_biller_mdm(
    request: SingleBillerMDMRequest,  # Pydantic validates request
    store_in_db: bool = True
) -> BBPSResponse:
    # Step 3a: Request data ko dict mein convert karta hai
    payload = request.model_dump()
    payload["store_in_db"] = store_in_db
    
    # Step 3b: Proxy service ko call karta hai
    response_data, status_code = await forward_to_bbps(
        category="mdm",
        endpoint_key="fetch_single",
        method="POST",
        payload=payload
    )
    # Step 3c: Response normalize karke return
    return normalize_response(response_data, status_code)
```

#### Step 4: ProxyForwarder URL Construct Karta Hai
**File:** `app/services/proxy.py` (Line 26-50)

```python
async def forward_request(self, category: str, endpoint_key: str, ...):
    # Step 4a: bbps_urls.yaml se URL nikalta hai
    target_url = settings.get_full_url(category, endpoint_key, path_params)
    # Result: "https://your-actual-lcrpay-backend.com/api/v1/mdm/fetch/single"
    
    if not target_url:
        return {"success": False, "message": "No URL configured"}, 500
    
    # Step 4b: Request ID generate karta hai for tracking
    request_id = log_request(
        category=category,
        endpoint=endpoint_key,
        method=method,
        request_data=payload
    )
    # Result: request_id = "mdm_20250101120530123456"
```

#### Step 5: HTTP Request Real Backend Ko Bhejta Hai
**File:** `app/services/proxy.py` (Line 60-85)

```python
# Step 5a: Headers prepare karta hai
default_headers = {
    "Content-Type": "application/json",
    "X-Request-ID": request_id,
    "X-BBPS-Category": category,
    "X-Timestamp": datetime.utcnow().isoformat()
}

# Step 5b: Retry mechanism ke saath request bhejta hai
for attempt in range(self.max_retries):  # Default: 3 retries
    try:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                target_url,  # Real backend URL
                headers=default_headers,
                json=payload,  # {"biller_id": "TATA001", "store_in_db": true}
                params=query_params
            )
            
            # Step 5c: Response parse karta hai
            response_data = response.json()
            response_data["request_id"] = request_id
            response_data["timestamp"] = datetime.utcnow().isoformat()
            
            # Success/Failure set karta hai
            if response.status_code >= 200 and response.status_code < 300:
                response_data["success"] = True
            else:
                response_data["success"] = False
            
            return response_data, response.status_code
            
    except httpx.TimeoutException:
        # Timeout hua to retry karta hai
        await self._delay_retry(attempt)  # Exponential backoff
```

#### Step 6: Response Normalize Hota Hai
**File:** `app/api/deps.py` (Line 20-70)

```python
def normalize_response(response_data: Dict[str, Any], status_code: int):
    # Step 6a: Success determine karta hai
    success = response_data.get("success", status_code >= 200 and status_code < 300)
    
    # Step 6b: Message extract karta hai
    message = response_data.get("message", "Request processed successfully")
    
    # Step 6c: Data extract karta hai
    if "data" in response_data:
        data = response_data.get("data")
    else:
        # Exclude common keys aur baki sab data mein daal do
        excluded_keys = {"success", "message", "request_id", "timestamp", "errors"}
        data = {k: v for k, v in response_data.items() if k not in excluded_keys}
    
    # Step 6d: Errors handle karta hai
    errors = None
    if not success:
        errors = [{
            "code": response_data.get("error_code", "ERROR"),
            "message": response_data.get("details", "An error occurred")
        }]
    
    # Step 6e: Standardized BBPSResponse return karta hai
    return BBPSResponse(
        success=success,
        message=message,
        data=data,
        request_id=response_data.get("request_id"),
        timestamp=response_data.get("timestamp"),
        errors=errors
    )
```

#### Step 7: Client Ko Response Bheja Jata Hai
```json
{
    "success": true,
    "message": "Biller MDM fetched successfully",
    "data": {
        "biller_id": "TATA001",
        "biller_name": "Tata Power",
        "category": "Electricity",
        "input_params": [...]
    },
    "request_id": "mdm_20250101120530123456",
    "timestamp": "2025-01-01T12:05:30.500000",
    "errors": null
}
```

---

## 4. Route-by-Route Explanation

### 4.1 Health & Configuration Routes

#### GET `/health`
**File:** `app/api/v1/endpoints/health.py` (Line 10-17)

**Kya Karta Hai:**
- Basic health check endpoint
- Server status verify karta hai

**Flow:**
1. Client request bhejta hai → 2. FastAPI directly response return karta hai
3. Koi backend call nahi hoti

**Response:**
```json
{
    "status": "healthy",
    "service": "BBPS Proxy System",
    "version": "1.0.0",
    "timestamp": "2025-01-01T12:00:00"
}
```

#### GET `/categories`
**File:** `app/api/v1/endpoints/health.py` (Line 20-43)

**Kya Karta Hai:**
- bbps_urls.yaml se saare configured categories list karta hai
- Har category ke endpoints dikhata hai

**Flow:**
1. Client → 2. FastAPI → 3. Config file read → 4. Categories extract → 5. Response

---

### 4.2 MDM (Master Data Management) Routes

#### POST `/api/v1/mdm/fetch/single`
**Purpose:** Single biller ka MDM data fetch karna

**Request:**
```json
{
    "biller_id": "TATA001"
}
```

**Internal Flow:**
```
Client → mdm.py endpoint → forward_to_bbps() → 
ProxyForwarder → Real Backend (https://your-backend.com/api/v1/mdm/fetch/single) →
Response → normalize_response() → Client
```

**Real Backend Kya Karta Hai:**
- BBPS API se biller details fetch karta hai
- Database mein store karta hai (if store_in_db=true)
- Complete biller configuration return karta hai

#### POST `/api/v1/mdm/fetch/multiple`
**Purpose:** Multiple billers ka MDM data ek saath fetch karna

**Request:**
```json
{
    "biller_ids": ["TATA001", "BSNL001", "JIO001"]
}
```

#### GET `/api/v1/mdm/stats`
**Purpose:** MDM sync statistics dekhna

**Response:**
```json
{
    "total_billers": 1500,
    "synced_billers": 1200,
    "last_sync_time": "2025-01-01T10:00:00",
    "sync_status": "completed"
}
```

---

### 4.3 Bill Fetch Routes

#### GET `/api/v1/billfetch/input-params/{biller_id}`
**File:** `app/api/v1/endpoints/billfetch.py` (Line 14-23)

**Purpose:** Biller ke liye required input parameters fetch karna

**Example Request:**
```http
GET /api/v1/billfetch/input-params/TATA001
```

**Response:**
```json
{
    "success": true,
    "data": {
        "biller_id": "TATA001",
        "input_params": [
            {
                "name": "consumer_number",
                "label": "Consumer Number",
                "type": "text",
                "max_length": 12,
                "required": true
            }
        ]
    }
}
```

#### POST `/api/v1/billfetch/fetch`
**File:** `app/api/v1/endpoints/billfetch.py` (Line 26-36)

**Purpose:** Consumer ka bill fetch karna

**Request:**
```json
{
    "biller_id": "TATA001",
    "consumer_number": "123456789012",
    "input_params": {
        "consumer_number": "123456789012"
    }
}
```

**Internal Flow:**
1. Request validate hota hai (BillFetchRequest schema)
2. forward_to_bbps() call hota hai category="billfetch"
3. Real backend BBPS API se bill fetch karta hai
4. Response normalize hoke client ko jaata hai

---

### 4.4 Bill Payment Routes

#### POST `/api/v1/billpayment/pay`
**File:** `app/api/v1/endpoints/billpayment.py` (Line 14-24)

**Purpose:** Bill payment process karna

**Request:**
```json
{
    "biller_id": "TATA001",
    "consumer_number": "123456789012",
    "amount": 1500.00,
    "payment_mode": "UPI",
    "customer_info": {
        "mobile": "9876543210",
        "email": "customer@email.com"
    }
}
```

**Real Backend Actions:**
1. Transaction ID generate karta hai
2. BBPS API ko payment request bhejta hai
3. Database mein transaction record karta hai
4. Payment status track karta hai
5. Receipt generate karta hai

#### GET `/api/v1/billpayment/status/{transaction_id}`
**Purpose:** Payment ka status check karna

---

### 4.5 Authentication Routes

#### POST `/api/v1/auth/login`
**File:** `app/api/v1/endpoints/auth.py`

**Purpose:** OAuth2 token generate karna

**Request:**
```json
{
    "username": "client_id",
    "password": "client_secret"
}
```

**Response:**
```json
{
    "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "token_type": "bearer",
    "expires_in": 1800
}
```

---

## 5. Configuration Guide

### bbps_urls.yaml Structure

```yaml
bbps_backend_urls:
  mdm:
    base_url: "https://your-actual-backend.com/api/v1"
    fetch_single: "/mdm/fetch/single"
    fetch_multiple: "/mdm/fetch/multiple"
```

**Kaise Kaam Karta Hai:**

1. **settings.get_full_url()** function URL construct karta hai:
```python
# Input
category = "mdm"
endpoint_key = "fetch_single"

# Process
base_url = "https://your-actual-backend.com/api/v1"  # from yaml
endpoint = "/mdm/fetch/single"  # from yaml

# Output
full_url = "https://your-actual-backend.com/api/v1/mdm/fetch/single"
```

2. **Path Parameters** replace hote hain:
```python
endpoint = "/billers/{biller_id}"
path_params = {"biller_id": "TATA001"}
# Result: "/billers/TATA001"
```

---

## 6. API Usage Examples

### Example 1: Fetch Bill
```bash
curl -X POST "http://localhost:5000/api/v1/billfetch/fetch" \
  -H "Content-Type: application/json" \
  -d '{
    "biller_id": "TATA001",
    "consumer_number": "123456789012"
  }'
```

### Example 2: Pay Bill
```bash
curl -X POST "http://localhost:5000/api/v1/billpayment/pay" \
  -H "Content-Type: application/json" \
  -d '{
    "biller_id": "TATA001",
    "consumer_number": "123456789012",
    "amount": 1500.00,
    "payment_mode": "UPI"
  }'
```

### Example 3: Check Payment Status
```bash
curl -X GET "http://localhost:5000/api/v1/billpayment/status/TXN123456"
```

---

## 7. Key Components Summary

### Files Aur Unka Role

| File | Kya Karta Hai |
|------|---------------|
| `app/main.py` | FastAPI app initialize, middleware setup, global exception handling |
| `app/api/v1/router.py` | Saare routers ko combine karke main API router banata hai |
| `app/api/v1/endpoints/*.py` | Individual endpoints define karte hain |
| `app/services/proxy.py` | ProxyForwarder - Real backend ko requests forward karta hai |
| `app/core/config.py` | Settings aur URL configuration manage karta hai |
| `app/core/logging.py` | Request/Response logging handle karta hai |
| `app/data/bbps_urls.yaml` | Real backend URLs configuration |

---

## 8. Error Handling Flow

```
Request → Validation Error? → 422 Pydantic Error
       ↓
       No URL Found? → 500 Config Error
       ↓
       Backend Timeout? → Retry (3 attempts with exponential backoff)
       ↓
       Backend Error? → Forward error to client
       ↓
       Success → Normalize & return response
```

---

**Document Created:** 2025-12-01  
**Version:** 1.0.0  
**System:** BBPS Proxy System
