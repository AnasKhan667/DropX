"""
Backward-compatibility shim.

Permissions have moved to core.permissions.
Any code that still does `from DropX.permissions import IsDriver` will continue
to work. Update imports to `from core.permissions import …` when convenient.
"""
from core.permissions import IsDriver, IsVerifiedDriver, IsSender  # noqa: F401
