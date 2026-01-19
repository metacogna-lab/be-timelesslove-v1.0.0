"""
Site-wide warning filters for the backend test/runtime environment.
Ensures noisy third-party warnings don't obscure relevant signal.
"""

import warnings

warnings.filterwarnings(
    "ignore",
    message="Core Pydantic V1 functionality isn't compatible with Python 3.14 or greater.",
    category=UserWarning
)
