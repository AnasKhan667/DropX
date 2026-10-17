"""
Backward-compatibility shim.

Settings have moved to the `config/` package:
    - config.base  → shared settings
    - config.dev   → local development
    - config.test  → pytest / CI
    - config.prod  → production

This module re-exports the dev settings so any tooling that still
references `DropX.settings` continues to work for one release.
Delete after the team has fully migrated.
"""

from config.dev import *  # noqa: F401, F403
