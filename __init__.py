from __future__ import annotations

from pathlib import Path

_INNER_PACKAGE = Path(__file__).resolve().parent / "grammar_feature_extractor"
if str(_INNER_PACKAGE) not in __path__:
    __path__.append(str(_INNER_PACKAGE))

from .grammar_feature_extractor import *  # noqa: F401,F403
from .grammar_feature_extractor import __all__  # noqa: F401
