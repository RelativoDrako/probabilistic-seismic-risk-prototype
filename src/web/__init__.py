"""Web package for the seismic risk prototype.

Avoid importing the Streamlit app at package import time.
This keeps module imports side-effect free and prevents recursive imports.
"""

__all__: list[str] = []
