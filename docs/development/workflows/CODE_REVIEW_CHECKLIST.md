# Code Review Checklist

Use this checklist to conduct thorough and effective code reviews.

## 1. Code Structure & Design

- [ ] **Modularity**: Is the code broken down into small, reusable functions/classes?
- [ ] **Separation of Concerns**: Does each component have a single responsibility?
- [ ] **DRY (Don't Repeat Yourself)**: Is there any duplicated code that should be refactored?
- [ ] **KISS (Keep It Simple, Stupid)**: Is the solution overly complex? Can it be simplified?
- [ ] **File Organization**: Are files located in the correct directories?

## 2. Readability & Style

- [ ] **Naming Conventions**: Do variables, functions, and classes follow the project's naming conventions (e.g., snake_case for Python, camelCase for JS)?
- [ ] **Clarity**: Are variable names descriptive and meaningful?
- [ ] **Comments**: Are complex logic blocks explained with comments? (Avoid "what" comments, focus on "why").
- [ ] **Formatting**: Does the code follow the project's style guide (e.g., PEP 8, Prettier)?
- [ ] **Dead Code**: Is there any commented-out code or unused imports to remove?

## 3. Error Handling & Reliability

- [ ] **Input Validation**: Are function arguments and external inputs validated?
- [ ] **Exception Handling**: Are exceptions caught and handled appropriately? Avoid bare `except:` clauses.
- [ ] **Edge Cases**: Have edge cases and boundary conditions been considered?
- [ ] **Logging**: Is there adequate logging for debugging and monitoring?

## 4. Documentation

- [ ] **Docstrings**: Do public functions and classes have docstrings explaining purpose, args, and returns?
- [ ] **README**: If this is a new feature/module, is it documented in the README or relevant docs?
- [ ] **API Documentation**: If an API is modified, is the documentation updated?

## 5. Performance

- [ ] **Efficiency**: Are there any obvious performance bottlenecks (e.g., O(n^2) loops, unnecessary database queries)?
- [ ] **Resource Management**: Are resources (files, connections) properly closed/released?
- [ ] **Caching**: Is caching used effectively where appropriate?

## 6. Security

- [ ] **Sensitive Data**: Are secrets (API keys, passwords) excluded from the code?
- [ ] **Injection Prevention**: Is the code safe against injection attacks (SQL, XSS)?
- [ ] **Authorization**: are proper permission checks in place?

## 7. Testing

- [ ] **Unit Tests**: Are there unit tests for the new functionality?
- [ ] **Test Coverage**: Do tests cover happy paths and failure scenarios?
- [ ] **Integration Tests**: If applicable, are there integration tests?
