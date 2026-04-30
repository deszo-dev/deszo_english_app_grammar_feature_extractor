from __future__ import annotations

MODAL_LEMMAS = frozenset(
    {"can", "could", "may", "might", "must", "shall", "should", "will", "would"}
)
ABILITY_MODALS = frozenset({"can", "could"})
PERMISSION_MODALS = frozenset({"may"})
POSSIBILITY_MODALS = frozenset({"might"})
OBLIGATION_MODALS = frozenset({"must"})
ADVICE_MODALS = frozenset({"should"})
PREDICTION_MODALS = frozenset({"will", "shall"})
CONDITIONAL_MODALS = frozenset({"would"})
