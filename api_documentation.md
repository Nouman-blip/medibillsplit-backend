Here's the comprehensive API documentation for all endpoints:

---

## **1. Accounts API**

### **1.1 Registration**
**Endpoint**: `POST /api/accounts/register/`  
**Description**: Create new family account  
**Request**:
```json
{
  "email": "family@example.com",
  "password": "SecurePass123!",
  "password2": "SecurePass123!",
  "phone": "+1234567890",
  "primary_account": {
    "name": "Smith Family",
    "phone": "+1234567890",
    "address": "123 Main St"
  }
}
```
**Response** (`201 Created`):
```json
{
  "user_id": 1,
  "refresh": "xxx.yyy.zzz",
  "access": "aaa.bbb.ccc"
}
```

---

### **1.2 Login**
**Endpoint**: `POST /api/accounts/login/`  
**Description**: Authenticate user  
**Request**:
```json
{
  "email": "family@example.com",
  "password": "SecurePass123!"
}
```
**Response** (`200 OK`):
```json
{
  "user_id": 1,
  "email": "family@example.com",
  "access": "aaa.bbb.ccc"
}
```
**Cookie**: `refresh_token=xxx.yyy.zzz`

---

### **1.3 Logout**
**Endpoint**: `POST /api/accounts/logout/`  
**Description**: Invalidate refresh token  
**Response**: `205 Reset Content`

---

### **1.4 Account Management**
**Base Endpoint**: `/api/accounts/accounts/`  

| Method | URL Pattern | Description | 
|--------|-------------|-------------|
| GET | `/` | List all family accounts |
| POST | `/` | Create new account |
| GET | `/{id}/` | Get account details |
| PUT | `/{id}/` | Update account |
| DELETE | `/{id}/` | Delete account |

**Account Object**:
```json
{
  "id": 1,
  "name": "Smith Family",
  "phone": "+1234567890",
  "members": [
    {"id": 1, "name": "John", "role": "admin"},
    {"id": 2, "name": "Sarah", "role": "contributor"}
  ]
}
```

---

### **1.5 Member Management**
**Endpoint**: `POST /api/accounts/accounts/{account_id}/add_member/`  
**Request**:
```json
{
  "name": "Emma Smith",
  "email": "emma@example.com",
  "relationship": "CHILD",
  "access_level": "VIEWER"
}
```
**Response** (`201 Created`):
```json
{
  "id": 3,
  "name": "Emma Smith",
  "email": "emma@example.com",
  "relationship": "CHILD",
  "access_level": "VIEWER"
}
```

---

## **2. Insurance API**

### **2.1 Insurance Profiles**
**Base Endpoint**: `/api/insurance/profiles/`  

| Method | Description |
|--------|-------------|
| GET | List all policies |
| POST | Create new policy |
| PUT | Update policy |
| DELETE | Remove policy |

**Policy Object**:
```json
{
  "id": 1,
  "provider_name": "HealthPlus",
  "policy_number": "HP-12345",
  "insurance_type": "PPO",
  "deductible": 1500.00,
  "out_of_pocket_max": 6850.00
}
```

---

### **2.2 Coverage Calculation**
**Endpoint**: `POST /api/insurance/calculate-coverage/`  
**Request**:
```json
{
  "member_id": 1,
  "billed_amount": 2500.00,
  "service_type": "ER Visit",
  "provider_npi": "1234567890",
  "service_date": "2024-03-15"
}
```
**Response** (`200 OK`):
```json
{
  "total_billed": 2500.00,
  "insurance_covered": 1800.00,
  "patient_responsibility": 700.00,
  "breakdown": [
    {
      "policy": "HealthPlus PPO",
      "deductible_applied": 500.00,
      "coinsurance": 1300.00
    }
  ]
}
```

---

## **3. Billing API**

### **3.1 Bill Management**
**Base Endpoint**: `/api/billing/bills/`  

| Method | Description |
|--------|-------------|
| POST | Create new bill with line items |
| GET | List all bills |
| GET | `/{id}/` | Get bill details |

**Bill Creation Request**:
```json
{
  "provider_name": "City Hospital",
  "provider_npi": "1234567890",
  "total_amount": 3500.00,
  "line_items": [
    {
      "procedure_code": "99213",
      "description": "Emergency Visit",
      "amount": 1500.00
    }
  ]
}
```

---

### **3.2 Bill Splitting**
**Endpoint**: `POST /api/billing/bills/{bill_id}/split/`  
**Request**:
```json
{
  "method": "PERCENTAGE",
  "percentages": {
    "1": 60,
    "2": 40
  }
}
```
**Response** (`200 OK`):
```json
{
  "total_shared": 3500.00,
  "shares": [
    {
      "member": "John",
      "amount": 2100.00,
      "due_date": "2024-04-01"
    }
  ]
}
```

---

### **3.3 Payments**
**Base Endpoint**: `/api/billing/payments/`  

| Method | Description |
|--------|-------------|
| POST | Record payment |
| GET | List payment history |

**Payment Request**:
```json
{
  "bill_share": 1,
  "amount": 500.00,
  "payment_method": "credit_card",
  "transaction_id": "txn_12345"
}
```

---

### **3.4 Disputes**
**Base Endpoint**: `/api/billing/disputes/`  

| Method | Description |
|--------|-------------|
| POST | Create dispute |
| GET | List disputes |
| PUT | Update dispute status |

**Dispute Creation**:
```json
{
  "bill": 1,
  "reason": "Incorrect procedure code 99213"
}
```

---

## **4. Notifications API**

### **4.1 Notification Preferences**
**Endpoint**: `GET|PUT /api/notifications/preferences/`  
**Current Preferences**:
```json
{
  "email": true,
  "push": true,
  "sms": false,
  "types": ["PAYMENT", "DISPUTE"]
}
```

---

### **4.2 Notification Management**
**Base Endpoint**: `/api/notifications/notifications/`  

| Method | Description |
|--------|-------------|
| GET | List all notifications |
| POST | Mark all as read |
| GET | `/{id}/` | Get notification |
| DELETE | Delete notification |

**Notification Object**:
```json
{
  "id": 1,
  "type": "PAYMENT",
  "message": "Payment of $500 received",
  "is_read": false,
  "created_at": "2024-03-15T10:00:00Z"
}
```

---

## **Common Responses**

### **Success**
- `200 OK`: Successful GET/PUT
- `201 Created`: Resource created
- `204 No Content`: Successful DELETE

### **Errors**
- `400 Bad Request`: Invalid input
- `401 Unauthorized`: Missing/invalid token
- `403 Forbidden`: Insufficient permissions
- `404 Not Found`: Resource not found
- `500 Internal Server Error`: Server error

---

**Authentication**:  
Include JWT token in Authorization header:  
`Authorization: Bearer <access_token>`
