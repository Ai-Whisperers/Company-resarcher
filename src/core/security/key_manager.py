"""
Backward compatibility shim for key_manager module.

The key_manager module has been moved to src/core/managers/.
This file re-exports everything for backward compatibility.
"""

from ..managers.key_manager import *
