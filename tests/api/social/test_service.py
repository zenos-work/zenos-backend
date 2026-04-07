from pathlib import Path
import importlib
import sys

import pytest

ROOT = Path(__file__).resolve().parents[3]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

SocialService = importlib.import_module("api.social.service").SocialService


class _Log:
    def __init__(self):
        self.analytics_calls = []

    async def analytics(self, name, data=None):
        self.analytics_calls.append((name, data))


class _Ctx:
    def __init__(self):
        self.log = _Log()


class _Env:
    def __init__(self):
        self.DB = object()


class _Repo:
    def __init__(self):
        self.calls = []
        self.flags = {
            "liked": False,
            "disliked": False,
            "reacted": False,
            "bookmarked": False,
            "following": False,
        }
        self.fail_like = False
        self.fail_dislike = False
        self.fail_bookmark = False
        self.fail_follow = False
        self.share_count = 4
        self.like_count = 2
        self.dislike_count = 1
        self.bookmark_count = 3
        self.followers_count = 10
        self.following_count = 7
        self.reaction_counts = {
            "fire_count": 2,
            "lightbulb_count": 1,
            "heart_count": 3,
            "brain_count": 0,
        }
        self.user_reactions = {"fire"}

    async def like(self, user_id, article_id):
        self.calls.append(("like", user_id, article_id))
        if self.fail_like:
            raise Exception("duplicate")

    async def unlike(self, user_id, article_id):
        self.calls.append(("unlike", user_id, article_id))

    async def has_liked(self, user_id, article_id):
        self.calls.append(("has_liked", user_id, article_id))
        return self.flags["liked"]

    async def count_likes(self, article_id):
        self.calls.append(("count_likes", article_id))
        return self.like_count

    async def dislike(self, user_id, article_id):
        self.calls.append(("dislike", user_id, article_id))
        if self.fail_dislike:
            raise Exception("duplicate")

    async def undislike(self, user_id, article_id):
        self.calls.append(("undislike", user_id, article_id))

    async def has_disliked(self, user_id, article_id):
        self.calls.append(("has_disliked", user_id, article_id))
        return self.flags["disliked"]

    async def count_dislikes(self, article_id):
        self.calls.append(("count_dislikes", article_id))
        return self.dislike_count

    async def share(self, user_id, article_id, provider):
        self.calls.append(("share", user_id, article_id, provider))

    async def count_shares(self, article_id):
        self.calls.append(("count_shares", article_id))
        return self.share_count

    async def has_reacted(self, article_id, user_id, reaction_type):
        self.calls.append(("has_reacted", article_id, user_id, reaction_type))
        return self.flags["reacted"]

    async def add_reaction(self, article_id, user_id, reaction_type):
        self.calls.append(("add_reaction", article_id, user_id, reaction_type))

    async def remove_reaction(self, article_id, user_id, reaction_type):
        self.calls.append(("remove_reaction", article_id, user_id, reaction_type))

    async def get_reaction_counts(self, article_id):
        self.calls.append(("get_reaction_counts", article_id))
        return {
            "fire": self.reaction_counts["fire_count"],
            "lightbulb": self.reaction_counts["lightbulb_count"],
            "heart": self.reaction_counts["heart_count"],
            "brain": self.reaction_counts["brain_count"],
        }

    async def get_user_reactions(self, article_id, user_id):
        self.calls.append(("get_user_reactions", article_id, user_id))
        return self.user_reactions

    async def bookmark(self, user_id, article_id):
        self.calls.append(("bookmark", user_id, article_id))
        if self.fail_bookmark:
            raise Exception("duplicate")

    async def unbookmark(self, user_id, article_id):
        self.calls.append(("unbookmark", user_id, article_id))

    async def has_bookmarked(self, user_id, article_id):
        self.calls.append(("has_bookmarked", user_id, article_id))
        return self.flags["bookmarked"]

    async def find_bookmarks(self, user_id, limit, offset):
        self.calls.append(("find_bookmarks", user_id, limit, offset))
        return ["a1", "a2"]

    async def count_bookmarks(self, user_id):
        self.calls.append(("count_bookmarks", user_id))
        return self.bookmark_count

    async def follow(self, follower_id, following_id):
        self.calls.append(("follow", follower_id, following_id))
        if self.fail_follow:
            raise Exception("duplicate")

    async def unfollow(self, follower_id, following_id):
        self.calls.append(("unfollow", follower_id, following_id))

    async def is_following(self, follower_id, following_id):
        self.calls.append(("is_following", follower_id, following_id))
        return self.flags["following"]

    async def find_followers(self, user_id, limit, offset):
        self.calls.append(("find_followers", user_id, limit, offset))
        return ["u1"]

    async def count_followers(self, user_id):
        self.calls.append(("count_followers", user_id))
        return self.followers_count

    async def find_following(self, user_id, limit, offset):
        self.calls.append(("find_following", user_id, limit, offset))
        return ["u2", "u3"]

    async def count_following(self, user_id):
        self.calls.append(("count_following", user_id))
        return self.following_count


class _ArticleRepo:
    def __init__(self):
        self.calls = []

    async def increment_likes(self, article_id):
        self.calls.append(("increment_likes", article_id))

    async def decrement_likes(self, article_id):
        self.calls.append(("decrement_likes", article_id))

    async def increment_dislikes(self, article_id):
        self.calls.append(("increment_dislikes", article_id))

    async def decrement_dislikes(self, article_id):
        self.calls.append(("decrement_dislikes", article_id))

    async def increment_shares(self, article_id):
        self.calls.append(("increment_shares", article_id))


class _AnalyticsService:
    def __init__(self):
        self.calls = []
        self.fail = False

    async def record_article_event(self, **kwargs):
        self.calls.append(kwargs)
        if self.fail:
            raise RuntimeError("analytics unavailable")


@pytest.fixture
def service():
    ctx = _Ctx()
    svc = SocialService(_Env(), ctx)
    svc._repo = _Repo()
    svc._article_repo = _ArticleRepo()
    svc._analytics_service = _AnalyticsService()
    return svc


class TestSocialService:
    @pytest.mark.asyncio
    async def test_toggle_like_add_success(self, service):
        result = await service.toggle_like("u1", "a1", True)

        assert result.action == "like"
        assert result.target_id == "a1"
        assert result.active is True
        assert ("like", "u1", "a1") in service._repo.calls
        assert ("increment_likes", "a1") in service._article_repo.calls
        assert service._analytics_service.calls[0]["event_type"] == "LIKE"
        assert service._ctx.log.analytics_calls[-1][0] == "social.liked"

    @pytest.mark.asyncio
    async def test_toggle_like_duplicate_raises_value_error(self, service):
        service._repo.fail_like = True

        with pytest.raises(ValueError, match="Already liked"):
            await service.toggle_like("u1", "a1", True)

    @pytest.mark.asyncio
    async def test_toggle_like_swallows_analytics_record_errors(self, service):
        service._analytics_service.fail = True

        result = await service.toggle_like("u1", "a1", True)

        assert result.active is True
        assert ("increment_likes", "a1") in service._article_repo.calls

    @pytest.mark.asyncio
    async def test_toggle_like_remove_success(self, service):
        result = await service.toggle_like("u1", "a1", False)

        assert result.active is False
        assert ("unlike", "u1", "a1") in service._repo.calls
        assert ("decrement_likes", "a1") in service._article_repo.calls
        assert service._ctx.log.analytics_calls[-1][0] == "social.unliked"

    @pytest.mark.asyncio
    async def test_like_and_dislike_stats_and_checks(self, service):
        service._repo.flags["liked"] = True
        service._repo.flags["disliked"] = True

        assert await service.check_liked("u1", "a1") is True
        assert await service.check_disliked("u1", "a1") is True
        assert await service.get_like_stats("a1") == {
            "article_id": "a1",
            "like_count": 2,
        }
        assert await service.get_dislike_stats("a1") == {
            "article_id": "a1",
            "dislike_count": 1,
        }

    @pytest.mark.asyncio
    async def test_toggle_dislike_add_remove_and_duplicate(self, service):
        add_result = await service.toggle_dislike("u1", "a1", True)
        remove_result = await service.toggle_dislike("u1", "a1", False)

        assert add_result.active is True
        assert remove_result.active is False
        assert ("increment_dislikes", "a1") in service._article_repo.calls
        assert ("decrement_dislikes", "a1") in service._article_repo.calls

        service._repo.fail_dislike = True
        with pytest.raises(ValueError, match="Already disliked"):
            await service.toggle_dislike("u1", "a1", True)

    @pytest.mark.asyncio
    async def test_share_article_validates_provider_and_returns_stats(self, service):
        with pytest.raises(ValueError, match="Unsupported provider"):
            await service.share_article("u1", "a1", provider="reddit")

        result = await service.share_article("u1", "a1", provider=" X ")

        assert result == {
            "article_id": "a1",
            "provider": "x",
            "share_count": 4,
        }
        assert ("increment_shares", "a1") in service._article_repo.calls
        assert service._ctx.log.analytics_calls[-1][0] == "social.shared"

    @pytest.mark.asyncio
    async def test_toggle_reaction_add_and_remove_paths(self, service):
        with pytest.raises(ValueError, match="Invalid reaction type"):
            await service.toggle_reaction("u1", "a1", "wow")

        service._repo.flags["reacted"] = False
        add_result = await service.toggle_reaction("u1", "a1", " Fire ")
        assert add_result.action == "reaction:fire"
        assert add_result.active is True
        assert ("add_reaction", "a1", "u1", "fire") in service._repo.calls

        service._repo.flags["reacted"] = True
        remove_result = await service.toggle_reaction("u1", "a1", "fire")
        assert remove_result.active is False
        assert ("remove_reaction", "a1", "u1", "fire") in service._repo.calls

    @pytest.mark.asyncio
    async def test_remove_reaction_and_get_reactions(self, service):
        with pytest.raises(ValueError, match="Invalid reaction type"):
            await service.remove_reaction("u1", "a1", "invalid")

        result = await service.remove_reaction("u1", "a1", "heart")
        assert result.action == "reaction:heart"
        assert result.active is False

        with_user = await service.get_reactions("a1", user_id="u1")
        no_user = await service.get_reactions("a1", user_id=None)

        assert with_user["reactions"]["fire"]["userReacted"] is True
        assert no_user["reactions"]["fire"]["userReacted"] is False
        assert with_user["total_reactions"] == 6

    @pytest.mark.asyncio
    async def test_bookmark_paths(self, service):
        add_result = await service.toggle_bookmark("u1", "a1", True)
        remove_result = await service.toggle_bookmark("u1", "a1", False)

        assert add_result.active is True
        assert remove_result.active is False

        service._repo.fail_bookmark = True
        with pytest.raises(ValueError, match="Already bookmarked"):
            await service.toggle_bookmark("u1", "a1", True)

        service._repo.flags["bookmarked"] = True
        assert await service.check_bookmarked("u1", "a1") is True

    @pytest.mark.asyncio
    async def test_get_bookmarks_clamps_pagination(self, service):
        items, total = await service.get_bookmarks("u1", page=0, limit=500)

        assert items == ["a1", "a2"]
        assert total == 3
        assert ("find_bookmarks", "u1", 100, 0) in service._repo.calls

    @pytest.mark.asyncio
    async def test_follow_paths(self, service):
        with pytest.raises(ValueError, match="Cannot follow yourself"):
            await service.toggle_follow("u1", "u1", True)

        add_result = await service.toggle_follow("u1", "u2", True)
        remove_result = await service.toggle_follow("u1", "u2", False)

        assert add_result.active is True
        assert remove_result.active is False

        service._repo.fail_follow = True
        with pytest.raises(ValueError, match="Already following"):
            await service.toggle_follow("u1", "u2", True)

    @pytest.mark.asyncio
    async def test_follow_lists_and_user_stats(self, service):
        service._repo.flags["following"] = True

        assert await service.check_following("u1", "u2") is True

        followers, followers_total = await service.list_followers(
            "u2", page=0, limit=1000
        )
        following, following_total = await service.list_following(
            "u1", page=0, limit=1000
        )

        assert followers == ["u1"]
        assert followers_total == 10
        assert following == ["u2", "u3"]
        assert following_total == 7

        stats = await service.get_user_social_stats("u1")
        assert stats == {
            "user_id": "u1",
            "followers_count": 10,
            "following_count": 7,
        }
