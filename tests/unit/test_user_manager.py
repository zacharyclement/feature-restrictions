from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException

from feature_restriction.models import UserData


def test_get_user_existing(user_manager, mock_redis, sample_user_data):
    """
    Test retrieving an existing user from Redis.
    """
    mock_redis["user"].get.return_value = sample_user_data.json()
    user_data = user_manager.get_user("test_user")
    assert user_data.user_id == "test_user"
    assert user_data.scam_message_flags == 1
    assert user_data.access_flags["can_message"]


def test_get_user_nonexistent(user_manager, mock_redis):
    """
    Test retrieving a non-existent user raises KeyError.
    """
    mock_redis["user"].get.return_value = None
    with pytest.raises(KeyError):
        user_manager.get_user("nonexistent_user")


def test_get_user_exception(user_manager, mock_redis):
    """
    Test get_user raises a generic exception if redis get fails.
    """
    mock_redis["user"].get.side_effect = Exception("Redis error")
    with pytest.raises(Exception, match="Redis error"):
        user_manager.get_user("test_user")


def test_create_user(user_manager, mock_redis):
    """
    Test creating a new user.
    """
    mock_redis["user"].set.return_value = True
    user_data = user_manager.create_user("new_user")
    assert user_data.user_id == "new_user"
    mock_redis["user"].set.assert_called_once_with("new_user", user_data.json())


def test_create_user_exception(user_manager, mock_redis):
    """
    Test create_user raises an exception if saving the user fails.
    """
    mock_redis["user"].set.side_effect = Exception("Redis set error")
    with pytest.raises(Exception, match="Redis set error"):
        user_manager.create_user("failing_user")


def test_save_user(user_manager, mock_redis, sample_user_data):
    """
    Test saving user data to Redis.
    """
    user_manager.save_user(sample_user_data)
    mock_redis["user"].set.assert_called_once_with(
        sample_user_data.user_id, sample_user_data.json()
    )


def test_save_user_exception(user_manager, mock_redis, sample_user_data):
    """
    Test save_user raises an exception if redis set fails.
    """
    mock_redis["user"].set.side_effect = Exception("Redis set error")
    with pytest.raises(Exception, match="Redis set error"):
        user_manager.save_user(sample_user_data)


def test_delete_user(user_manager, mock_redis):
    """
    Test deleting a user from Redis.
    """
    mock_redis["user"].delete.return_value = 1
    user_manager.delete_user("test_user")
    mock_redis["user"].delete.assert_called_once_with("test_user")


def test_delete_user_exception(user_manager, mock_redis):
    """
    Test delete_user raises an exception if redis delete fails.
    """
    mock_redis["user"].delete.side_effect = Exception("Redis delete error")
    with pytest.raises(Exception, match="Redis delete error"):
        user_manager.delete_user("test_user")


def test_get_user_count(user_manager, mock_redis):
    """
    Test counting the number of users in Redis.
    """
    mock_redis["user"].keys.return_value = ["user1", "user2", "user3"]
    count = user_manager.get_user_count()
    assert count == 3
    mock_redis["user"].keys.assert_called_once_with("*")


def test_get_user_count_exception(user_manager, mock_redis):
    """
    Test get_user_count returns 0 and logs error if redis keys fail.
    """
    mock_redis["user"].keys.side_effect = Exception("Redis keys error")
    count = user_manager.get_user_count()
    assert count == 0
    mock_redis["user"].keys.assert_called_once_with("*")


def test_clear_all_users(user_manager, mock_redis):
    """
    Test clearing all user data from Redis.
    """
    mock_redis["user"].keys.return_value = ["user1", "user2"]
    mock_redis["user"].delete.return_value = 2
    user_manager.clear_all_users()
    mock_redis["user"].delete.assert_called_once_with("user1", "user2")


def test_clear_all_users_no_keys(user_manager, mock_redis):
    """
    Test clearing all user data when there are no keys in Redis.
    """
    mock_redis["user"].keys.return_value = []
    user_manager.clear_all_users()
    # delete not called since no keys
    mock_redis["user"].delete.assert_not_called()


def test_clear_all_users_exception(user_manager, mock_redis):
    """
    Test clear_all_users raises an exception if redis delete fails.
    """
    mock_redis["user"].keys.return_value = ["user1", "user2"]
    mock_redis["user"].delete.side_effect = Exception("Redis delete error")
    with pytest.raises(Exception, match="Redis delete error"):
        user_manager.clear_all_users()


def test_display_user_data_existing(user_manager, mock_redis, sample_user_data):
    """
    Test displaying user data for an existing user.
    """
    mock_redis["user"].get.return_value = sample_user_data.json()
    output = user_manager.display_user_data("test_user")
    assert "User ID: test_user" in output
    assert "Total Spend: 100.0" in output


def test_display_user_data_nonexistent(user_manager, mock_redis):
    """
    Test displaying user data for a non-existent user.
    """
    mock_redis["user"].get.return_value = None
    output = user_manager.display_user_data("nonexistent_user")
    assert "User ID 'nonexistent_user' not found." in output


def test_display_user_data_with_provided_user_data(user_manager, sample_user_data):
    """
    Test displaying user data when user_data is directly provided.
    """
    # This avoids calling get_user and directly uses the given user_data.
    output = user_manager.display_user_data("test_user", user_data=sample_user_data)
    assert "User ID: test_user" in output
    assert "Scam Message Flags: 1" in output


def test_display_user_data_exception(user_manager, mock_redis):
    """
    Test display_user_data returns error message if an unexpected exception occurs.
    """
    mock_redis["user"].get.side_effect = Exception("Unexpected error")
    output = user_manager.display_user_data("failing_user")
    assert "Error displaying data for user_id 'failing_user'." in output
