# Security & Compliance Backlog Items

### [SEC] API Key Rotation

**Priority:** Low
**Description:** Mechanism to rotate keys if one is exhausted or compromised.
**Acceptance Criteria:**

- [ ] Support multiple keys per provider in `Settings`.
- [ ] Implement round-robin or failover rotation strategy.

### [SEC] Data Anonymization

**Priority:** Low
**Description:** Remove PII from research outputs if necessary.
**Acceptance Criteria:**

- [ ] Implement `PIIScrubber` using `presidio` or regex.
- [ ] Scrub emails, phone numbers from public scrapes before saving.
