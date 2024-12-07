from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException

from feature_restriction.endpoint_access import RedisEndpointAccess
from feature_restriction.models import UserData
from feature_restriction.redis_user_manager import RedisUserManager


def test_check_access_success(endpoint_access, user_manager):
    # Arrange
    user_id = "user123"
    access_key = "can_message"
    user_data = UserData(
        user_id=user_id,
        scam_message_flags=1,
        credit_cards={"card_001": "12345"},
        total_credit_cards=1,
        unique_zip_codes={"12345"},
        total_spend=100.0,
        total_chargebacks=5.0,
        access_flags={"can_message": True},
    )
    user_manager.get_user = MagicMock(return_value=user_data)

    # Act
    result = endpoint_access.check_access(user_id, access_key)

    # Assert
    assert result == {"can_message": True}
    user_manager.get_user.assert_called_once_with(user_id)


def test_check_access_no_access_key(endpoint_access, user_manager):
    # Arrange
    user_id = "user123"
    access_key = "can_purchase"
    # User doesn't have "can_purchase" key
    user_data = UserData(
        user_id=user_id,
        scam_message_flags=1,
        credit_cards={"card_001": "12345"},
        total_credit_cards=1,
        unique_zip_codes={"12345"},
        total_spend=100.0,
        total_chargebacks=5.0,
        access_flags={"can_message": True},
    )
    user_manager.get_user = MagicMock(return_value=user_data)

    # Act
    result = endpoint_access.check_access(user_id, access_key)

    # Assert
    assert result == {"can_purchase": None}
    user_manager.get_user.assert_called_once_with(user_id)


def test_check_access_user_not_found(endpoint_access, user_manager):
    # Arrange
    user_id = "user_not_found"
    access_key = "can_message"
    user_manager.get_user = MagicMock(side_effect=KeyError("User not found"))

    # Act
    result = endpoint_access.check_access(user_id, access_key)

    # Assert
    assert result == {"error": f"No user found with ID '{user_id}'"}
    user_manager.get_user.assert_called_once_with(user_id)


def test_check_access_unexpected_error(endpoint_access, user_manager):
    # Arrange
    user_id = "user123"
    access_key = "can_message"
    user_manager.get_user = MagicMock(
        side_effect=Exception("Database connection error")
    )

    # Act & Assert
    with pytest.raises(HTTPException) as exc:
        endpoint_access.check_access(user_id, access_key)

    assert exc.value.status_code == 500
    assert "An unexpected error occurred." in exc.value.detail
    user_manager.get_user.assert_called_once_with(user_id)
