# MEDIUM: Exception Handling Swallows All Errors

## Severity: Medium
## Files: Multiple (`src/agents/specialists.py`, others)

## Problem

Many places catch exceptions but silently continue:

```python
# specialists.py:46-47
except Exception as e:
    logger.error(f"Error fetching SEC data: {e}")
    # Silently continues - no re-raise, no error tracking

# Similar patterns in other files
```

## Impact

- Errors are logged but not tracked
- No visibility into failure rates
- Debugging is difficult
- Silent degradation - users don't know data is incomplete
- No way to retry failed operations

## Solution

Option 1: Track errors in state:

```python
class ResearchState(BaseModel):
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)

# In agent:
try:
    sec_content = self.sec_tool.get_latest_10k_content(company.name)
except Exception as e:
    logger.error(f"Error fetching SEC data: {e}")
    # Track the error
    return ResearchPhaseResult(
        phase_name=self.agent_name,
        errors=[f"SEC data unavailable: {e}"],
        ...
    )
```

Option 2: Use custom exceptions with context:

```python
class DataSourceError(Exception):
    def __init__(self, source: str, message: str):
        self.source = source
        self.message = message
        super().__init__(f"{source}: {message}")

# Usage:
try:
    sec_content = self.sec_tool.get_latest_10k_content(company.name)
except Exception as e:
    raise DataSourceError("SEC", str(e)) from e
```

Option 3: Return partial results with status:

```python
@dataclass
class DataResult:
    success: bool
    data: Any
    error: Optional[str] = None

def get_sec_data(company_name: str) -> DataResult:
    try:
        content = self.sec_tool.get_latest_10k_content(company_name)
        return DataResult(success=True, data=content)
    except Exception as e:
        return DataResult(success=False, data=None, error=str(e))
```

## Testing

After fix:
1. Force an error in data fetching
2. Verify error is tracked/reported
3. Verify error appears in final report or status
