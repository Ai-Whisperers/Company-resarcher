# AP-001: No Authentication Mechanism

## Status: RESOLVED - API Key Authentication Implemented

## Priority: Critical (for production deployment)

---

## Current State

| Security Layer | Status |
|----------------|--------|
| Rate limiting (10 req/min per IP) | ✅ Implemented |
| Request size limits (1MB max) | ✅ Implemented |
| Input validation via Pydantic | ✅ Implemented |
| CORS configured | ✅ Implemented |
| **Authentication** | ❌ Missing |

**Location**: `src/api/app.py` - All endpoints are unprotected

---

## The Problem

Without authentication, anyone with network access can:
- Initiate research requests (consuming AI API credits)
- Access all research results
- Exhaust rate limits for legitimate users
- Potentially access sensitive company research data

---

## Option Analysis

### Option 1: API Keys (Recommended for Current Stage)

**How it works**: Static keys stored in environment, validated via header.

| Aspect | Assessment |
|--------|------------|
| **Complexity** | Low - 2-4 hours implementation |
| **Security** | Good for internal/service-to-service |
| **Scalability** | Limited - manual key management |
| **User Experience** | Simple - one header to add |

**Pros**:
- Simplest to implement
- Stateless - no database required
- Works well for CLI tools, scripts, internal services
- Easy to rotate (update env + restart)

**Cons**:
- No user identity (just "valid key")
- Hard to manage at scale (100+ keys)
- No built-in expiration
- If leaked, must rotate for everyone

**Best for**: Internal tools, service-to-service, development, small teams

```python
# Implementation sketch
from fastapi import Security, HTTPException
from fastapi.security import APIKeyHeader

API_KEY_HEADER = APIKeyHeader(name="X-API-Key")

async def verify_api_key(api_key: str = Security(API_KEY_HEADER)):
    if api_key != settings.API_KEY.get_secret_value():
        raise HTTPException(status_code=401, detail="Invalid API key")
    return api_key

@app.post("/api/v1/research")
async def start_research(
    request: ResearchRequest,
    api_key: str = Depends(verify_api_key)  # Protected!
):
    ...
```

---

### Option 2: JWT (JSON Web Tokens)

**How it works**: User logs in, receives signed token, includes token in requests.

| Aspect | Assessment |
|--------|------------|
| **Complexity** | Medium - 1-2 days implementation |
| **Security** | Excellent for user-based auth |
| **Scalability** | High - stateless verification |
| **User Experience** | Requires login flow |

**Pros**:
- Stateless - token contains all info needed
- Scales to millions of users
- Self-contained user identity
- Works great with microservices
- Can include roles/permissions in token

**Cons**:
- Requires user database
- Token revocation needs blacklist mechanism
- More complex implementation
- Must secure the signing secret

**Best for**: Multi-user applications, microservices, mobile apps

```python
# Implementation sketch
from datetime import datetime, timedelta
import jwt  # Use PyJWT, not python-jose (abandoned)

class AuthService:
    def __init__(self, secret: str, algorithm: str = "HS256"):
        self.secret = secret
        self.algorithm = algorithm

    def create_token(self, user_id: str, expires_in: timedelta = timedelta(hours=24)):
        payload = {
            "sub": user_id,
            "exp": datetime.utcnow() + expires_in,
            "iat": datetime.utcnow()
        }
        return jwt.encode(payload, self.secret, algorithm=self.algorithm)

    def verify_token(self, token: str) -> dict:
        return jwt.decode(token, self.secret, algorithms=[self.algorithm])
```

---

### Option 3: OAuth2 + JWT

**How it works**: Full OAuth2 flow with JWT tokens, supports third-party auth.

| Aspect | Assessment |
|--------|------------|
| **Complexity** | High - 3-5 days implementation |
| **Security** | Enterprise-grade |
| **Scalability** | Excellent |
| **User Experience** | Can use Google/GitHub login |

**Pros**:
- Industry standard
- Supports "Login with Google/GitHub"
- Delegated access (scopes)
- Refresh token support
- Well-documented patterns

**Cons**:
- Significant complexity
- Overkill for internal tools
- Requires understanding OAuth2 flows
- More attack surface if misconfigured

**Best for**: SaaS products, enterprise apps, third-party integrations

---

### Option 4: Basic Auth (Not Recommended)

**How it works**: Username:password in every request header.

| Aspect | Assessment |
|--------|------------|
| **Complexity** | Very Low |
| **Security** | Poor - credentials sent every request |
| **Scalability** | Low |
| **User Experience** | Browser popup (ugly) |

**Not recommended** - Only mention for completeness. Credentials in every request is a security risk.

---

## Decision Matrix

| Criteria | API Keys | JWT | OAuth2+JWT |
|----------|----------|-----|------------|
| Implementation Time | 2-4 hours | 1-2 days | 3-5 days |
| Multi-user Support | ❌ | ✅ | ✅ |
| User Identity | ❌ | ✅ | ✅ |
| Third-party Login | ❌ | ❌ | ✅ |
| Stateless | ✅ | ✅ | ✅ |
| Complexity | Low | Medium | High |
| Fits Current Use Case | ✅ | ⚠️ | ❌ |

---

## Recommendation

### For Now: **API Keys** (Option 1)

**Rationale**:
1. This is a research tool, not a user-facing SaaS
2. Single user / small team use case
3. Already have rate limiting as second layer
4. Fastest path to production security
5. Can evolve to JWT later if needed

### Migration Path

```
Phase 1 (Now):     API Keys → Blocks unauthorized access
Phase 2 (Later):   JWT → When multi-user needed
Phase 3 (Maybe):   OAuth2 → If third-party integration required
```

---

## Implementation Checklist

If you choose **API Keys**:

- [ ] Add `API_KEY` to Settings as SecretStr
- [ ] Create API key validation dependency
- [ ] Add middleware or per-route protection
- [ ] Exempt `/health` endpoint from auth
- [ ] Update `.env.example` with API_KEY placeholder
- [ ] Document in API reference
- [ ] Add to deployment guide

If you choose **JWT**:

- [ ] Add User model to database
- [ ] Create AuthService class
- [ ] Add `/auth/login` endpoint
- [ ] Add `/auth/refresh` endpoint
- [ ] Create JWT validation dependency
- [ ] Add SECRET_KEY to settings
- [ ] Consider token blacklist for revocation

---

## References

- [FastAPI Security Tutorial](https://fastapi.tiangolo.com/tutorial/security/)
- [FastAPI OAuth2 + JWT](https://fastapi.tiangolo.com/tutorial/security/oauth2-jwt/)
- [Better Stack: Authentication with FastAPI](https://betterstack.com/community/guides/scaling-python/authentication-fastapi/)
- [TestDriven.io: FastAPI JWT Auth](https://testdriven.io/blog/fastapi-jwt-auth/)

---

## Related Issues

- [AP-002](AP-002-no-authorization.md) - Authorization/RBAC (depends on this)
- [AP-006](../completed/AP-006-no-rate-limiting.md) - Rate limiting (completed)
