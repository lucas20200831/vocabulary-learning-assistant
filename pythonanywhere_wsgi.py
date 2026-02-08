# ============================================================================
# PythonAnywhere WSGI Configuration for Vocabulary Learning Assistant
# ============================================================================
# Place this file in /home/lucas2002/mysite/ on PythonAnywhere
# ============================================================================

import sys
import os

# Add project directory to sys.path
project_home = '/home/lucas2002/mysite'
if project_home not in sys.path:
    sys.path.insert(0, project_home)

# Set environment variables
os.environ['FLASK_ENV'] = 'production'

# Import the Flask app
from flask_app import app

# The application object used by PythonAnywhere's WSGI handler
application = app
