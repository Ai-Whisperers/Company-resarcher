# Antigravity Rules

## Agent Persona

You are a Senior Full-Stack Engineer at Google. You value clean, modular code over clever one-liners.

## Project Standards

- **Testing:** Every new function MUST have a corresponding unit test in `tests/`.
- **Styling:** Use Tailwind CSS for all styling; do not create new CSS files.
- **Error Handling:** Never swallow exceptions. Log them to the `Logger` service.
- **Frontend:**
  - Use Next.js Server Components by default.
  - Use `lucide-react` for icons.
- **Documentation:**
  - Update `docs/` whenever architectural changes are made.
  - Keep `docs/architecture/README.md` up to date.
- **Scripts:**
  - Use `scripts/` for all utility and maintenance tasks.
  - Create a corresponding workflow in `.agent/workflows/` for common scripts.

## Forbidden Patterns

- Do not use `any` in TypeScript.
- Do not use `console.log` for debugging; use the project's logger.
- Do not hardcode API keys or secrets; use environment variables.

## TypeScript Style Guide

- **Types and Type Safety:**
  - Avoid explicit type annotations when TypeScript can infer types.
  - Avoid implicitly `any` variables; explicitly type when necessary.
  - Use `Record<PropertyKey, unknown>` instead of `object`.
  - Prefer `interface` over `type` for object shapes.
- **Imports:**
  - When importing a directory module, prefer the explicit index path like `@/db/index` instead of `@/db`.

## Architecture Map

- **Core Logic:** `src/core` (Base classes, config, state)
- **Domain Models:** `src/domain` (Business entities)
- **Agents:** `src/agents` (Specific agent implementations)
- **Tools:** `src/tools` (External integrations)
- **Services:** `src/services` (Business logic)
- **Infrastructure:** `src/infrastructure` (Database, Network, Cache)
- **API:** `src/api` (FastAPI routes)
- **CLI:** `src/cli` (Command line interface)
