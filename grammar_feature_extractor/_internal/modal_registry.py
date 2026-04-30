from __future__ import annotations

MODAL_LEMMAS = frozenset(
    {"can", "could", "may", "might", "must", "shall", "should", "will", "would"}
)
ABILITY_MODALS = frozenset({"can", "could"})
OBLIGATION_MODALS = frozenset({"must", "should"})
PREDICTION_MODALS = frozenset({"will", "would", "shall"})
