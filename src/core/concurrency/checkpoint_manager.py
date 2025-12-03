"""
Backward compatibility shim for checkpoint_manager module.

The checkpoint_manager module has been moved to src/core/managers/.
This file re-exports everything for backward compatibility.
"""

from ..managers.checkpoint_manager import *
