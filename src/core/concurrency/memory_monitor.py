"""
Backward compatibility shim for memory_monitor module.

The memory_monitor module has been moved to src/core/managers/.
This file re-exports everything for backward compatibility.
"""

from ..managers.memory_monitor import *
