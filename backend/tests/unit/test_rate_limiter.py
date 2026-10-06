"""Unit tests for the sliding-window rate limiter."""
from unittest.mock import patch

from app.core.middleware.rate_limit import (
    WINDOW_SECONDS,
    InMemorySlidingWindow,
)


def test_allows_up_to_limit_then_denies():
    window = InMemorySlidingWindow()
    for _ in range(5):
        allowed, retry_after = window.allow("client-a", 5)
        assert allowed
        assert retry_after == 0

    allowed, retry_after = window.allow("client-a", 5)
    assert not allowed
    assert retry_after >= 1


def test_keys_are_independent():
    window = InMemorySlidingWindow()
    for _ in range(3):
        assert window.allow("client-a", 3)[0]
    assert not window.allow("client-a", 3)[0]
    # Different key keeps its own budget
    assert window.allow("client-b", 3)[0]


def test_window_expiry_releases_budget():
    window = InMemorySlidingWindow()
    fake_now = [1000.0]
    with patch(
        "app.core.middleware.rate_limit.time.monotonic",
        side_effect=lambda: fake_now[0],
    ):
        assert window.allow("client-a", 1)[0]
        assert not window.allow("client-a", 1)[0]

        # Advance past the window: the old hit expires out
        fake_now[0] += WINDOW_SECONDS + 1
        allowed, retry_after = window.allow("client-a", 1)
        assert allowed
        assert retry_after == 0


def test_reset_clears_all_state():
    window = InMemorySlidingWindow()
    assert window.allow("client-a", 1)[0]
    assert not window.allow("client-a", 1)[0]
    window.reset()
    assert window.allow("client-a", 1)[0]
