from auth.models import User


class TestAuthModels:
    def test_user_dataclass_defaults(self):
        user = User(
            id="u1",
            email="u1@example.com",
            name="User One",
            role="AUTHOR",
        )

        assert user.id == "u1"
        assert user.email == "u1@example.com"
        assert user.name == "User One"
        assert user.role == "AUTHOR"
        assert user.avatar_url is None
        assert user.google_id is None
        assert user.is_active == 1

    def test_user_dataclass_with_custom_optional_fields(self):
        user = User(
            id="u2",
            email="u2@example.com",
            name="User Two",
            role="READER",
            avatar_url="https://cdn/u2.png",
            google_id="gid-2",
            is_active=0,
        )

        assert user.avatar_url == "https://cdn/u2.png"
        assert user.google_id == "gid-2"
        assert user.is_active == 0
