import pytest
from unittest.mock import MagicMock, patch
from feature_restriction.models import UserData
from feature_restriction.redis_user_manager import RedisUserManager


def test_sample():
    assert 1 + 1 == 2


@pytest.fixture
def mock_redis():
    """
    Create a mock Redis client.
    """
    with patch(
        "feature_restriction.redis_user_manager.redis.StrictRedis"
    ) as mock_redis_cls:
        mock_redis_instance = MagicMock()
        mock_redis_cls.return_value = mock_redis_instance
        yield mock_redis_instance


@pytest.fixture
def user_manager(mock_redis):
    """
    Provide an instance of RedisUserManager with a mocked Redis client.
    """
    return RedisUserManager()


@pytest.fixture
def sample_user_data():
    """
    Create sample user data for testing.
    """
    return UserData(
        user_id="test_user",
        scam_message_flags=1,
        credit_cards={"card_001": "12345"},
        total_credit_cards=1,
        unique_zip_codes={"12345"},
        total_spend=100.0,
        total_chargebacks=5.0,
        access_flags={"can_message": True, "can_purchase": True},
    )


def test_get_user_existing(user_manager, mock_redis, sample_user_data):
    """
    Test retrieving an existing user from Redis.
    """
    mock_redis.get.return_value = sample_user_data.json()
    user_data = user_manager.get_user("test_user")
    assert user_data.user_id == "test_user"
    assert user_data.scam_message_flags == 1
    assert user_data.access_flags["can_message"]


def test_get_user_nonexistent(user_manager, mock_redis):
    """
    Test retrieving a non-existent user raises KeyError.
    """
    mock_redis.get.return_value = None
    with pytest.raises(KeyError):
        user_manager.get_user("nonexistent_user")


def test_create_user(user_manager, mock_redis):
    """
    Test creating a new user.
    """
    mock_redis.set.return_value = True
    user_data = user_manager.create_user("new_user")
    assert user_data.user_id == "new_user"
    mock_redis.set.assert_called_once_with("new_user", user_data.json())


def test_save_user(user_manager, mock_redis, sample_user_data):
    """
    Test saving user data to Redis.
    """
    user_manager.save_user(sample_user_data)
    mock_redis.set.assert_called_once_with(
        sample_user_data.user_id, sample_user_data.json()
    )


def test_delete_user(user_manager, mock_redis):
    """
    Test deleting a user from Redis.
    """
    mock_redis.delete.return_value = 1
    user_manager.delete_user("test_user")
    mock_redis.delete.assert_called_once_with("test_user")


def test_get_user_count(user_manager, mock_redis):
    """
    Test counting the number of users in Redis.
    """
    mock_redis.keys.return_value = ["user1", "user2", "user3"]
    count = user_manager.get_user_count()
    assert count == 3
    mock_redis.keys.assert_called_once_with("*")


def test_clear_all_users(user_manager, mock_redis):
    """
    Test clearing all user data from Redis.
    """
    mock_redis.keys.return_value = ["user1", "user2"]
    mock_redis.delete.return_value = 2
    user_manager.clear_all_users()
    mock_redis.delete.assert_called_once_with("user1", "user2")


def test_display_user_data_existing(user_manager, mock_redis, sample_user_data):
    """
    Test displaying user data for an existing user.
    """
    mock_redis.get.return_value = sample_user_data.json()
    output = user_manager.display_user_data("test_user")
    assert "User ID: test_user" in output
    assert "Total Spend: 100.0" in output


def test_display_user_data_nonexistent(user_manager, mock_redis):
    """
    Test displaying user data for a non-existent user.
    """
    mock_redis.get.return_value = None
    output = user_manager.display_user_data("nonexistent_user")
    assert "User ID 'nonexistent_user' not found." in output
