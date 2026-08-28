"""
Challenge phrase generation for enrollment liveness checks.

DESIGN.md §4.2 requires a server-generated *random* challenge phrase,
not a fixed passphrase, to resist replay of a recorded/cloned enrollment
attempt. Uses `secrets` (not `random`) for cryptographic randomness —
a predictable challenge defeats the entire anti-replay purpose.
"""

import secrets

# Curated word list — common, unambiguous, easy to pronounce across
# Indian languages/accents (DESIGN.md §4.4). Kept short for the
# reference implementation; a production list would be larger and
# validated by the linguistics/UX team.
_WORD_LIST = [
    "mountain", "crystal", "seven", "umbrella", "garden", "silver",
    "dolphin", "harvest", "piano", "compass", "thunder", "lantern",
    "marble", "falcon", "river", "copper", "sunset", "anchor",
    "velvet", "bridge", "ocean", "timber", "rocket", "forest",
    "candle", "pepper", "violet", "basket", "mirror", "arrow",
    "jacket", "ladder", "puzzle", "ribbon", "socket", "beacon",
    "filter", "magnet", "pebble", "tunnel", "breeze", "castle",
    "feather", "helmet", "island", "kernel", "nectar", "orchid",
    "quartz", "saddle", "temple", "walnut", "zenith", "bottle",
    "desert", "engine", "glacier", "harbor", "jigsaw", "kitten",
]

# Number of words per challenge phrase. 5 words gives ~28 bits of
# entropy against the 60-word list, which is sufficient for anti-replay
# (the attacker would need to have pre-recorded the exact combination).
_PHRASE_LENGTH = 5


def generate_challenge() -> str:
    """
    Generate a random challenge phrase for a liveness check.

    Returns a string of space-separated words chosen uniformly at random
    (with replacement) from the word list, using cryptographic randomness.
    """
    words = [secrets.choice(_WORD_LIST) for _ in range(_PHRASE_LENGTH)]
    return " ".join(words)
