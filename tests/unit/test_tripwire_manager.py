import time
from unittest.mock import MagicMock
import pytest
from feature_restriction.tripwire_manager import TripWireManager


def test_basic_():
    assert 2 + 2 == 4


# def test_is_rule_disabled_via_tripwire(tripwire_manager, mock_redis):
#     """
#     Test the is_rule_disabled_via_tripwire method.
#     """
#     # Mock Redis response
#     mock_redis.hget.return_value = "1"

#     assert tripwire_manager.is_rule_disabled_via_tripwire("test_rule") is True
#     mock_redis.hget.assert_called_with("tripwire:states", "test_rule")

#     # Mock Redis response for not disabled
#     mock_redis.hget.return_value = "0"
#     assert tripwire_manager.is_rule_disabled_via_tripwire("test_rule") is False


# def test_apply_tripwire_if_needed(tripwire_manager, mock_redis):
#     """
#     Test the apply_tripwire_if_needed method.
#     """
#     mock_redis.hgetall.return_value = {"user_1": str(time.time() - 100)}
#     mock_redis.hlen.return_value = 1
#     tripwire_manager.threshold = 0.1  # 10%

#     tripwire_manager.apply_tripwire_if_needed("test_rule", "user_2", 10)

#     # Check expired users removal and updated affected users
#     affected_users_key = "tripwire:affected_users:test_rule"
#     mock_redis.hdel.assert_not_called()  # No expired users
#     mock_redis.hset.assert_called_with(affected_users_key, "user_2", mock_redis.hset.call_args[0][2])

#     # Check tripwire state updated
#     mock_redis.hset.assert_called_with("tripwire:states", "test_rule", "1")


# def test_clear_rules(tripwire_manager, mock_redis):
#     """
#     Test the clear_rules method.
#     """
#     # Mock Redis keys
#     mock_redis.keys.return_value = ["tripwire:affected_users:test_rule"]

#     tripwire_manager.clear_rules()

#     # Check deletion of states and affected users
#     mock_redis.delete.assert_any_call("tripwire:states")
#     mock_redis.delete.assert_any_call("tripwire:affected_users:test_rule")


# def test_get_tripwire_state(tripwire_manager, mock_redis):
#     """
#     Test the get_tripwire_state method.
#     """
#     # Mock Redis response
#     mock_redis.hget.return_value = "1"
#     assert tripwire_manager.get_tripwire_state("test_rule") is True

#     mock_redis.hget.return_value = "0"
#     assert tripwire_manager.get_tripwire_state("test_rule") is False


# def test_get_affected_users(tripwire_manager, mock_redis):
#     """
#     Test the get_affected_users method.
#     """
#     # Mock Redis response
#     mock_redis.hgetall.return_value = {"user_1": str(time.time())}

#     affected_users = tripwire_manager.get_affected_users("test_rule")
#     assert affected_users == {"user_1": str(time.time())}
#     mock_redis.hgetall.assert_called_with("tripwire:affected_users:test_rule")


# def test_get_disabled_rules(tripwire_manager, mock_redis):
#     """
#     Test the get_disabled_rules method.
#     """
#     # Mock Redis response
#     mock_redis.hgetall.return_value = {"test_rule": "1", "another_rule": "0"}

#     disabled_rules = tripwire_manager.get_disabled_rules()
#     assert disabled_rules == {"test_rule": "1", "another_rule": "0"}
#     mock_redis.hgetall.assert_called_with("tripwire:states")
