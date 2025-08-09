# Security Policy

## Supported Versions

We release patches for security vulnerabilities. Currently supported versions:

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |

## Reporting a Vulnerability

If you discover a security vulnerability within this LLM Chat App, please send an email to security@yourdomain.com. All security vulnerabilities will be promptly addressed.

**Please do not report security vulnerabilities through public GitHub issues.**

### What to Include

When reporting a vulnerability, please include:

- Description of the vulnerability
- Steps to reproduce the issue
- Possible impact
- Suggested fix (if any)

## Security Measures

### Application Security

#### Input Validation
- All user inputs are validated using Pydantic models
- Message length limits (10,000 characters for user messages, 5,000 for system messages)
- Conversation length limits (maximum 50 messages)
- Temperature and parameter validation

#### Rate Limiting
- Configurable per-IP rate limiting
- Default: 100 requests per 60-second window
- Graceful degradation with 429 status codes

#### CORS Protection
- Configurable allowed origins
- Default allows only localhost for development
- Must be explicitly configured for production domains

#### Authentication & Authorization
- API key validation for LLM providers
- Secret key validation (minimum 32 characters)
- Environment-based configuration validation

### Infrastructure Security

#### Container Security
- Non-root user execution (UID 1000)
- Read-only root filesystem
- Dropped capabilities (ALL)
- No privilege escalation
- Health checks included

#### Kubernetes Security
- Service Account with minimal permissions
- Security contexts enforced
- Resource limits and requests
- Pod Anti-Affinity for availability
- Network policies ready

### Data Security

#### Sensitive Data Handling
- API keys stored in Kubernetes secrets
- No sensitive data in logs
- Environment variables validated at startup
- Secure headers implementation

#### Communication Security
- HTTPS enforcement in production
- Secure session management
- HSTS headers
- Content Security Policy headers

## Security Configuration

### Environment Variables

Critical security-related environment variables:

```bash
# Required - API Authentication
LLM_API_KEY=your-provider-api-key

# Required - Application Security
SECRET_KEY=secure-random-string-minimum-32-characters

# Security Configuration
ALLOWED_ORIGINS=["https://yourdomain.com"]
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=60
API_REQUEST_TIMEOUT=60

# Production Settings
APP_ENV=production
DEBUG=false
LOG_LEVEL=WARNING
```

### Production Security Checklist

#### Before Deployment
- [ ] Generate cryptographically secure `SECRET_KEY`
- [ ] Validate all API keys are production-ready
- [ ] Configure `ALLOWED_ORIGINS` for your domain only
- [ ] Set `APP_ENV=production` and `DEBUG=false`
- [ ] Review and adjust rate limiting settings
- [ ] Enable HTTPS with valid certificates
- [ ] Configure logging to exclude sensitive data

#### Kubernetes Deployment
- [ ] Update secrets in `k8s/base/service.yaml`
- [ ] Configure network policies
- [ ] Set resource limits appropriately
- [ ] Enable Pod Security Standards
- [ ] Configure service mesh (if applicable)
- [ ] Set up monitoring and alerting

#### Monitoring & Alerting
- [ ] Monitor for unusual API usage patterns
- [ ] Set up alerts for rate limit violations
- [ ] Monitor error rates and response times
- [ ] Set up log aggregation and analysis
- [ ] Configure uptime monitoring

### Security Headers

The application automatically includes security headers:

```
Strict-Transport-Security: max-age=31536000; includeSubDomains
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
X-XSS-Protection: 1; mode=block
Referrer-Policy: strict-origin-when-cross-origin
```

### Rate Limiting

Default rate limiting configuration:
- 100 requests per 60-second window per IP
- Configurable via environment variables
- Returns 429 status with retry information
- Graceful degradation for legitimate users

## Vulnerability Management

### Known Security Considerations

1. **API Key Exposure**: Ensure API keys are never committed to version control
2. **CORS Misconfiguration**: Properly configure allowed origins for production
3. **Rate Limiting Bypass**: Monitor for attempts to bypass rate limiting
4. **Input Validation**: Continuously validate all user inputs
5. **Dependency Vulnerabilities**: Regularly update dependencies

### Security Updates

We monitor dependencies for security vulnerabilities using:
- GitHub Security Advisories
- Dependabot alerts
- Regular dependency audits

### Incident Response

In case of a security incident:

1. **Immediate Response**
   - Assess the scope and impact
   - Contain the threat
   - Preserve evidence

2. **Investigation**
   - Analyze logs and metrics
   - Identify root cause
   - Document findings

3. **Recovery**
   - Apply fixes
   - Verify resolution
   - Monitor for recurrence

4. **Post-Incident**
   - Update security measures
   - Improve monitoring
   - Share learnings

## Compliance & Standards

### Security Standards
- OWASP Top 10 compliance
- Secure coding practices
- Defense in depth approach
- Principle of least privilege

### Privacy Considerations
- No persistent storage of chat content by default
- Local browser storage for user convenience (can be disabled)
- No data sharing with third parties beyond LLM providers
- Transparent data handling practices

## Security Testing

### Automated Testing
- Security-focused unit tests
- Integration tests for authentication
- CORS policy validation
- Rate limiting verification

### Manual Testing
- Penetration testing (recommended for production)
- Code review for security issues
- Configuration validation
- Dependency vulnerability scans

## Contact Information

For security-related inquiries:
- **Security Email**: security@yourdomain.com
- **PGP Key**: [Link to public key]
- **Response Time**: Within 24 hours for critical issues

## Attribution

We follow responsible disclosure practices and will credit security researchers who help improve our security posture.