import time
from unittest.mock import MagicMock


def test_is_rule_disabled_via_tripwire(tripwire_manager, mock_redis):
    """
    Test the is_rule_disabled_via_tripwire method.
    """
    mock_redis["tripwire"].hget.return_value = "1"
    assert tripwire_manager.is_rule_disabled_via_tripwire("test_rule") is True
    mock_redis["tripwire"].hget.assert_called_with("tripwire:states", "test_rule")

    mock_redis["tripwire"].hget.return_value = "0"
    assert tripwire_manager.is_rule_disabled_via_tripwire("test_rule") is False


def test_apply_tripwire_if_needed(tripwire_manager, mock_redis):
    """
    Test the apply_tripwire_if_needed method.
    """
    # Mock Redis responses for affected users and count
    current_time = time.time()
    mock_redis["tripwire"].hgetall.return_value = {"user_1": str(current_time - 100)}
    mock_redis["tripwire"].hlen.return_value = 1

    # Adjust the threshold
    tripwire_manager.threshold = 0.1  # 10%

    # Act: Apply the tripwire
    tripwire_manager.apply_tripwire_if_needed("test_rule", "user_2", 10)

    # Validate calls to hset and hgetall
    affected_users_key = "tripwire:affected_users:test_rule"
    assert any(
        call.args[0] == affected_users_key and call.args[1] == "user_2"
        for call in mock_redis["tripwire"].hset.call_args_list
    ), "Expected hset call with correct arguments not found."

    # Validate tripwire state update
    mock_redis["tripwire"].hset.assert_any_call("tripwire:states", "test_rule", "1")


def test_get_disabled_rules(tripwire_manager, mock_redis):
    """
    Test the get_disabled_rules method.
    """
    mock_redis["tripwire"].hgetall.return_value = {
        "test_rule": "1",
        "another_rule": "0",
    }
    disabled_rules = tripwire_manager.get_disabled_rules()
    assert disabled_rules == {"test_rule": "1", "another_rule": "0"}
    mock_redis["tripwire"].hgetall.assert_called_with("tripwire:states")


def test_apply_tripwire_if_needed_no_expired_users(tripwire_manager, mock_redis):
    """
    Test apply_tripwire_if_needed when there are no expired users.
    Ensures no hdel call occurs for expired users.
    """
    current_time = time.time()
    # Existing user still within the time window
    mock_redis["tripwire"].hgetall.return_value = {"user_1": str(current_time - 100)}
    mock_redis["tripwire"].hlen.return_value = 2  # 2 affected users
    mock_redis["tripwire"].hget.return_value = "0"  # rule currently enabled
    tripwire_manager.threshold = 0.5  # 50%

    # With total_users = 10 and 2 affected, percentage = 20%, below threshold
    tripwire_manager.apply_tripwire_if_needed("test_rule", "user_2", 10)

    mock_redis["tripwire"].hgetall.assert_called_once()
    # No expired users removed
    mock_redis["tripwire"].hdel.assert_not_called()
    # Since 20% < 50%, rule stays enabled
    mock_redis["tripwire"].hset.assert_any_call("tripwire:states", "test_rule", "0")


def test_apply_tripwire_if_needed_reenable_rule(tripwire_manager, mock_redis):
    """
    Test apply_tripwire_if_needed scenario where the rule was previously disabled
    but now conditions improve (percentage drops below threshold) and the rule is re-enabled.
    """
    current_time = time.time()
    # Users still within time window
    mock_redis["tripwire"].hgetall.return_value = {"user_1": str(current_time - 50)}
    mock_redis["tripwire"].hlen.return_value = 1  # 1 affected user
    # rule was previously disabled
    mock_redis["tripwire"].hget.return_value = "1"
    tripwire_manager.threshold = 0.5  # 50%

    # With total_users = 10 and 1 affected, percentage = 10%, below threshold
    tripwire_manager.apply_tripwire_if_needed("test_rule", "user_2", 10)

    # Rule should now be re-enabled since percentage < threshold
    mock_redis["tripwire"].hset.assert_any_call("tripwire:states", "test_rule", "0")


def test_apply_tripwire_if_needed_zero_total_users(tripwire_manager, mock_redis):
    """
    Test apply_tripwire_if_needed with total_users=0 to ensure no division by zero error.
    Percentage should be 0 if no users exist.
    """
    current_time = time.time()
    mock_redis["tripwire"].hgetall.return_value = {}
    mock_redis["tripwire"].hlen.return_value = 1  # 1 affected user, but total_users=0
    mock_redis["tripwire"].hget.return_value = "0"
    tripwire_manager.threshold = 0.1

    # total_users=0 implies percentage=0/0=0 by code logic
    tripwire_manager.apply_tripwire_if_needed("test_rule", "user_1", 0)

    # Should remain enabled since percentage=0
    mock_redis["tripwire"].hset.assert_any_call("tripwire:states", "test_rule", "0")


def test_apply_tripwire_if_needed_expired_users_removed(tripwire_manager, mock_redis):
    """
    Test apply_tripwire_if_needed removes expired users correctly.
    """
    current_time = time.time()
    # user_1 is expired, user_2 is not
    mock_redis["tripwire"].hgetall.return_value = {
        "user_1": str(current_time - 1000),  # expired beyond time_window=300
        "user_2": str(current_time - 100),
    }
    mock_redis["tripwire"].hlen.return_value = 2
    mock_redis["tripwire"].hget.return_value = "0"
    tripwire_manager.threshold = 0.5

    # total_users=10 and after removing expired user_1, we have 2 affected (including user_3 just added)
    tripwire_manager.apply_tripwire_if_needed("test_rule", "user_3", 10)

    # Expired user_1 should be removed
    mock_redis["tripwire"].hdel.assert_called_once_with(
        "tripwire:affected_users:test_rule", "user_1"
    )
