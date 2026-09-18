"""Optional integrations with external systems.

Nothing in the core imports a module from here at import time: an integration is loaded
lazily, where it is used, and it must never be able to take the server down.
"""
