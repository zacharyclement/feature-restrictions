import time
from unittest.mock import MagicMock


def test_is_rule_disabled_via_tripwire(tripwire_manager, mock_redis):
    """
    Test the is_rule_disabled_via_tripwire method.
    """
    mock_redis.hget.return_value = "1"
    assert tripwire_manager.is_rule_disabled_via_tripwire("test_rule") is True
    mock_redis.hget.assert_called_with("tripwire:states", "test_rule")

    mock_redis.hget.return_value = "0"
    assert tripwire_manager.is_rule_disabled_via_tripwire("test_rule") is False


def test_apply_tripwire_if_needed(tripwire_manager, mock_redis):
    """
    Test the apply_tripwire_if_needed method.
    """
    # Mock Redis responses for affected users and count
    current_time = time.time()
    mock_redis.hgetall.return_value = {"user_1": str(current_time - 100)}
    mock_redis.hlen.return_value = 1

    # Adjust the threshold
    tripwire_manager.threshold = 0.1  # 10%

    # Act: Apply the tripwire
    tripwire_manager.apply_tripwire_if_needed("test_rule", "user_2", 10)

    # Validate calls to hset and hgetall
    affected_users_key = "tripwire:affected_users:test_rule"
    assert any(
        call.args[0] == affected_users_key and call.args[1] == "user_2"
        for call in mock_redis.hset.call_args_list
    ), "Expected hset call with correct arguments not found."

    # Validate tripwire state update
    mock_redis.hset.assert_any_call("tripwire:states", "test_rule", "1")


def test_clear_rules(tripwire_manager, mock_redis):
    """
    Test the clear_rules method.
    """
    mock_redis.keys.return_value = ["tripwire:affected_users:test_rule"]
    tripwire_manager.clear_rules()

    mock_redis.delete.assert_any_call("tripwire:states")
    mock_redis.delete.assert_any_call("tripwire:affected_users:test_rule")


def test_get_tripwire_state(tripwire_manager, mock_redis):
    """
    Test the get_tripwire_state method.
    """
    mock_redis.hget.return_value = "1"
    assert tripwire_manager.get_tripwire_state("test_rule") is True

    mock_redis.hget.return_value = "0"
    assert tripwire_manager.get_tripwire_state("test_rule") is False


def test_get_affected_users(tripwire_manager, mock_redis):
    """
    Test the get_affected_users method.
    """
    # Mock Redis response
    timestamp = time.time()
    mock_redis.hgetall.return_value = {"user_1": f"{timestamp}"}

    # Act
    affected_users = tripwire_manager.get_affected_users("test_rule")

    # Validate
    mock_redis.hgetall.assert_called_with("tripwire:affected_users:test_rule")
    assert "user_1" in affected_users
    assert (
        abs(float(affected_users["user_1"]) - timestamp) < 0.1
    ), "Timestamps do not match within tolerance."


def test_get_disabled_rules(tripwire_manager, mock_redis):
    """
    Test the get_disabled_rules method.
    """
    mock_redis.hgetall.return_value = {"test_rule": "1", "another_rule": "0"}
    disabled_rules = tripwire_manager.get_disabled_rules()
    assert disabled_rules == {"test_rule": "1", "another_rule": "0"}
    mock_redis.hgetall.assert_called_with("tripwire:states")
