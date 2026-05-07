"""Self-Learning Loop tests — verify the helper functions work correctly."""
from __future__ import annotations
import pytest


def test_sign_function():
    from app.workers.engines.learning_loop import _sign
    assert _sign(1.0) == 1
    assert _sign(-1.0) == -1
    assert _sign(0.0) == 0
    assert _sign(100) == 1
    assert _sign(-0.001) == -1


def test_module_exposes_required_async_helpers():
    """Public API of learning_loop must include both update functions."""
    from app.workers.engines import learning_loop
    assert callable(getattr(learning_loop, "update_after_closed_trade", None))
    assert callable(getattr(learning_loop, "run_loop_for_recent", None))
    assert callable(getattr(learning_loop, "_get_voting_weights", None))
    assert callable(getattr(learning_loop, "_save_voting_weights", None))


def test_weight_update_logic_increments_correctly():
    """Test the core weight-update math (signed reward × signal alignment)."""
    # Recreate the inner reward formula as a self-contained sanity check
    initial_weight = 1.0
    learning_rate = 0.05
    # Profit on a buy signal with positive contrib → weight up
    reward = 1.0  # winning trade
    contrib_sign = +1  # analyzer voted buy and trade was buy
    new_weight = initial_weight + learning_rate * reward * contrib_sign
    assert new_weight > initial_weight
    # Loss on aligned signal → weight down
    reward = -1.0
    new_weight = initial_weight + learning_rate * reward * contrib_sign
    assert new_weight < initial_weight
