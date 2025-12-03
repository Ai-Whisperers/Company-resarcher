"""
Backward compatibility shim for concurrency_manager module.

The concurrency_manager module has been moved to src/core/managers/.
This file re-exports everything for backward compatibility.
"""

from ..managers.concurrency_manager import *
