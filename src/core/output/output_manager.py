"""
Backward compatibility shim for output_manager module.

The output_manager module has been moved to src/core/managers/.
This file re-exports everything for backward compatibility.
"""

from ..managers.output_manager import *
