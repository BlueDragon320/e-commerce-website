# B2B Engine REST API Reference — Client Developer Specification

> Complete technical reference for e-commerce developers consuming the **Weighted Ranking Engine REST API (v1)**.  
> This specification covers authentication/tenant identification, endpoints, request parameters, JSON schemas, dynamic weight tuning, and error responses.

---

## 🔐 Tenant Identification & Authentication

The Weighted Ranking Engine is a multi-tenant B2B service. Every API request must identify the tenant company. The engine accepts tenant identification through three mechanisms (in order of precedence):

1. **HTTP Request Header**:
   ```http
   X-Company-ID: 1
   ```
2. **Query String Parameter**:
   ```http
   GET /api/v1/search?company_id=1&q=earbuds
   ```
3. **JSON Request Body**:
   ```json
   {
     "company_id": 1,
     "q": "earbuds"
   }
   ```

> **Base URL**: `http://localhost:5000` (Production: `https://engine.yourdomain.com`)  
> **API Version**: `v1`  
> **Response Format**: `application/json; charset=utf-8`

---

## 📡 Endpoints Specification

### 1. Multi-Criteria Product Search & Ranking

Executes free-text keyword search combined with deterministic multi-attribute scoring and anti-bias sponsored placement interleaving.

- **Route**: `/api/v1/search`
- **Methods**: `GET`, `POST`
- **Rate Limit**: 1,000 req/min per tenant

#### Query Parameters (`GET`)
| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `company_id` | Integer | Yes* | — | Tenant Company ID (optional if `X-Company-ID` header is set). |
| `q` | String | No | `""` | Free-text search query. Searches product names using case-insensitive substring matching. If empty, ranks all category products. |
| `category_id` | Integer | No | `null` | Filters results to a specific category. Recommended when applying `custom_weights`. |
| `limit` | Integer | No | `20` | Maximum number of results to return (capped at 100). |
| `offset` | Integer | No | `0` | Number of results to skip (for pagination). |
| `include_sponsors`| Boolean | No | `true` | When `true`, interleaves active sponsored placements adhering to the 1:5 placement policy. |

#### JSON Payload (`POST`)
Used when submitting complex queries with **Dynamic Custom Weights** for customer personalization:

```json
{
  "company_id": 1,
  "q": "anc earbuds",
  "category_id": 1,
  "limit": 10,
  "offset": 0,
  "include_sponsors": true,
  "custom_weights": {
    "Battery Life (hours)": 40.0,
    "Price (INR)": 30.0,
    "Rating": 15.0,
    "Active Noise Cancelling": 15.0
  }
}
```

> **Custom Weights Rule**: The sum of values in `custom_weights` **must equal exactly 100.0%** ($\pm 0.05\%$ floating-point tolerance). Keys can be attribute names (e.g. `"Price (INR)"`) or stringified attribute IDs (e.g. `"2"`).

#### Success Response (`200 OK`)
```json
{
  "status": "success",
  "engine": "Weighted Ranking Engine",
  "company_id": 1,
  "company_name": "TechMart Electronics",
  "query": "anc earbuds",
  "category_id": 1,
  "category_name": "Wireless Earbuds",
  "total_results": 7,
  "offset": 0,
  "limit": 10,
  "results": [
    {
      "rank": 1,
      "product_id": 2,
      "name": "boAt Airdopes 141",
      "category_id": 1,
      "category_name": "Wireless Earbuds",
      "composite_score": 0.8145,
      "score_pct": "81.5%",
      "is_sponsored": true,
      "attributes": {
        "Battery Life (hours)": {
          "attribute_id": 1,
          "data_type": "numeric",
          "raw_value": 42.0,
          "normalized_value": 1.0,
          "weight": 35.0,
          "lower_is_better": false,
          "display_value": 42.0
        },
        "Price (INR)": {
          "attribute_id": 2,
          "data_type": "numeric",
          "raw_value": 999.0,
          "normalized_value": 0.9655,
          "weight": 35.0,
          "lower_is_better": true,
          "display_value": 999.0
        },
        "Rating": {
          "attribute_id": 3,
          "data_type": "numeric",
          "raw_value": 3.8,
          "normalized_value": 0.76,
          "weight": 15.0,
          "lower_is_better": false,
          "display_value": 3.8
        },
        "Active Noise Cancelling": {
          "attribute_id": 4,
          "data_type": "binary",
          "raw_value": 0.0,
          "normalized_value": 0.0,
          "weight": 15.0,
          "lower_is_better": false,
          "display_value": "NO"
        }
      }
    },
    {
      "rank": 2,
      "product_id": 1,
      "name": "Sony WF-1000XM5",
      "category_id": 1,
      "category_name": "Wireless Earbuds",
      "composite_score": 0.7325,
      "score_pct": "73.3%",
      "is_sponsored": false,
      "attributes": {
        "Battery Life (hours)": {
          "attribute_id": 1,
          "data_type": "numeric",
          "raw_value": 30.0,
          "normalized_value": 0.75,
          "weight": 35.0,
          "lower_is_better": false,
          "display_value": 30.0
        },
        "Price (INR)": {
          "attribute_id": 2,
          "data_type": "numeric",
          "raw_value": 12990.0,
          "normalized_value": 0.1386,
          "weight": 35.0,
          "lower_is_better": true,
          "display_value": 12990.0
        },
        "Rating": {
          "attribute_id": 3,
          "data_type": "numeric",
          "raw_value": 4.5,
          "normalized_value": 0.9,
          "weight": 15.0,
          "lower_is_better": false,
          "display_value": 4.5
        },
        "Active Noise Cancelling": {
          "attribute_id": 4,
          "data_type": "binary",
          "raw_value": 1.0,
          "normalized_value": 1.0,
          "weight": 15.0,
          "lower_is_better": false,
          "display_value": "YES"
        }
      }
    }
  ]
}
```

---

### 2. Tenant Category & Attribute Schema

Retrieves all product categories, active scoring attributes, boundary ranges ($min / max$), directionality (`lower_is_better`), and data types for the tenant.

- **Route**: `/api/v1/categories`
- **Method**: `GET`

#### Query Parameters
| Parameter | Type | Required | Description |
|---|---|---|---|
| `company_id` | Integer | Yes* | Tenant Company ID (or via `X-Company-ID` header). |

#### Success Response (`200 OK`)
```json
{
  "status": "success",
  "company_id": 1,
  "company_name": "TechMart Electronics",
  "categories": [
    {
      "category_id": 1,
      "name": "Wireless Earbuds",
      "product_count": 7,
      "attributes": [
        {
          "attribute_id": 1,
          "name": "Battery Life (hours)",
          "data_type": "numeric",
          "weight": 35.0,
          "min_value": 0.0,
          "max_value": 40.0,
          "lower_is_better": false
        },
        {
          "attribute_id": 2,
          "name": "Price (INR)",
          "data_type": "numeric",
          "weight": 35.0,
          "min_value": 500.0,
          "max_value": 15000.0,
          "lower_is_better": true
        },
        {
          "attribute_id": 3,
          "name": "Rating",
          "data_type": "numeric",
          "weight": 15.0,
          "min_value": 0.0,
          "max_value": 5.0,
          "lower_is_better": false
        },
        {
          "attribute_id": 4,
          "name": "Active Noise Cancelling",
          "data_type": "binary",
          "weight": 15.0,
          "min_value": 0.0,
          "max_value": 1.0,
          "lower_is_better": false
        }
      ]
    },
    {
      "category_id": 2,
      "name": "Budget Laptops",
      "product_count": 5,
      "attributes": [
        {
          "attribute_id": 5,
          "name": "Performance Score",
          "data_type": "numeric",
          "weight": 40.0,
          "min_value": 0.0,
          "max_value": 100.0,
          "lower_is_better": false
        },
        {
          "attribute_id": 6,
          "name": "Price (INR)",
          "data_type": "numeric",
          "weight": 35.0,
          "min_value": 20000.0,
          "max_value": 80000.0,
          "lower_is_better": true
        },
        {
          "attribute_id": 7,
          "name": "Display Quality",
          "data_type": "numeric",
          "weight": 25.0,
          "min_value": 0.0,
          "max_value": 10.0,
          "lower_is_better": false
        }
      ]
    }
  ]
}
```

---

### 3. Product Score Breakdown & Attribution

Returns detailed ranking information for a single product, including its composite score, active sponsorship status, search telemetry hits, and the mathematical formula breakdown per attribute.

- **Route**: `/api/v1/product/<int:product_id>`
- **Method**: `GET`

#### Success Response (`200 OK`)
```json
{
  "status": "success",
  "product_id": 1,
  "name": "Sony WF-1000XM5",
  "company_id": 1,
  "company_name": "TechMart Electronics",
  "category_id": 1,
  "category_name": "Wireless Earbuds",
  "composite_score": 0.7325,
  "score_pct": "73.3%",
  "search_count": 99,
  "is_sponsored": false,
  "score_breakdown": [
    {
      "attribute_name": "Battery Life (hours)",
      "raw_value": 30.0,
      "normalized_value": 0.75,
      "weight": 35.0,
      "weighted_score": 0.2625,
      "percentage_of_score": 35.84,
      "lower_is_better": false
    },
    {
      "attribute_name": "Price (INR)",
      "raw_value": 12990.0,
      "normalized_value": 0.1386,
      "weight": 35.0,
      "weighted_score": 0.0485,
      "percentage_of_score": 6.62,
      "lower_is_better": true
    },
    {
      "attribute_name": "Rating",
      "raw_value": 4.5,
      "normalized_value": 0.9,
      "weight": 15.0,
      "weighted_score": 0.135,
      "percentage_of_score": 18.43,
      "lower_is_better": false
    },
    {
      "attribute_name": "Active Noise Cancelling",
      "raw_value": 1.0,
      "normalized_value": 1.0,
      "weight": 15.0,
      "weighted_score": 0.15,
      "percentage_of_score": 20.48,
      "lower_is_better": false
    }
  ]
}
```

---

## ⚠️ Error Codes & Formats

When an API request fails, the engine returns a standard JSON error envelope with an appropriate HTTP status code:

```json
{
  "status": "error",
  "error": "ERROR_CODE_CONSTANT",
  "message": "Human-readable explanation of why the request was rejected."
}
```

### Error Code Reference Matrix

| HTTP Status | Error Code | Description / Remedy |
|---|---|---|
| `400 Bad Request` | `MISSING_COMPANY_ID` | Neither `X-Company-ID` header, query parameter, nor body field was supplied. |
| `400 Bad Request` | `INVALID_CATEGORY_ID` | The provided `category_id` cannot be parsed as an integer. |
| `400 Bad Request` | `INVALID_WEIGHT_SUM` | Custom weights do not sum to 100.0%. Ensure sum equals 100 within $\pm 0.05\%$. |
| `400 Bad Request` | `INVALID_WEIGHTS` | One or more weight values are non-numeric or negative. |
| `404 Not Found` | `COMPANY_NOT_FOUND` | The specified `company_id` does not exist in the platform database. |
| `404 Not Found` | `CATEGORY_NOT_FOUND` | The specified `category_id` does not belong to the tenant company. |
| `404 Not Found` | `PRODUCT_NOT_FOUND` | The specified `product_id` was not found or belongs to another company. |

---

## 💻 Code Integration Examples

### Example 1: Python (`requests`) with Custom Weights
```python
import requests

ENGINE_URL = "http://localhost:5000/api/v1/search"
HEADERS = {"X-Company-ID": "1", "Content-Type": "application/json"}

payload = {
    "q": "Noise",
    "category_id": 1,
    "limit": 10,
    "custom_weights": {
        "Battery Life (hours)": 50.0,
        "Price (INR)": 20.0,
        "Rating": 15.0,
        "Active Noise Cancelling": 15.0
    }
}

response = requests.post(ENGINE_URL, json=payload, headers=HEADERS, timeout=3.0)
if response.status_code == 200:
    data = response.json()
    for item in data['results']:
        print(f"#{item['rank']} {item['name']} - Score: {item['score_pct']} (Sponsored: {item['is_sponsored']})")
else:
    print(f"Error {response.status_code}: {response.json().get('message')}")
```

### Example 2: JavaScript (Node.js / Browser `fetch`)
```javascript
async function searchRankedProducts(query, categoryId, customWeights) {
  const url = 'http://localhost:5000/api/v1/search';
  const response = await fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-Company-ID': '1'
    },
    body: JSON.stringify({
      q: query,
      category_id: categoryId,
      custom_weights: customWeights,
      limit: 20
    })
  });

  const data = await response.json();
  if (data.status === 'success') {
    return data.results;
  } else {
    throw new Error(data.message);
  }
}
```

### Example 3: cURL Command Line
```bash
curl -X POST "http://localhost:5000/api/v1/search" \
  -H "X-Company-ID: 1" \
  -H "Content-Type: application/json" \
  -d '{
    "q": "",
    "category_id": 1,
    "custom_weights": {
      "Battery Life (hours)": 35.0,
      "Price (INR)": 35.0,
      "Rating": 15.0,
      "Active Noise Cancelling": 15.0
    }
  }'
```
