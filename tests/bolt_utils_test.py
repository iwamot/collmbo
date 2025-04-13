import pytest
from slack_bolt import BoltContext

from app.bolt_utils import extract_user_id_from_context


@pytest.mark.parametrize(
    "actor_user_id, user_id, expected",
    [
        ("U_ACTOR", "U_USER", "U_ACTOR"),
        (None, "U_USER", "U_USER"),
        (None, None, None),
    ],
)
def test_extract_user_id_from_context(actor_user_id, user_id, expected):
    context = BoltContext(actor_user_id=actor_user_id, user_id=user_id)

    result = extract_user_id_from_context(context)

    assert result == expected
