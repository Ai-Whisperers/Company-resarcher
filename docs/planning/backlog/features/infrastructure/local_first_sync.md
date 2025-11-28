# Feature: Local-First Sync

## Source

- **Repository:** `lobehub/lobe-chat`
- **File:** `src/services/sync.ts`

## Description

Sync agent data (chats, settings) between devices (e.g., Laptop <-> Desktop) without relying on a central SaaS server.

## Implementation Details

1.  **P2P Sync:** Use WebRTC or a local relay (like YJS).
2.  **CRDTs:** Use Conflict-free Replicated Data Types to merge changes from multiple devices.
3.  **Cloud Storage:** Optional backup to S3/iCloud/Google Drive.

## Code Reference

```python
# Concept: Use a library like py-crdt
doc = Doc()
doc["chat"] = Text("Hello")
```
