"""Phase 12 Step 46 — Fractional payout distribution algorithm."""

from collections import defaultdict


def calculate_distribution(
    reads: list[dict],
    active_subscribers: int,
    payout_ratio: float = 0.70,
    contribution_cents: int = 500,
    min_payout_cents: int = 2500,
) -> dict:
    """Calculate reader-centric monthly payout distribution.

    reads row shape:
    {
      "reader_id": "u_reader",
      "author_id": "u_author",
      "read_time_seconds": 123,
      "article_id": "a1"  # optional
    }
    """
    if active_subscribers < 0:
        raise ValueError("active_subscribers cannot be negative")
    if not 0 <= payout_ratio <= 1:
        raise ValueError("payout_ratio must be between 0 and 1")

    total_pool_cents = int(active_subscribers * contribution_cents * payout_ratio)
    if total_pool_cents <= 0 or not reads:
        return {
            "total_pool_cents": total_pool_cents,
            "author_shares": {},
            "eligible_payouts": {},
            "below_threshold": {},
        }

    # Per-reader total read time, used to split each reader's contribution proportionally.
    reader_total_time = defaultdict(int)
    for r in reads:
        sec = int(r.get("read_time_seconds", 0) or 0)
        if sec > 0:
            reader_total_time[r.get("reader_id", "")] += sec

    active_readers = [rid for rid, sec in reader_total_time.items() if rid and sec > 0]
    if not active_readers:
        return {
            "total_pool_cents": total_pool_cents,
            "author_shares": {},
            "eligible_payouts": {},
            "below_threshold": {},
        }

    per_reader_contribution = total_pool_cents / len(active_readers)
    author_shares = defaultdict(float)

    for r in reads:
        reader_id = r.get("reader_id", "")
        author_id = r.get("author_id", "")
        read_sec = int(r.get("read_time_seconds", 0) or 0)
        total_sec = reader_total_time.get(reader_id, 0)
        if not reader_id or not author_id or read_sec <= 0 or total_sec <= 0:
            continue
        author_shares[author_id] += (read_sec / total_sec) * per_reader_contribution

    rounded = {aid: int(round(cents)) for aid, cents in author_shares.items()}
    eligible = {aid: amt for aid, amt in rounded.items() if amt >= min_payout_cents}
    below_threshold = {
        aid: amt for aid, amt in rounded.items() if amt < min_payout_cents
    }

    return {
        "total_pool_cents": total_pool_cents,
        "author_shares": rounded,
        "eligible_payouts": eligible,
        "below_threshold": below_threshold,
    }
