# CO-004: No Secret Rotation Support

## Status: OPEN - Architectural Decision Required

## Priority: High (downgraded from Critical)

---

## Current State

| Feature | Status |
|---------|--------|
| Settings cached via `@lru_cache()` | ✅ Implemented |
| `clear_settings()` to reset cache | ✅ Implemented |
| `SecretStr` for secure handling | ✅ Implemented |
| Automatic secret rotation | ❌ Not implemented |

**Location**: `src/core/config.py`

---

## The Problem

When API keys or credentials need to be rotated:

- Requires manual intervention (update env + restart or call clear_settings)
- No graceful transition between old and new secrets
- No automatic rotation on schedule
- May cause brief downtime during rotation

---

## Do You Need Automatic Secret Rotation?

### You DON'T need it if

- Small team / internal tool
- Secrets change rarely (quarterly or less)
- Brief downtime during rotation is acceptable
- No compliance requirements mandate it

### You DO need it if

- SOC 2 / PCI-DSS / HIPAA compliance
- Secrets must rotate frequently (daily/weekly)
- Zero-downtime rotation required
- Multiple applications share secrets

---

## Option Analysis

### Option 1: Manual Rotation with clear_settings() (Current)

**How it works**: Update env vars, call `clear_settings()`, new config loads.

| Aspect | Assessment |
|--------|------------|
| **Complexity** | Already implemented |
| **Cost** | Free |
| **Automation** | Manual |
| **Downtime** | Minimal (milliseconds) |

**Current flow**:

```python
# 1. Update environment variable
os.environ["OPENAI_API_KEY"] = "new-key-here"

# 2. Clear cached settings
from src.core.config import clear_settings
clear_settings()

# 3. Next request uses new key automatically
```

**Enhancement**: Add admin endpoint for triggering reload:

```python
@app.post("/admin/reload-config")
@require_admin
async def reload_config():
    clear_settings()
    return {"status": "Configuration reloaded"}
```

---

### Option 2: AWS Secrets Manager

**How it works**: Secrets stored in AWS, SDK fetches and caches them.

| Aspect | Assessment |
|--------|------------|
| **Complexity** | Medium |
| **Cost** | ~$0.40/secret/month + API calls |
| **Automation** | Built-in rotation lambdas |
| **Downtime** | Zero |

**Pros**:

- Native AWS integration (RDS, Lambda, etc.)
- Built-in rotation for common services
- IAM-based access control
- Audit logging included

**Cons**:

- AWS lock-in
- Cost scales with secret count
- Requires AWS infrastructure knowledge

**Best for**: AWS-native applications, RDS database credentials

```python
# Implementation sketch
import boto3
from functools import lru_cache

@lru_cache(maxsize=1)
def get_secrets_client():
    return boto3.client('secretsmanager')

def get_secret(secret_name: str) -> str:
    client = get_secrets_client()
    response = client.get_secret_value(SecretId=secret_name)
    return response['SecretString']

# Usage
openai_key = get_secret("company-researcher/openai-api-key")
```

---

### Option 3: HashiCorp Vault

**How it works**: Centralized secret management with dynamic secrets.

| Aspect | Assessment |
|--------|------------|
| **Complexity** | High |
| **Cost** | Free (self-hosted) or HCP pricing |
| **Automation** | Dynamic secrets, auto-rotation |
| **Downtime** | Zero |

**Pros**:

- Multi-cloud / hybrid support
- Dynamic secrets (generated on-demand, auto-expire)
- Fine-grained access policies
- Excellent audit logging

**Cons**:

- Significant operational overhead
- Requires Vault cluster management
- Learning curve for policies

**Best for**: Multi-cloud, enterprise, strict compliance

```python
# Implementation sketch
import hvac

client = hvac.Client(url='https://vault.example.com')
client.token = os.getenv('VAULT_TOKEN')

def get_secret(path: str) -> dict:
    secret = client.secrets.kv.v2.read_secret_version(path=path)
    return secret['data']['data']

# Usage
secrets = get_secret('company-researcher/api-keys')
openai_key = secrets['openai']
```

---

### Option 4: Doppler / Infisical (Modern Alternatives)

**How it works**: Cloud-native secret management with simple SDK.

| Aspect | Assessment |
|--------|------------|
| **Complexity** | Low |
| **Cost** | Free tier available |
| **Automation** | Sync + rotation support |
| **Downtime** | Zero |

**Pros**:

- Developer-friendly UX
- Simple SDK integration
- Environment sync (dev/staging/prod)
- Free tier for small teams

**Cons**:

- Newer, less battle-tested
- Limited enterprise features
- External dependency

**Best for**: Startups, small teams wanting simplicity

```python
# Doppler example
import doppler

config = doppler.get_config()
openai_key = config['OPENAI_API_KEY']
```

---

### Option 5: Dual-Key Support (Zero-Downtime DIY)

**How it works**: Support both old and new keys during transition period.

| Aspect | Assessment |
|--------|------------|
| **Complexity** | Low-Medium |
| **Cost** | Free |
| **Automation** | Manual rotation, zero downtime |
| **Downtime** | Zero |

**Implementation**:

```python
class Settings(BaseSettings):
    OPENAI_API_KEY: Optional[SecretStr] = None
    OPENAI_API_KEY_BACKUP: Optional[SecretStr] = None  # For rotation

    def get_openai_keys(self) -> list[str]:
        """Return all valid API keys for fallback."""
        keys = []
        if self.OPENAI_API_KEY:
            keys.append(self.OPENAI_API_KEY.get_secret_value())
        if self.OPENAI_API_KEY_BACKUP:
            keys.append(self.OPENAI_API_KEY_BACKUP.get_secret_value())
        return keys
```

**Rotation flow**:

1. Add new key to `OPENAI_API_KEY_BACKUP`
2. Reload config
3. Both keys now work
4. Move new key to `OPENAI_API_KEY`, remove backup
5. Revoke old key

---

## Decision Matrix

| Criteria | Manual | AWS SM | Vault | Doppler | Dual-Key |
|----------|--------|--------|-------|---------|----------|
| Implementation Time | 0 | 4-8 hours | 1-2 days | 2-4 hours | 2-4 hours |
| Operational Cost | Free | ~$5/mo | Free-$$ | Free-$$ | Free |
| Zero-Downtime | ⚠️ | ✅ | ✅ | ✅ | ✅ |
| Auto-Rotation | ❌ | ✅ | ✅ | ✅ | ❌ |
| Multi-Cloud | ✅ | ❌ | ✅ | ✅ | ✅ |
| Complexity | None | Medium | High | Low | Low |
| Fits Current Use Case | ✅ | ⚠️ | ❌ | ⚠️ | ✅ |

---

## Recommendation

### For Now: **Keep Current + Add Reload Endpoint**

**Rationale**:

1. `clear_settings()` already provides manual rotation capability
2. No compliance requirements currently mandate auto-rotation
3. Adding external dependencies increases complexity
4. Current solution has near-zero downtime (cache clear is instant)

**Suggested Enhancement**:

```python
# Add to app.py
@app.post("/admin/reload-config")
async def reload_config(api_key: str = Depends(verify_api_key)):
    """Reload configuration from environment. Requires API key auth."""
    from ..core.config import clear_settings
    clear_settings()
    logger.info("Configuration reloaded via admin endpoint")
    return {"status": "ok", "message": "Configuration reloaded"}
```

### When to Revisit

Implement AWS Secrets Manager or Vault when:

- SOC 2 audit requires automated rotation
- Managing 10+ secrets across multiple services
- Need to share secrets across multiple applications
- Database credentials need automatic rotation

---

## Implementation Checklist

If you choose **Manual + Reload Endpoint**:

- [ ] Add `/admin/reload-config` endpoint
- [ ] Protect endpoint with API key auth
- [ ] Add logging for config reloads
- [ ] Document rotation procedure

If you choose **AWS Secrets Manager**:

- [ ] Create secrets in AWS console
- [ ] Add boto3 to dependencies
- [ ] Create SecretManager wrapper class
- [ ] Update Settings to fetch from AWS
- [ ] Configure IAM permissions
- [ ] Set up rotation lambdas (optional)

If you choose **Dual-Key Support**:

- [ ] Add `*_BACKUP` fields to Settings
- [ ] Update AI client to try backup keys
- [ ] Document rotation procedure
- [ ] Add key validation on startup

---

## References

- [OWASP Secrets Management Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html)
- [AWS Secrets Manager Best Practices](https://docs.aws.amazon.com/secretsmanager/latest/userguide/best-practices.html)
- [HashiCorp Vault Python Client](https://hvac.readthedocs.io/)
- [Infisical Python SDK](https://infisical.com/docs/sdks/languages/python)

---

## Related Issues

- [AP-001](../api/AP-001-no-authentication.md) - Authentication (protects reload endpoint)
