"""
Kepler-404
==========

AI-driven super-resolution & colorization of Landsat 9 TIR imagery.

Public API:
    from kepler import create_app, Pipeline, Settings, InferenceResult
"""

__version__ = "1.0.0"
__all__ = [
    "__version__",
    "Settings",
    "Pipeline",
    "InferenceResult",
    "create_app",
    "main",  # CLI entry
]


def __getattr__(name):  # PEP 562 — lazy public exports to avoid import cycles
    if name == "Settings":
        from .config import Settings
        return Settings
    if name == "InferenceResult":
        from .models import InferenceResult
        return InferenceResult
    if name == "Pipeline":
        from .pipeline import Pipeline
        return Pipeline
    if name == "create_app":
        from .app import create_app
        return create_app
    if name == "main":
        from .cli import main
        return main
    raise AttributeError(f"module 'kepler' has no attribute {name!r}")


def __dir__():  # PEP 562 — make lazy exports visible to IDEs / dir()
    return sorted(__all__)
