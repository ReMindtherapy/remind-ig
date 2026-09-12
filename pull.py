"""
pull.py — the weekly pull for ReMind. Prints JSON on stdout.

  python3 pull.py

Claude reads that JSON, follows BRIEF.md, and writes the Monday brief.

What it collects, and why each piece is here:

  account          who we are pinned to, follower count
  activity         reach, PROFILE VIEWS and follows for the week. Profile views
                   are the closest thing to intent the API gives us — reach with
                   no profile views is the signature of the wrong audience.
  audience         follower demographics vs ENGAGED audience demographics. This
                   is the block that tells them whether Instagram is serving
                   their Reels to the people they want to reach.
  posts            per-post metrics and rates
  comments         text, triaged into question / advance / abuse / praise, so
                   unwanted contact is visible and countable rather than just
                   felt.

No access token appears in this repository. See README.md.
"""
import json, sys
from datetime import datetime

import ig

WEEK_DAYS = 7
BASELINE_DAYS = 180
TREND_MIN_DAYS = 60       # account must be this old...
TREND_MIN_POSTS = 8       # ...and have this many prior posts, to call a trend


def main():
    payload = {"pulled_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
               "window_days": WEEK_DAYS, "baseline_days": BASELINE_DAYS}

    try:
        acct = ig.account()
    except ig.IGError as e:
        print(json.dumps({"error": str(e)}, indent=1))
        sys.exit(1)
    payload["account"] = acct

    payload["activity"] = ig.account_activity(payload, days=WEEK_DAYS)
    payload["audience"] = ig.demographics(payload, timeframe="this_month")

    try:
        raw = ig.media(limit_pages=4)
    except ig.IGError as e:
        print(json.dumps({"error": str(e)}, indent=1))
        sys.exit(1)

    if not raw:
        print(json.dumps({"error":
            "No posts came back for @%s, which has media_count=%s. If the "
            "account really has posted, this is an API problem — do NOT report "
            "it as a quiet week." % (acct["username"], acct["media_count"])},
            indent=1))
        sys.exit(1)

    posts = ig.enrich(raw, payload, with_comments=True)
    this_week, baseline = ig.split_window(posts, days=WEEK_DAYS)

    oldest = min([d for d in (ig._dt(p.get("posted_at")) for p in posts) if d],
                 default=datetime.utcnow())
    history_days = (datetime.utcnow() - oldest).days

    payload.update({
        "account_history_days": history_days,
        "enough_history_for_trend":
            history_days >= TREND_MIN_DAYS and len(baseline) >= TREND_MIN_POSTS,
        "this_week": ig.totals(this_week),
        "baseline": ig.totals(baseline),
        "comment_summary": ig.comment_summary(posts),
        "this_week_posts": this_week,
        "baseline_posts": baseline[:15],
    })

    print(json.dumps(payload, indent=1, default=str))


if __name__ == "__main__":
    main()
