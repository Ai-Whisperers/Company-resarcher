# SEC-006: Vault Unencrypted Storage

## Priority: Medium
## Category: Security
## Status: Backlog

## Summary

The Vault stores research data in plain JSON files without encryption, making sensitive business intelligence accessible to anyone with file system access.

## Affected Files

| File | Line | Issue |
|------|------|-------|
| `src/core/vault.py` | 28 | Hardcoded path `data/vault` |
| `src/core/vault.py` | 70-97 | Plain JSON file storage |

## Current Code

```python
# src/core/vault.py
VAULT_PATH = "data/vault"

async def store_report(self, company_name: str, content: str, metadata: dict):
    filepath = Path(VAULT_PATH) / f"{company_name}.json"
    # Plain text JSON, readable by anyone
    with open(filepath, 'w') as f:
        json.dump(data, f)
```

## Risk

- Research data exposed to unauthorized users
- Competitive intelligence leakage
- Compliance issues (GDPR, SOC2)
- No access control on files

## Proposed Fix

### 1. Encrypted File Storage

```python
from cryptography.fernet import Fernet
import os

class EncryptedVault:
    def __init__(self):
        self.key = os.getenv("VAULT_ENCRYPTION_KEY")
        if not self.key:
            raise ValueError("VAULT_ENCRYPTION_KEY not configured")
        self.fernet = Fernet(self.key.encode())

    async def store_report(self, company_name: str, content: str, metadata: dict):
        data = json.dumps({"content": content, "metadata": metadata})
        encrypted = self.fernet.encrypt(data.encode())

        filepath = self._get_filepath(company_name)
        async with aiofiles.open(filepath, 'wb') as f:
            await f.write(encrypted)

    async def retrieve_report(self, company_name: str) -> dict:
        filepath = self._get_filepath(company_name)
        async with aiofiles.open(filepath, 'rb') as f:
            encrypted = await f.read()

        decrypted = self.fernet.decrypt(encrypted)
        return json.loads(decrypted.decode())

    def _get_filepath(self, company_name: str) -> Path:
        # Sanitize company name to prevent path traversal
        safe_name = re.sub(r'[^\w\-]', '_', company_name)
        return Path(os.getenv("VAULT_PATH", "data/vault")) / f"{safe_name}.enc"
```

### 2. Database-Backed Storage

```python
from sqlalchemy import Column, String, LargeBinary, DateTime
from sqlalchemy.orm import declarative_base

class VaultEntry(Base):
    __tablename__ = "vault_entries"

    id = Column(String, primary_key=True)
    company_name = Column(String, index=True)
    encrypted_content = Column(LargeBinary)  # Encrypted at rest
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)
```

### 3. Access Control

```python
class VaultAccessControl:
    """Role-based access to vault entries."""

    def can_read(self, user_id: str, company_name: str) -> bool:
        # Check user permissions
        pass

    def can_write(self, user_id: str, company_name: str) -> bool:
        # Check user permissions
        pass
```

## Implementation Tasks

- [ ] Add `cryptography` library to dependencies
- [ ] Implement encrypted file storage
- [ ] Add key rotation mechanism
- [ ] Create access control layer
- [ ] Migrate existing vault data
- [ ] Add audit logging for vault access
- [ ] Document encryption configuration

## Success Criteria

- All vault data encrypted at rest
- Encryption key externally managed
- Access control enforced
- Audit trail for all access
- Key rotation procedure documented
