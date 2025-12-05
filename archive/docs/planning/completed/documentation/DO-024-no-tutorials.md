# DO-024: No Step-by-Step Tutorials

**Priority**: Low
**Category**: Documentation
**Status**: Open
**Effort**: Large (4-8 hours)

## Problem

No guided tutorials exist for common use cases and learning paths.

## Impact

- Steep learning curve for new users
- Users don't discover full capabilities
- Common patterns not demonstrated
- Support burden increased

## Tutorials Needed

### Beginner Tutorials
1. **Your First Research** (30 min)
   - Setting up environment
   - Running a basic research task
   - Understanding the output

2. **Understanding Reports** (20 min)
   - Report structure
   - Reading financial data
   - Interpreting insights

### Intermediate Tutorials
3. **Using the REST API** (45 min)
   - Starting research via API
   - Polling for results
   - Error handling
   - Building a simple client

4. **Customizing Research** (60 min)
   - Configuring different LLM providers
   - Using local models (Ollama)
   - Adjusting research parameters

### Advanced Tutorials
5. **Creating Custom Agents** (90 min)
   - Understanding BaseAgent
   - Implementing a new specialist
   - Integrating with the workflow

6. **Adding New Tools** (60 min)
   - Tool interface
   - Implementing a data source
   - Testing and integration

7. **Deploying to Production** (60 min)
   - Docker setup
   - Environment configuration
   - Monitoring and logging

## Tutorial Template

```markdown
# Tutorial: [Title]

**Time**: X minutes
**Level**: Beginner/Intermediate/Advanced
**Prerequisites**: List prerequisites

## What You'll Learn
- Outcome 1
- Outcome 2

## Before You Start
- Setup requirements
- Required accounts/keys

## Step 1: [First Step]
Description of what to do...

```code
example code
```

**Expected Result**: What user should see

## Step 2: [Second Step]
...

## Troubleshooting
Common issues and solutions

## Next Steps
- Link to related tutorials
- Link to reference docs
```

## Solution

Create `docs/tutorials/` directory with progressive tutorials.

## Acceptance Criteria

- [ ] At least 3 tutorials created
- [ ] Beginner path defined
- [ ] Tutorials tested and working
- [ ] Code examples runnable
