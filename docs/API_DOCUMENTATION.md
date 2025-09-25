# Istanbul Plus E-commerce API Documentation

## Overview

This document provides comprehensive documentation for the Istanbul Plus E-commerce API, focusing on the advanced authentication system and user management features.

## Base URL

- Development: `http://localhost:8000/api/`
- Production: `https://istanbulplus.ir/api/`

## Authentication

The API uses JWT (JSON Web Token) authentication. Include the token in the Authorization header:

```
Authorization: Bearer <your_jwt_token>
```

## API Endpoints

### Authentication Endpoints

#### 1. Register User

- **URL:** `POST /api/auth/register/`
- **Description:** Register a new user account
- **Authentication:** Not required

**Request Body:**

```json
{
  "username": "string",
  "email": "user@example.com",
  "password": "string",
  "phone": "+989123456789",
  "first_name": "string",
  "last_name": "string"
}
```

**Response (201 Created):**

```json
{
  "user": {
    "id": "uuid",
    "username": "string",
    "email": "user@example.com",
    "phone": "+989123456789",
    "first_name": "string",
    "last_name": "string",
    "email_verified": false,
    "phone_verified": false
  },
  "tokens": {
    "access": "jwt_access_token",
    "refresh": "jwt_refresh_token"
  }
}
```

#### 2. Login User

- **URL:** `POST /api/auth/login/`
- **Description:** Authenticate user and get JWT tokens
- **Authentication:** Not required

**Request Body:**

```json
{
  "username": "string",
  "password": "string"
}
```

**Response (200 OK):**

```json
{
  "user": {
    "id": "uuid",
    "username": "string",
    "email": "user@example.com"
  },
  "tokens": {
    "access": "jwt_access_token",
    "refresh": "jwt_refresh_token"
  }
}
```

#### 3. Send OTP

- **URL:** `POST /api/auth/send-otp/`
- **Description:** Send OTP code via SMS or email
- **Authentication:** Not required

**Request Body:**

```json
{
  "contact_info": "user@example.com",
  "delivery_method": "email",
  "purpose": "login"
}
```

**Response (200 OK):**

```json
{
  "message": "OTP sent successfully",
  "delivery_method": "email",
  "expires_in": 300
}
```

#### 4. Verify OTP

- **URL:** `POST /api/auth/verify-otp/`
- **Description:** Verify OTP code and complete authentication
- **Authentication:** Not required

**Request Body:**

```json
{
  "contact_info": "user@example.com",
  "code": "123456",
  "purpose": "login"
}
```

**Response (200 OK):**

```json
{
  "user": {
    "id": "uuid",
    "username": "string",
    "email": "user@example.com"
  },
  "tokens": {
    "access": "jwt_access_token",
    "refresh": "jwt_refresh_token"
  }
}
```

#### 5. Password Reset Request

- **URL:** `POST /api/auth/password-reset/request/`
- **Description:** Request password reset token
- **Authentication:** Not required

**Request Body:**

```json
{
  "email": "user@example.com"
}
```

**Response (200 OK):**

```json
{
  "message": "Password reset instructions sent to your email"
}
```

#### 6. Password Reset Confirm

- **URL:** `POST /api/auth/password-reset/confirm/`
- **Description:** Confirm password reset with token
- **Authentication:** Not required

**Request Body:**

```json
{
  "token": "reset_token",
  "new_password": "new_password"
}
```

**Response (200 OK):**

```json
{
  "message": "Password reset successfully"
}
```

### Profile Management Endpoints

#### 7. Get User Profile

- **URL:** `GET /api/auth/profile/`
- **Description:** Get current user's profile information
- **Authentication:** Required

**Response (200 OK):**

```json
{
  "id": "uuid",
  "username": "string",
  "email": "user@example.com",
  "phone": "+989123456789",
  "first_name": "string",
  "last_name": "string",
  "avatar": "url_to_avatar",
  "birth_date": "1990-01-01",
  "email_verified": true,
  "phone_verified": true,
  "two_factor_enabled": false,
  "email_notifications": true,
  "sms_notifications": true,
  "date_joined": "2024-01-01T00:00:00Z",
  "last_login": "2024-01-01T00:00:00Z"
}
```

#### 8. Update User Profile

- **URL:** `PUT /api/auth/profile/`
- **Description:** Update user profile information
- **Authentication:** Required

**Request Body:**

```json
{
  "first_name": "string",
  "last_name": "string",
  "birth_date": "1990-01-01",
  "email_notifications": true,
  "sms_notifications": true
}
```

**Response (200 OK):**

```json
{
  "message": "Profile updated successfully",
  "user": {
    // Updated user object
  }
}
```

#### 9. Change Password

- **URL:** `POST /api/auth/change-password/`
- **Description:** Change user password
- **Authentication:** Required

**Request Body:**

```json
{
  "current_password": "current_password",
  "new_password": "new_password"
}
```

**Response (200 OK):**

```json
{
  "message": "Password changed successfully"
}
```

### Session Management Endpoints

#### 10. List Active Sessions

- **URL:** `GET /api/auth/sessions/`
- **Description:** Get list of user's active sessions
- **Authentication:** Required

**Response (200 OK):**

```json
{
  "sessions": [
    {
      "id": "uuid",
      "ip_address": "192.168.1.1",
      "user_agent": "Mozilla/5.0...",
      "location": "Tehran, Iran",
      "created_at": "2024-01-01T00:00:00Z",
      "last_activity": "2024-01-01T12:00:00Z",
      "is_current": true
    }
  ]
}
```

#### 11. Terminate Session

- **URL:** `DELETE /api/auth/sessions/{session_id}/`
- **Description:** Terminate a specific session
- **Authentication:** Required

**Response (204 No Content)**

#### 12. Logout All Devices

- **URL:** `POST /api/auth/logout-all/`
- **Description:** Logout from all devices
- **Authentication:** Required

**Response (200 OK):**

```json
{
  "message": "Logged out from all devices successfully"
}
```

### Email Verification Endpoints

#### 13. Send Email Verification

- **URL:** `POST /api/auth/verify-email/send/`
- **Description:** Send email verification link
- **Authentication:** Required

**Response (200 OK):**

```json
{
  "message": "Verification email sent successfully"
}
```

#### 14. Verify Email

- **URL:** `POST /api/auth/verify-email/confirm/`
- **Description:** Verify email with token
- **Authentication:** Not required

**Request Body:**

```json
{
  "token": "verification_token"
}
```

**Response (200 OK):**

```json
{
  "message": "Email verified successfully"
}
```

### Phone Verification Endpoints

#### 15. Send Phone Verification

- **URL:** `POST /api/auth/verify-phone/send/`
- **Description:** Send phone verification OTP
- **Authentication:** Required

**Response (200 OK):**

```json
{
  "message": "Verification SMS sent successfully"
}
```

#### 16. Verify Phone

- **URL:** `POST /api/auth/verify-phone/confirm/`
- **Description:** Verify phone with OTP
- **Authentication:** Required

**Request Body:**

```json
{
  "code": "123456"
}
```

**Response (200 OK):**

```json
{
  "message": "Phone verified successfully"
}
```

## Error Responses

### Common Error Codes

- **400 Bad Request:** Invalid request data
- **401 Unauthorized:** Authentication required or invalid
- **403 Forbidden:** Permission denied
- **404 Not Found:** Resource not found
- **429 Too Many Requests:** Rate limit exceeded
- **500 Internal Server Error:** Server error

### Error Response Format

```json
{
  "error": {
    "code": "error_code",
    "message": "Human readable error message",
    "details": {
      "field_name": ["Field specific error messages"]
    }
  }
}
```

### Authentication Specific Errors

#### Account Locked

```json
{
  "error": {
    "code": "account_locked",
    "message": "Account is temporarily locked due to multiple failed login attempts",
    "details": {
      "locked_until": "2024-01-01T13:00:00Z",
      "retry_after": 1800
    }
  }
}
```

#### Rate Limit Exceeded

```json
{
  "error": {
    "code": "rate_limit_exceeded",
    "message": "Too many requests. Please try again later.",
    "details": {
      "retry_after": 3600,
      "limit": 5,
      "window": "1 hour"
    }
  }
}
```

#### Invalid OTP

```json
{
  "error": {
    "code": "invalid_otp",
    "message": "Invalid or expired OTP code",
    "details": {
      "attempts_remaining": 2,
      "expires_at": "2024-01-01T12:05:00Z"
    }
  }
}
```

## Rate Limiting

The API implements rate limiting to prevent abuse:

- **OTP Requests:** 5 per hour per IP/user
- **Login Attempts:** 10 per hour per IP
- **Password Reset:** 3 per hour per email
- **General API:** 1000 per hour per authenticated user

Rate limit headers are included in responses:

- `X-RateLimit-Limit`: Request limit per window
- `X-RateLimit-Remaining`: Remaining requests in current window
- `X-RateLimit-Reset`: Time when the rate limit resets

## Security Features

### Account Security

- Automatic account locking after 3 failed login attempts
- Password strength validation
- Secure password hashing with bcrypt
- Session management and tracking

### OTP Security

- 6-digit random codes
- 5-minute expiration
- Maximum 3 verification attempts
- Rate limiting on generation

### Communication Security

- HTTPS enforcement in production
- CSRF protection
- XSS protection headers
- Content Security Policy

## SDK and Examples

### JavaScript/Node.js Example

```javascript
const API_BASE = "https://istanbulplus.ir/api";

// Login
async function login(username, password) {
  const response = await fetch(`${API_BASE}/auth/login/`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ username, password }),
  });

  if (response.ok) {
    const data = await response.json();
    localStorage.setItem("access_token", data.tokens.access);
    localStorage.setItem("refresh_token", data.tokens.refresh);
    return data.user;
  } else {
    throw new Error("Login failed");
  }
}

// Authenticated request
async function getProfile() {
  const token = localStorage.getItem("access_token");
  const response = await fetch(`${API_BASE}/auth/profile/`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  return response.json();
}
```

### Python Example

```python
import requests

API_BASE = 'https://istanbulplus.ir/api'

class IstanbulPlusAPI:
    def __init__(self):
        self.session = requests.Session()
        self.access_token = None

    def login(self, username, password):
        response = self.session.post(f'{API_BASE}/auth/login/', json={
            'username': username,
            'password': password
        })

        if response.status_code == 200:
            data = response.json()
            self.access_token = data['tokens']['access']
            self.session.headers.update({
                'Authorization': f'Bearer {self.access_token}'
            })
            return data['user']
        else:
            raise Exception('Login failed')

    def get_profile(self):
        response = self.session.get(f'{API_BASE}/auth/profile/')
        return response.json()
```

## Changelog

### Version 1.0.0

- Initial API release
- JWT authentication
- OTP support (SMS/Email)
- Password reset functionality
- Email/Phone verification
- Session management
- Rate limiting
- Security logging

## Support

For API support and questions:

- Email: support@istanbulplus.ir
- Documentation: https://istanbulplus.ir/api/docs/
- Status Page: https://status.istanbulplus.ir
