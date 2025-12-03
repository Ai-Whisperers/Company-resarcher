# 🧪 Testing Improvements

This document outlines improvements to the testing infrastructure. The goal is to move beyond simple unit tests to a comprehensive quality assurance strategy that includes integration, property-based, load, and contract testing.

## TEST-1: Integration Test Framework (6h)

### Concept & Rationale

Unit tests mock everything, which means they don't catch issues with database queries, Redis locks, or actual API interactions.

**The Improvement:**
Build a robust **Integration Test Framework** using `testcontainers`.

- **Real Dependencies:** Spin up ephemeral Docker containers for PostgreSQL and Redis during the test run. This ensures tests run against the real database engine, not an in-memory SQLite substitute that behaves differently.
- **Isolation:** Each test run gets a fresh environment, preventing flaky tests caused by shared state.
- **End-to-End Flows:** Test complete user flows (e.g., "Submit Research -> Save to DB -> Retrieve Result") via the API client.

### Key Implementation Details

- Create a `IntegrationTestBase` class that handles container lifecycle.
- Use `pytest` fixtures to inject database connections and API clients.
- Reference: `tests/integration/framework.py` (Proposed)

## TEST-2: Mock Provider Framework (4h)

### Concept & Rationale

Testing against real AI and Search APIs is slow, expensive, and non-deterministic. You need a way to simulate these providers reliably.

**The Improvement:**
Develop a **Mock Provider Framework** (`MockProviderFactory`).

- **Determinism:** Define exact responses for specific prompts ("When asked for 'SWOT', return 'Strengths...'").
- **Simulation:** Simulate real-world conditions like latency (sleep before returning) and random errors (throw exceptions) to test resilience.
- **Assertions:** Assert that the provider was called with the expected prompts and parameters (`assert_called_with`).

### Key Implementation Details

- Implement mock classes that adhere to the `AIClientProtocol`.
- Allow tests to inject specific behaviors (success, failure, timeout) on the fly.
- Reference: `tests/mocks/providers.py` (Proposed)

## TEST-3: Property-Based Testing (4h)

### Concept & Rationale

Example-based tests (checking `add(1, 2) == 3`) only test the scenarios you can think of. They often miss edge cases like empty strings, huge numbers, or weird unicode characters.

**The Improvement:**
Adopt **Property-Based Testing** using `hypothesis`.

- **Invariants:** Define properties that should _always_ be true (e.g., "Rate limiter tokens should never be negative", "Sanitized output should never contain script tags").
- **Generation:** The test framework automatically generates thousands of random inputs (fuzzing) to try and break these properties.
- **Shrinking:** When a failure is found, the framework finds the smallest possible input that reproduces the error.

### Key Implementation Details

- Write tests for critical logic: validators, rate limiters, caching strategies.
- Reference: `tests/property/test_validators.py` (Proposed)

## TEST-4: Load Testing Setup (6h)

### Concept & Rationale

You don't want to discover performance bottlenecks when users complain. You need to know the system's breaking point beforehand.

**The Improvement:**
Establish a **Load Testing** suite using `locust`.

- **User Simulation:** Define "User" classes that simulate real behavior (e.g., "ResearchUser" who submits a query, waits, then reads the report).
- **Scenarios:** Test different mixes of traffic (e.g., 80% cache hits, 20% heavy research).
- **Thresholds:** Define pass/fail criteria based on latency percentiles (e.g., "99% of requests must be under 2 seconds").

### Key Implementation Details

- Create a `locustfile.py` defining the user behaviors.
- Automate load tests in CI/CD to catch performance regressions.
- Reference: `tests/load/locustfile.py` (Proposed)

## TEST-5: Contract Testing (4h)

### Concept & Rationale

In a microservices or frontend-backend architecture, breaking changes in the API schema can cause failures in consumers.

**The Improvement:**
Implement **Contract Testing** using `pact`.

- **Consumer-Driven:** The consumer (e.g., the frontend or another service) defines what it expects from the API (the "contract").
- **Verification:** The provider (Company Researcher API) verifies that it honors these contracts.
- **Safety:** Prevents deploying backend changes that would break the frontend.

### Key Implementation Details

- Define contracts for key endpoints (`/api/research`).
- Run verification as part of the build process.
- Reference: `tests/contracts/test_api_contracts.py` (Proposed)
