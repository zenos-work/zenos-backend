import importlib

import pytest


users_service_module = importlib.import_module("api.users.service")
users_repo_module = importlib.import_module("api.users.repository")
Q = importlib.import_module("api.users.queries")

UserService = users_service_module.UserService
UserRepository = users_repo_module.UserRepository


class _User:
    def __init__(self, id="u1"):
        self.id = id

    def to_dict(self, _scope=None):
        return {"id": self.id}


class _Repo:
    def __init__(self):
        self.calls = []

    async def find_by_id(self, user_id):
        self.calls.append(("find_by_id", user_id))
        return _User(user_id)

    async def find_public_by_id(self, user_id):
        self.calls.append(("find_public_by_id", user_id))
        return _User(user_id)

    async def find_all(self, limit=20, offset=0):
        self.calls.append(("find_all", limit, offset))
        return [_User("u1"), _User("u2")]

    async def count_all(self):
        self.calls.append(("count_all",))
        return 2

    async def update_avatar_only(self, user_id, avatar_url):
        self.calls.append(("update_avatar_only", user_id, avatar_url))

    async def update_profile(self, user_id, name, avatar_url):
        self.calls.append(("update_profile", user_id, name, avatar_url))

    async def self_upgrade_role(self, user_id, new_role, current_role):
        self.calls.append(("self_upgrade_role", user_id, new_role, current_role))

    async def update_role(self, user_id, role):
        self.calls.append(("update_role", user_id, role))

    async def ban(self, user_id):
        self.calls.append(("ban", user_id))

    async def unban(self, user_id):
        self.calls.append(("unban", user_id))

    async def ensure_prefs(self, user_id):
        self.calls.append(("ensure_prefs", user_id))

    async def find_prefs(self, user_id):
        self.calls.append(("find_prefs", user_id))
        return {"topics": '["ai"]', "email_notifs": 1, "theme": "dark"}

    async def update_prefs(self, user_id, topics, email_notifs, theme):
        self.calls.append(("update_prefs", user_id, topics, email_notifs, theme))

    async def find_reading_history(self, user_id, limit, offset):
        self.calls.append(("find_reading_history", user_id, limit, offset))
        return [
            {
                "article_id": "a1",
                "slug": "s1",
                "title": "t1",
                "subtitle": None,
                "author_name": None,
                "cover_image_url": None,
                "read_time_minutes": 5,
                "progress": 50,
                "last_read_at": "now",
                "created_at": "c",
                "updated_at": "u",
            }
        ]

    async def count_reading_history(self, user_id):
        self.calls.append(("count_reading_history", user_id))
        return 1

    async def upsert_reading_history_item(self, *args):
        self.calls.append(("upsert_reading_history_item",) + args)

    async def delete_reading_history_item(self, user_id, article_id):
        self.calls.append(("delete_reading_history_item", user_id, article_id))

    async def clear_reading_history(self, user_id):
        self.calls.append(("clear_reading_history", user_id))


class _Ctx:
    class log:
        events = []

        @classmethod
        async def event(cls, name, data=None):
            cls.events.append((name, data))


class _Env:
    DB = object()


class _ReqRole:
    def __init__(self, role):
        self.role = role


class _ReqProfile:
    def __init__(self, name=None, avatar_url=None):
        self.name = name
        self.avatar_url = avatar_url


@pytest.fixture
def svc():
    s = UserService(_Env(), _Ctx())
    s._repo = _Repo()
    return s


class TestUserService:
    @pytest.mark.asyncio
    async def test_get_by_id_scopes(self, svc):
        await svc.get_by_id("u1", scope="private")
        await svc.get_by_id("u2", scope="public")

        assert ("find_by_id", "u1") in svc._repo.calls
        assert ("find_public_by_id", "u2") in svc._repo.calls

    @pytest.mark.asyncio
    async def test_list_all_update_and_role_actions(self, svc):
        items, total = await svc.list_all(limit=10, offset=0)
        assert total == 2
        assert items == [{"id": "u1"}, {"id": "u2"}]

        await svc.update_profile(
            "u1", _ReqProfile(avatar_url="x"), skip_name_update=True
        )
        await svc.update_profile(
            "u1", _ReqProfile(name="Alice", avatar_url="x"), skip_name_update=False
        )
        await svc.self_upgrade_to_author("u1")
        await svc.set_role("u1", _ReqRole("APPROVER"))
        await svc.ban("u1")
        await svc.unban("u1")

        assert any(call[0] == "update_avatar_only" for call in svc._repo.calls)
        assert any(call[0] == "update_profile" for call in svc._repo.calls)
        assert any(call[0] == "self_upgrade_role" for call in svc._repo.calls)
        assert any(call[0] == "update_role" for call in svc._repo.calls)
        assert any(call[0] == "ban" for call in svc._repo.calls)
        assert any(call[0] == "unban" for call in svc._repo.calls)

    @pytest.mark.asyncio
    async def test_prefs_and_history_and_mutations(self, svc):
        prefs = await svc.get_prefs("u1")
        assert prefs["topics"] == ["ai"]

        await svc.update_prefs("u1", ["x"], 0, "light")

        history = await svc.list_reading_history("u1", page=1, limit=10)
        assert history["pagination"]["total"] == 1
        assert history["items"][0]["article_id"] == "a1"

        item = await svc.upsert_reading_history_item(
            "u1",
            {
                "article_id": "a2",
                "slug": "slug",
                "title": "Title",
                "progress": 120,
                "read_time_minutes": -5,
            },
        )
        assert item["progress"] == 100
        assert item["read_time_minutes"] == 0

        await svc.remove_reading_history_item("u1", "a2")
        await svc.clear_reading_history("u1")

        with pytest.raises(ValueError, match="article_id is required"):
            await svc.remove_reading_history_item("u1", "")

    def test_normalize_payload_validation(self, svc):
        with pytest.raises(ValueError, match="article_id is required"):
            svc._normalize_reading_history_payload({})

        with pytest.raises(ValueError, match="slug is required"):
            svc._normalize_reading_history_payload({"article_id": "a1"})

        with pytest.raises(ValueError, match="title is required"):
            svc._normalize_reading_history_payload({"article_id": "a1", "slug": "s"})

        with pytest.raises(ValueError, match="read_time_minutes must be a number"):
            svc._normalize_reading_history_payload(
                {
                    "article_id": "a1",
                    "slug": "s",
                    "title": "t",
                    "read_time_minutes": "abc",
                }
            )

        with pytest.raises(ValueError, match="progress must be a number"):
            svc._normalize_reading_history_payload(
                {"article_id": "a1", "slug": "s", "title": "t", "progress": "abc"}
            )


class TestUserRepository:
    @pytest.mark.asyncio
    async def test_repository_methods(self):
        repo = UserRepository.__new__(UserRepository)
        executed = []

        async def _find_one(sql, *params):
            executed.append(("find_one", sql, params))
            if sql == Q.COUNT_READING_HISTORY_BY_USER:
                return {"c": 2}
            return {"id": "u1"}

        async def _execute(sql, *params):
            executed.append(("execute", sql, params))

        class _EX:
            async def all(self, sql, *params):
                executed.append(("_ex.all", sql, params))
                if sql == Q.SELECT_READING_HISTORY_BY_USER:
                    return [
                        {
                            "user_id": "u1",
                            "article_id": "a1",
                            "slug": "s1",
                            "title": "t1",
                            "subtitle": None,
                            "author_name": None,
                            "cover_image_url": None,
                            "read_time_minutes": 1,
                            "progress": 10,
                            "last_read_at": "x",
                            "created_at": "c",
                            "updated_at": "u",
                        }
                    ]
                return [{"id": "u1"}]

            async def first(self, sql):
                executed.append(("_ex.first", sql, ()))
                return {"cnt": 3}

        repo._ex = _EX()
        repo.find_one = _find_one
        repo.execute = _execute
        repo.map_one = lambda row, _model: {"mapped": row.get("id")}

        await repo.find_by_id("u1")
        await repo.find_public_by_id("u1")
        users = await repo.find_all(limit=10, offset=0)
        total = await repo.count_all()
        await repo.find_prefs("u1")
        await repo.ensure_prefs("u1")
        await repo.update_profile("u1", "Alice", None)
        await repo.update_avatar_only("u1", None)
        await repo.update_role("u1", "AUTHOR")
        await repo.self_upgrade_role("u1", "AUTHOR", "READER")
        await repo.update_prefs("u1", "[]", 1, "dark")
        history = await repo.find_reading_history("u1", 10, 0)
        count = await repo.count_reading_history("u1")
        await repo.upsert_reading_history_item(
            "u1", "a1", "s", "t", None, None, None, 1, 1, None
        )
        await repo.delete_reading_history_item("u1", "a1")
        await repo.clear_reading_history("u1")
        await repo.ban("u1")
        await repo.unban("u1")

        assert users == [{"mapped": "u1"}]
        assert total == 3
        assert history[0]["article_id"] == "a1"
        assert count == 2
        assert any(item[0] == "execute" for item in executed)
