import importlib

import pytest


social_repo_module = importlib.import_module("api.social.repository")
Q = importlib.import_module("api.social.queries")

SocialRepository = social_repo_module.SocialRepository


class _Article:
    def __init__(self, row):
        self.row = row

    @classmethod
    def from_row(cls, row):
        return cls(row)


class _User:
    def __init__(self, row):
        self.row = row

    @classmethod
    def from_row(cls, row):
        return cls(row)


class TestSocialRepository:
    @pytest.mark.asyncio
    async def test_all_methods(self, monkeypatch):
        repo = SocialRepository.__new__(SocialRepository)
        calls = []

        async def _execute(sql, *params):
            calls.append(("execute", sql, params))

        async def _find_one(sql, *params):
            calls.append(("find_one", sql, params))
            if sql == Q.SELECT_REACTION_COUNTS:
                return {
                    "fire_count": 2,
                    "lightbulb_count": 1,
                    "heart_count": 3,
                    "brain_count": 0,
                }
            if sql in (
                Q.COUNT_LIKES,
                Q.COUNT_DISLIKES,
                Q.COUNT_SHARES,
                Q.COUNT_BOOKMARKS,
                Q.COUNT_FOLLOWERS,
                Q.COUNT_FOLLOWING,
            ):
                return {"count": 7}
            if sql in (
                Q.SELECT_IF_LIKED,
                Q.SELECT_IF_DISLIKED,
                Q.SELECT_IF_REACTED,
                Q.SELECT_IF_BOOKMARKED,
                Q.SELECT_IF_FOLLOWING,
            ):
                return {"ok": 1}
            return None

        async def _find_all(sql, *params):
            calls.append(("find_all", sql, params))
            if sql == Q.SELECT_USER_REACTIONS:
                return [{"reaction_type": "fire"}, {"reaction_type": "heart"}]
            if sql == Q.SELECT_BOOKMARKS_BY_USER:
                return [{"id": "a1"}]
            if sql == Q.SELECT_FOLLOWERS:
                return [{"id": "u1"}]
            if sql == Q.SELECT_FOLLOWING:
                return [{"id": "u2"}]
            return []

        def _map_many(rows, model_cls):
            return [model_cls.from_row(r) for r in rows]

        monkeypatch.setattr(social_repo_module, "Article", _Article)
        monkeypatch.setattr(social_repo_module, "User", _User)

        repo.execute = _execute
        repo.find_one = _find_one
        repo.find_all = _find_all
        repo.map_many = _map_many

        await repo.like("u1", "a1")
        await repo.unlike("u1", "a1")
        assert await repo.has_liked("u1", "a1") is True
        assert await repo.count_likes("a1") == 7

        await repo.dislike("u1", "a1")
        await repo.undislike("u1", "a1")
        assert await repo.has_disliked("u1", "a1") is True
        assert await repo.count_dislikes("a1") == 7

        await repo.share("u1", "a1", "x")
        assert await repo.count_shares("a1") == 7

        await repo.add_reaction("a1", "u1", "fire")
        await repo.remove_reaction("a1", "u1", "fire")
        assert await repo.has_reacted("a1", "u1", "fire") is True

        counts = await repo.get_reaction_counts("a1")
        assert counts == {"fire": 2, "lightbulb": 1, "heart": 3, "brain": 0}

        user_reactions = await repo.get_user_reactions("a1", "u1")
        assert user_reactions == {"fire", "heart"}

        await repo.bookmark("u1", "a1")
        await repo.unbookmark("u1", "a1")
        assert await repo.has_bookmarked("u1", "a1") is True

        bookmarks = await repo.find_bookmarks("u1", 10, 0)
        assert isinstance(bookmarks[0], _Article)
        assert await repo.count_bookmarks("u1") == 7

        await repo.follow("u1", "u2")
        await repo.unfollow("u1", "u2")
        assert await repo.is_following("u1", "u2") is True

        followers = await repo.find_followers("u2", 10, 0)
        following = await repo.find_following("u1", 10, 0)
        assert isinstance(followers[0], _User)
        assert isinstance(following[0], _User)
        assert await repo.count_followers("u2") == 7
        assert await repo.count_following("u1") == 7

        assert any(call[0] == "execute" for call in calls)
        assert any(call[0] == "find_one" for call in calls)
        assert any(call[0] == "find_all" for call in calls)

    @pytest.mark.asyncio
    async def test_reaction_counts_empty_row(self):
        repo = SocialRepository.__new__(SocialRepository)

        async def _find_one(sql, *params):
            return None

        repo.find_one = _find_one

        counts = await repo.get_reaction_counts("a1")
        assert counts == {"fire": 0, "lightbulb": 0, "heart": 0, "brain": 0}
