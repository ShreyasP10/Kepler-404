"""Kepler-404 web server entry point.

Usage:
    python app.py

All logic lives in the `kepler/` package. This file is just a thin launcher.
"""

from kepler.app import create_app

if __name__ == "__main__":
    app = create_app()
    app.run(host=app.config["KEPLER_SETTINGS"].host,
            port=app.config["KEPLER_SETTINGS"].port,
            debug=app.config["KEPLER_SETTINGS"].debug)
