"""API package for the seismic risk prototype.

Avoid importing the FastAPI application at package import time.
This keeps module imports side-effect free for repository and runtime tooling.
"""

__all__: list[str] = []
