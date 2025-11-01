"""Constants for the hyperway package.

This module contains package-wide constants to avoid magic strings
and prevent circular import issues.
"""

# Stepper initiation mode constants
INITIATE_DISTRIBUTED = 'distributed'  # Edge-centric: call node once per connection
INITIATE_UNIFIED = 'unified'          # Node-centric: call node once, fan out to connections
