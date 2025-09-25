# API Documentation Configuration for User Authentication System
# This file contains OpenAPI schema customizations and documentation

from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample
from drf_spectacular.types import OpenApiTypes
from rest_framework import status

# Common response schemas
COMMON_ERROR_RESPONSES = {
    400: {
        "description": "Bad Request",
        "examples": {
            "validation_error": {
                "summary": "Validation Error",
                "value": {
                    "error": {
                        "code": "validation_error",
                        "message": "Invalid input data",
                        "details": {
                            "email": ["Enter a valid email address."],
                            "password": ["This field is required."]
                        }
                    }
                }
            }
        }
    },
    401: {
        "description": "Unauthorized",
        "examples": {
            "invalid_credentials": {
                "summary": "Invalid Credentials",
                "value": {
                    "error": {
                        "code": "invalid_credentials",
                        "message": "Invalid username or password"
                    }
                }
            },
            "token_expired": {
                "summary": "Token Expired",
                "value": {
                    "error": {
                        "code": "token_expired",
                        "message": "Access token has expired"
                    }
                }
            }
        }
    },
    403: {
        "description": "Forbidden",
        "examples": {
            "account_locked": {
                "summary": "Account Locked",
                "value": {
                    "error": {
                        "code": "account_locked",
                        "message": "Account is temporarily locked due to multiple failed login attempts",
                        "details": {
                            "locked_until": "2024-01-01T13:00:00Z",
                            "retry_after": 1800
                        }
                    }
                }
            }
        }
    },
    429: {
        "description": "Too Many Requests",
        "examples": {
            "rate_limit_exceeded": {
                "summary": "Rate Limit Exceeded",
                "value": {
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
            }
        }
    },
    500: {
        "description": "Internal Server Error",
        "examples": {
            "server_error": {
                "summary": "Server Error",
                "value": {
                    "error": {
                        "code": "internal_error",
                        "message": "An internal server error occurred"
                    }
                }
            }
        }
    }
}

# Authentication schemas
REGISTER_SCHEMA = extend_schema(
    tags=['Authentication'],
    summary='Register new user',
    description='Create a new user account with email/phone verification',
    request={
        'application/json': {
            'type': 'object',
            'properties': {
                'username': {'type': 'string', 'minLength': 3, 'maxLength': 150},
                'email': {'type': 'string', 'format': 'email'},
                'password': {'type': 'string', 'minLength': 8},
                'phone': {'type': 'string', 'pattern': r'^\+?[1-9]\d{1,14}$'},
                'first_name': {'type': 'string', 'maxLength': 30},
                'last_name': {'type': 'string', 'maxLength': 30}
            },
            'required': ['username', 'email', 'password']
        }
    },
    responses={
        201: {
            'description': 'User registered successfully',
            'examples': {
                'success': {
                    'summary': 'Successful Registration',
                    'value': {
                        'user': {
                            'id': 'uuid',
                            'username': 'john_doe',
                            'email': 'john@example.com',
                            'phone': '+989123456789',
                            'first_name': 'John',
                            'last_name': 'Doe',
                            'email_verified': False,
                            'phone_verified': False
                        },
                        'tokens': {
                            'access': 'jwt_access_token',
                            'refresh': 'jwt_refresh_token'
                        }
                    }
                }
            }
        },
        **COMMON_ERROR_RESPONSES
    }
)

LOGIN_SCHEMA = extend_schema(
    tags=['Authentication'],
    summary='User login',
    description='Authenticate user with username/email and password',
    request={
        'application/json': {
            'type': 'object',
            'properties': {
                'username': {'type': 'string', 'description': 'Username or email'},
                'password': {'type': 'string'}
            },
            'required': ['username', 'password']
        }
    },
    responses={
        200: {
            'description': 'Login successful',
            'examples': {
                'success': {
                    'summary': 'Successful Login',
                    'value': {
                        'user': {
                            'id': 'uuid',
                            'username': 'john_doe',
                            'email': 'john@example.com'
                        },
                        'tokens': {
                            'access': 'jwt_access_token',
                            'refresh': 'jwt_refresh_token'
                        }
                    }
                }
            }
        },
        **COMMON_ERROR_RESPONSES
    }
)

SEND_OTP_SCHEMA = extend_schema(
    tags=['Authentication'],
    summary='Send OTP code',
    description='Send OTP code via SMS or email for authentication or verification',
    request={
        'application/json': {
            'type': 'object',
            'properties': {
                'contact_info': {'type': 'string', 'description': 'Email or phone number'},
                'delivery_method': {'type': 'string', 'enum': ['sms', 'email']},
                'purpose': {'type': 'string', 'enum': ['login', 'register', 'password_reset', 'email_verify', 'phone_verify']}
            },
            'required': ['contact_info', 'delivery_method', 'purpose']
        }
    },
    responses={
        200: {
            'description': 'OTP sent successfully',
            'examples': {
                'success': {
                    'summary': 'OTP Sent',
                    'value': {
                        'message': 'OTP sent successfully',
                        'delivery_method': 'email',
                        'expires_in': 300
                    }
                }
            }
        },
        **COMMON_ERROR_RESPONSES
    }
)

VERIFY_OTP_SCHEMA = extend_schema(
    tags=['Authentication'],
    summary='Verify OTP code',
    description='Verify OTP code and complete authentication process',
    request={
        'application/json': {
            'type': 'object',
            'properties': {
                'contact_info': {'type': 'string', 'description': 'Email or phone number'},
                'code': {'type': 'string', 'pattern': r'^\d{6}$'},
                'purpose': {'type': 'string', 'enum': ['login', 'register', 'password_reset', 'email_verify', 'phone_verify']}
            },
            'required': ['contact_info', 'code', 'purpose']
        }
    },
    responses={
        200: {
            'description': 'OTP verified successfully',
            'examples': {
                'success': {
                    'summary': 'OTP Verified',
                    'value': {
                        'user': {
                            'id': 'uuid',
                            'username': 'john_doe',
                            'email': 'john@example.com'
                        },
                        'tokens': {
                            'access': 'jwt_access_token',
                            'refresh': 'jwt_refresh_token'
                        }
                    }
                }
            }
        },
        **COMMON_ERROR_RESPONSES
    }
)

PASSWORD_RESET_REQUEST_SCHEMA = extend_schema(
    tags=['Authentication'],
    summary='Request password reset',
    description='Request password reset token to be sent via email',
    request={
        'application/json': {
            'type': 'object',
            'properties': {
                'email': {'type': 'string', 'format': 'email'}
            },
            'required': ['email']
        }
    },
    responses={
        200: {
            'description': 'Password reset instructions sent',
            'examples': {
                'success': {
                    'summary': 'Reset Email Sent',
                    'value': {
                        'message': 'Password reset instructions sent to your email'
                    }
                }
            }
        },
        **COMMON_ERROR_RESPONSES
    }
)

PASSWORD_RESET_CONFIRM_SCHEMA = extend_schema(
    tags=['Authentication'],
    summary='Confirm password reset',
    description='Confirm password reset with token and set new password',
    request={
        'application/json': {
            'type': 'object',
            'properties': {
                'token': {'type': 'string'},
                'new_password': {'type': 'string', 'minLength': 8}
            },
            'required': ['token', 'new_password']
        }
    },
    responses={
        200: {
            'description': 'Password reset successfully',
            'examples': {
                'success': {
                    'summary': 'Password Reset',
                    'value': {
                        'message': 'Password reset successfully'
                    }
                }
            }
        },
        **COMMON_ERROR_RESPONSES
    }
)

# Profile management schemas
PROFILE_SCHEMA = extend_schema(
    tags=['Profile'],
    summary='Get user profile',
    description='Get current user profile information',
    responses={
        200: {
            'description': 'User profile data',
            'examples': {
                'success': {
                    'summary': 'User Profile',
                    'value': {
                        'id': 'uuid',
                        'username': 'john_doe',
                        'email': 'john@example.com',
                        'phone': '+989123456789',
                        'first_name': 'John',
                        'last_name': 'Doe',
                        'avatar': 'https://example.com/avatar.jpg',
                        'birth_date': '1990-01-01',
                        'email_verified': True,
                        'phone_verified': True,
                        'two_factor_enabled': False,
                        'email_notifications': True,
                        'sms_notifications': True,
                        'date_joined': '2024-01-01T00:00:00Z',
                        'last_login': '2024-01-01T00:00:00Z'
                    }
                }
            }
        },
        **COMMON_ERROR_RESPONSES
    }
)

UPDATE_PROFILE_SCHEMA = extend_schema(
    tags=['Profile'],
    summary='Update user profile',
    description='Update user profile information',
    request={
        'application/json': {
            'type': 'object',
            'properties': {
                'first_name': {'type': 'string', 'maxLength': 30},
                'last_name': {'type': 'string', 'maxLength': 30},
                'birth_date': {'type': 'string', 'format': 'date'},
                'email_notifications': {'type': 'boolean'},
                'sms_notifications': {'type': 'boolean'}
            }
        }
    },
    responses={
        200: {
            'description': 'Profile updated successfully',
            'examples': {
                'success': {
                    'summary': 'Profile Updated',
                    'value': {
                        'message': 'Profile updated successfully',
                        'user': {
                            'id': 'uuid',
                            'username': 'john_doe',
                            'email': 'john@example.com',
                            'first_name': 'John',
                            'last_name': 'Doe'
                        }
                    }
                }
            }
        },
        **COMMON_ERROR_RESPONSES
    }
)

CHANGE_PASSWORD_SCHEMA = extend_schema(
    tags=['Profile'],
    summary='Change password',
    description='Change user password',
    request={
        'application/json': {
            'type': 'object',
            'properties': {
                'current_password': {'type': 'string'},
                'new_password': {'type': 'string', 'minLength': 8}
            },
            'required': ['current_password', 'new_password']
        }
    },
    responses={
        200: {
            'description': 'Password changed successfully',
            'examples': {
                'success': {
                    'summary': 'Password Changed',
                    'value': {
                        'message': 'Password changed successfully'
                    }
                }
            }
        },
        **COMMON_ERROR_RESPONSES
    }
)

# Session management schemas
SESSIONS_LIST_SCHEMA = extend_schema(
    tags=['Security'],
    summary='List active sessions',
    description='Get list of user active sessions',
    responses={
        200: {
            'description': 'List of active sessions',
            'examples': {
                'success': {
                    'summary': 'Active Sessions',
                    'value': {
                        'sessions': [
                            {
                                'id': 'uuid',
                                'ip_address': '192.168.1.1',
                                'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                                'location': 'Tehran, Iran',
                                'created_at': '2024-01-01T00:00:00Z',
                                'last_activity': '2024-01-01T12:00:00Z',
                                'is_current': True
                            }
                        ]
                    }
                }
            }
        },
        **COMMON_ERROR_RESPONSES
    }
)

TERMINATE_SESSION_SCHEMA = extend_schema(
    tags=['Security'],
    summary='Terminate session',
    description='Terminate a specific user session',
    parameters=[
        OpenApiParameter(
            name='session_id',
            type=OpenApiTypes.UUID,
            location=OpenApiParameter.PATH,
            description='Session ID to terminate'
        )
    ],
    responses={
        204: {'description': 'Session terminated successfully'},
        **COMMON_ERROR_RESPONSES
    }
)

LOGOUT_ALL_SCHEMA = extend_schema(
    tags=['Security'],
    summary='Logout all devices',
    description='Logout from all devices and invalidate all sessions',
    responses={
        200: {
            'description': 'Logged out from all devices',
            'examples': {
                'success': {
                    'summary': 'Logout All',
                    'value': {
                        'message': 'Logged out from all devices successfully'
                    }
                }
            }
        },
        **COMMON_ERROR_RESPONSES
    }
)

# Email verification schemas
SEND_EMAIL_VERIFICATION_SCHEMA = extend_schema(
    tags=['Authentication'],
    summary='Send email verification',
    description='Send email verification link to user email',
    responses={
        200: {
            'description': 'Verification email sent',
            'examples': {
                'success': {
                    'summary': 'Verification Email Sent',
                    'value': {
                        'message': 'Verification email sent successfully'
                    }
                }
            }
        },
        **COMMON_ERROR_RESPONSES
    }
)

VERIFY_EMAIL_SCHEMA = extend_schema(
    tags=['Authentication'],
    summary='Verify email',
    description='Verify email address with verification token',
    request={
        'application/json': {
            'type': 'object',
            'properties': {
                'token': {'type': 'string'}
            },
            'required': ['token']
        }
    },
    responses={
        200: {
            'description': 'Email verified successfully',
            'examples': {
                'success': {
                    'summary': 'Email Verified',
                    'value': {
                        'message': 'Email verified successfully'
                    }
                }
            }
        },
        **COMMON_ERROR_RESPONSES
    }
)

# Phone verification schemas
SEND_PHONE_VERIFICATION_SCHEMA = extend_schema(
    tags=['Authentication'],
    summary='Send phone verification',
    description='Send phone verification OTP to user phone',
    responses={
        200: {
            'description': 'Verification SMS sent',
            'examples': {
                'success': {
                    'summary': 'Verification SMS Sent',
                    'value': {
                        'message': 'Verification SMS sent successfully'
                    }
                }
            }
        },
        **COMMON_ERROR_RESPONSES
    }
)

VERIFY_PHONE_SCHEMA = extend_schema(
    tags=['Authentication'],
    summary='Verify phone',
    description='Verify phone number with OTP code',
    request={
        'application/json': {
            'type': 'object',
            'properties': {
                'code': {'type': 'string', 'pattern': r'^\d{6}$'}
            },
            'required': ['code']
        }
    },
    responses={
        200: {
            'description': 'Phone verified successfully',
            'examples': {
                'success': {
                    'summary': 'Phone Verified',
                    'value': {
                        'message': 'Phone verified successfully'
                    }
                }
            }
        },
        **COMMON_ERROR_RESPONSES
    }
)
# Custom hooks for OpenAPI schema processing
def custom_preprocessing_hook(endpoints):
    """
    Custom preprocessing hook to modify endpoints before schema generation
    """
    # Add custom headers or modify endpoints if needed
    return endpoints

def custom_postprocessing_hook(result, generator, request, public):
    """
    Custom postprocessing hook to modify the generated schema
    """
    # Add custom examples or modify schema structure
    if 'components' not in result:
        result['components'] = {}
    
    if 'examples' not in result['components']:
        result['components']['examples'] = {}
    
    # Add common examples
    result['components']['examples'].update({
        'UserExample': {
            'summary': 'User Object Example',
            'value': {
                'id': 'uuid-string',
                'username': 'john_doe',
                'email': 'john@example.com',
                'phone': '+989123456789',
                'first_name': 'John',
                'last_name': 'Doe',
                'email_verified': True,
                'phone_verified': True,
                'date_joined': '2024-01-01T00:00:00Z'
            }
        },
        'TokensExample': {
            'summary': 'JWT Tokens Example',
            'value': {
                'access': 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...',
                'refresh': 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...'
            }
        },
        'ErrorExample': {
            'summary': 'Error Response Example',
            'value': {
                'error': {
                    'code': 'validation_error',
                    'message': 'Invalid input data',
                    'details': {
                        'email': ['Enter a valid email address.']
                    }
                }
            }
        }
    })
    
    return result

# Schema extensions for specific views
def get_auth_schema_extensions():
    """
    Get common schema extensions for authentication views
    """
    return {
        'security': [{'bearerAuth': []}],
        'responses': {
            401: {
                'description': 'Authentication credentials were not provided or are invalid',
                'content': {
                    'application/json': {
                        'schema': {
                            'type': 'object',
                            'properties': {
                                'error': {
                                    'type': 'object',
                                    'properties': {
                                        'code': {'type': 'string'},
                                        'message': {'type': 'string'}
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }