"""
Named rate-limit strings applied via @limiter.limit(...) on specific
routes (see app/routes/auth_routes.py for usage). Centralized here so
limits are easy to tune from one place instead of hunting through routes.
"""

LOGIN_RATE_LIMIT = "5 per minute"
REGISTER_RATE_LIMIT = "3 per minute"
REFRESH_RATE_LIMIT = "10 per minute"
FACE_VERIFY_RATE_LIMIT = "10 per minute"        # used in Part 5
VOTE_RATE_LIMIT = "3 per minute"                 # used in Part 7
