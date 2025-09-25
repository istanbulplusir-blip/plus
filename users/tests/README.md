# Comprehensive Authentication System Tests

This directory contains comprehensive integration and security tests for the user authentication system. The test suite covers all aspects of the authentication flow, security measures, performance characteristics, and browser compatibility.

## Test Structure

### Core Test Files

1. **`test_comprehensive_integration.py`** - Complete end-to-end integration tests

   - Full registration flow with email/phone verification
   - Complete login flow with OTP support
   - Security integration testing
   - Performance testing under load
   - Browser compatibility testing
   - End-to-end workflow testing

2. **`test_advanced_security_scenarios.py`** - Advanced security scenario tests

   - Brute force protection (distributed attacks, timing attacks)
   - Advanced OTP security (replay attacks, brute force, timing attacks)
   - Session hijacking protection
   - Advanced rate limiting scenarios
   - Data integrity and validation security

3. **`test_comprehensive_performance.py`** - Performance and scalability tests

   - Load testing with concurrent users
   - Database query optimization
   - Cache performance testing
   - Memory usage monitoring
   - Scalability testing

4. **`test_browser_compatibility.py`** - Browser compatibility tests
   - User agent compatibility across browsers
   - HTTP header handling
   - JavaScript/AJAX compatibility
   - Legacy browser support
   - Response time consistency

### Supporting Files

5. **`test_config.py`** - Test configuration and utilities

   - Test constants and thresholds
   - Test data templates
   - Utility functions and mixins
   - Performance decorators

6. **`run_comprehensive_tests.py`** - Test runner script
   - Automated test execution
   - Detailed reporting
   - Performance metrics
   - Failed test analysis

### Existing Test Files (Enhanced)

- `test_integration.py` - Basic integration tests
- `test_security_integration.py` - Security service integration
- `test_performance.py` - Basic performance tests
- `test_verification_integration.py` - Verification flow tests
- `test_password_reset.py` - Password reset flow tests
- `test_security.py` - Security feature tests
- `test_services.py` - Service layer tests

## Test Categories

### 1. Integration Testing

**Complete Registration Flow:**

- User registration with validation
- Email verification process
- Phone verification with OTP
- Profile completion
- Security logging

**Complete Login Flow:**

- Password-based login
- OTP-based login (SMS/Email)
- Multi-factor authentication
- Session management
- Security monitoring

**Password Reset Flow:**

- Reset request with OTP
- Token verification
- Password update
- Security notifications

### 2. Security Testing

**Brute Force Protection:**

- Account lockout mechanisms
- Rate limiting enforcement
- Distributed attack protection
- Timing attack prevention

**OTP Security:**

- Replay attack prevention
- Brute force protection
- Rate limiting per contact method
- Expiry enforcement

**Session Security:**

- Session fixation protection
- Concurrent session detection
- Token refresh security
- Session timeout handling

**Input Validation:**

- SQL injection prevention
- XSS protection
- Unicode handling
- Data integrity validation

### 3. Performance Testing

**Load Testing:**

- High-volume login requests
- Sustained load over time
- Memory usage monitoring
- Concurrent user operations

**Database Optimization:**

- Query performance testing
- Index effectiveness
- Bulk operation efficiency
- Connection handling

**Cache Performance:**

- Rate limiting cache efficiency
- Hit ratio optimization
- Memory usage monitoring
- Response time consistency

### 4. Browser Compatibility

**User Agent Testing:**

- Modern browsers (Chrome, Firefox, Safari, Edge)
- Mobile browsers (iOS Safari, Android Chrome)
- Legacy browsers (IE11, older versions)
- Response format consistency

**HTTP Header Handling:**

- Accept header variations
- Content-Type handling
- Language preferences
- Encoding support
- Custom headers

**JavaScript Compatibility:**

- AJAX request handling
- JSON response format
- CORS header support
- Error handling

## Running Tests

### Run All Tests

```bash
python users/tests/run_comprehensive_tests.py
```

### Run Specific Categories

```bash
# Integration tests only
python users/tests/run_comprehensive_tests.py --categories integration

# Security tests only
python users/tests/run_comprehensive_tests.py --categories security

# Performance tests only
python users/tests/run_comprehensive_tests.py --categories performance

# Browser compatibility tests only
python users/tests/run_comprehensive_tests.py --categories compatibility
```

### Run Specific Module

```bash
python users/tests/run_comprehensive_tests.py --module users.tests.test_comprehensive_integration
```

### Django Test Runner

```bash
# Run all authentication tests
python manage.py test users.tests --verbosity=2

# Run specific test file
python manage.py test users.tests.test_comprehensive_integration --verbosity=2

# Run specific test class
python manage.py test users.tests.test_comprehensive_integration.CompleteRegistrationFlowTest --verbosity=2
```

## Test Configuration

### Performance Thresholds

- Maximum response time: 2.0 seconds
- Maximum login time: 1.0 seconds
- Maximum registration time: 3.0 seconds
- Maximum OTP time: 0.5 seconds
- Concurrent users: 50
- Load test duration: 30 seconds

### Security Limits

- Maximum login attempts: 3
- Maximum OTP attempts: 3
- Rate limit (login): 5 per 15 minutes
- Rate limit (OTP): 5 per hour
- Account lock duration: 30 minutes
- OTP expiry: 5 minutes

### Browser Support

- Chrome 70+
- Firefox 60+
- Safari 12+
- Edge 79+
- Mobile Chrome 70+
- Mobile Safari 12+
- IE 11 (legacy support)

## Test Reports

Test reports are generated in the `test_reports/` directory:

- `comprehensive_test_report_YYYYMMDD_HHMMSS.json` - Detailed test results
- `failed_tests_YYYYMMDD_HHMMSS.json` - Failed test details

## Test Data

### Valid Test User

```python
{
    'username': 'testuser',
    'email': 'test@example.com',
    'phone': '+989123456789',
    'password': 'TestPassword123!',
    'first_name': 'Test',
    'last_name': 'User'
}
```

### Security Test Payloads

- SQL injection attempts
- XSS attack vectors
- Unicode edge cases
- Invalid input formats

## Utilities and Mixins

### TestUtils Class

- Configuration management
- Test data generation
- Performance measurement
- Cleanup utilities

### Test Mixins

- `PerformanceTestMixin` - Performance testing utilities
- `SecurityTestMixin` - Security testing utilities
- `BrowserCompatibilityTestMixin` - Browser testing utilities

### Decorators

- `@performance_test(max_time)` - Performance test decorator
- `@security_test` - Security test decorator
- `@browser_compatibility_test(browsers)` - Browser test decorator

## Coverage Areas

### ✅ Implemented

- Complete registration flow testing
- Complete login flow with OTP testing
- Advanced security scenario testing
- Performance and load testing
- Browser compatibility testing
- Database optimization testing
- Cache performance testing
- Session management testing
- Rate limiting testing
- Input validation testing

### 🔄 Continuous Monitoring

- Response time consistency
- Memory usage patterns
- Database query performance
- Cache hit ratios
- Security event logging
- Error rate monitoring

## Best Practices

1. **Test Isolation**: Each test is independent and cleans up after itself
2. **Realistic Data**: Tests use realistic user data and scenarios
3. **Performance Monitoring**: All tests include performance assertions
4. **Security Focus**: Security tests cover common attack vectors
5. **Browser Coverage**: Tests cover modern and legacy browsers
6. **Error Handling**: Tests verify proper error handling and messages
7. **Concurrent Testing**: Tests verify system behavior under load
8. **Data Integrity**: Tests verify data consistency and validation

## Maintenance

- Update browser user agents regularly
- Review performance thresholds quarterly
- Update security test payloads based on new threats
- Monitor test execution times and optimize slow tests
- Keep test data current with application changes

## Troubleshooting

### Common Issues

1. **Test Timeouts**: Increase timeout values in test configuration
2. **Database Locks**: Ensure proper test isolation and cleanup
3. **Cache Issues**: Clear cache between security tests
4. **Memory Leaks**: Monitor memory usage in performance tests
5. **Browser Compatibility**: Update user agent strings regularly

### Debug Mode

Set `DEBUG=True` in test settings for detailed error information.

### Verbose Output

Use `--verbosity=2` with Django test runner for detailed output.

## Contributing

When adding new tests:

1. Follow the existing test structure and naming conventions
2. Include performance assertions where appropriate
3. Add security considerations for new features
4. Update browser compatibility tests for new UI features
5. Document any new test utilities or configurations
6. Ensure tests are isolated and clean up properly
