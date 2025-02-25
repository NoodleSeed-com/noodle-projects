"""
SQLAlchemy event listeners for model validation and lifecycle hooks.
"""
from sqlalchemy import event

# Note: The automatic creation of initial versions has been moved to the
# create_project route handler, which explicitly calls versions.create_initial_version.
# This avoids duplicate version creation and provides better control over the process.
