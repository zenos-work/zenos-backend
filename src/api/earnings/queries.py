# ── Author Earnings ──
SELECT_EARNINGS_BY_AUTHOR = (
    "SELECT * FROM author_earnings"
    " WHERE author_id = ?"
    " ORDER BY period_start DESC"
    " LIMIT ? OFFSET ?"
)

COUNT_EARNINGS_BY_AUTHOR = (
    "SELECT COUNT(*) AS c FROM author_earnings WHERE author_id = ?"
)

SELECT_EARNINGS_SUMMARY = (
    "SELECT"
    "  SUM(total_earnings_cents) AS total_earnings,"
    "  SUM(net_earnings_cents) AS net_earnings,"
    "  SUM(platform_fee_cents) AS total_fees,"
    "  SUM(premium_reads_count) AS total_reads"
    " FROM author_earnings"
    " WHERE author_id = ? AND status IN ('confirmed', 'paid')"
)

# ── Author Payouts ──
SELECT_PAYOUTS_BY_AUTHOR = (
    "SELECT * FROM author_payouts"
    " WHERE author_id = ?"
    " ORDER BY created_at DESC"
    " LIMIT ? OFFSET ?"
)

COUNT_PAYOUTS_BY_AUTHOR = "SELECT COUNT(*) AS c FROM author_payouts WHERE author_id = ?"

INSERT_PAYOUT_REQUEST = (
    "INSERT INTO author_payouts"
    " (id, author_id, amount_cents, currency, payout_method, period_start, period_end)"
    " VALUES (?, ?, ?, ?, ?, NULLIF(?, ''), NULLIF(?, ''))"
)

SELECT_PENDING_PAYOUT = (
    "SELECT id FROM author_payouts"
    " WHERE author_id = ? AND status IN ('pending', 'processing')"
    " LIMIT 1"
)

# ── Tip Transactions ──
INSERT_TIP = (
    "INSERT INTO tip_transactions"
    " (id, tipper_id, author_id, article_id, amount_cents, currency,"
    "  platform_fee_cents, net_amount_cents, message, is_anonymous)"
    " VALUES (?, ?, ?, NULLIF(?, ''), ?, ?, ?, ?, NULLIF(?, ''), ?)"
)

SELECT_TIPS_RECEIVED = (
    "SELECT * FROM tip_transactions"
    " WHERE author_id = ?"
    " ORDER BY created_at DESC"
    " LIMIT ? OFFSET ?"
)

COUNT_TIPS_RECEIVED = "SELECT COUNT(*) AS c FROM tip_transactions WHERE author_id = ?"

SELECT_TIPS_SENT = (
    "SELECT * FROM tip_transactions"
    " WHERE tipper_id = ?"
    " ORDER BY created_at DESC"
    " LIMIT ? OFFSET ?"
)

# ── Phase 12 Step 46: Distribution ──
SELECT_PREMIUM_READS_FOR_PERIOD = (
    "SELECT"
    "  pr.user_id AS reader_id,"
    "  a.author_id AS author_id,"
    "  COALESCE(pr.read_time_seconds, 0) AS read_time_seconds,"
    "  pr.article_id AS article_id"
    " FROM premium_article_reads pr"
    " JOIN articles a ON a.id = pr.article_id"
    " WHERE pr.created_at >= ? AND pr.created_at < ?"
)

SELECT_EARNINGS_BY_PERIOD = (
    "SELECT * FROM author_earnings"
    " WHERE period_type = 'monthly' AND period_start = ?"
    " ORDER BY total_earnings_cents DESC"
)

UPSERT_AUTHOR_EARNINGS_DISTRIBUTION = (
    "INSERT INTO author_earnings"
    " (id, author_id, period_type, period_start, period_end,"
    "  premium_read_revenue_cents, total_earnings_cents, net_earnings_cents,"
    "  platform_fee_cents, premium_reads_count, total_read_time_seconds,"
    "  articles_contributing, status)"
    " VALUES (?, ?, 'monthly', ?, ?, ?, ?, ?, 0, ?, ?, ?, 'confirmed')"
    " ON CONFLICT(author_id, period_type, period_start) DO UPDATE SET"
    " premium_read_revenue_cents = excluded.premium_read_revenue_cents,"
    " total_earnings_cents = excluded.total_earnings_cents,"
    " net_earnings_cents = excluded.net_earnings_cents,"
    " premium_reads_count = excluded.premium_reads_count,"
    " total_read_time_seconds = excluded.total_read_time_seconds,"
    " articles_contributing = excluded.articles_contributing,"
    " updated_at = datetime('now')"
)

INSERT_PENDING_PAYOUT = (
    "INSERT INTO author_payouts"
    " (id, author_id, amount_cents, currency, payout_method, status, period_start, period_end)"
    " VALUES (?, ?, ?, 'USD', 'stripe', 'pending', ?, ?)"
)
