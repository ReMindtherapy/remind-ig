"""
pull.py — fetch this week's Instagram numbers for ReMind and print them as JSON.

Run it with no arguments:   python3 pull.py

THERE IS NO ACCESS TOKEN IN THIS FILE, AND THERE MUST NEVER BE ONE.

The token lives in the Claude cloud environment as an API credential. Anthropic's
proxy adds the `Authorization: Bearer ...` header to every request to
graph.facebook.com after it leaves the session, so this script sends no token and
Claude never sees one. If you ever find yourself pasting a token in here, stop —
it would end up in git.

Output is JSON on stdout: account, this week's posts, a baseline of older posts,
and totals for both. Claude reads that and writes the brief.
"""
import json, sys, urllib.error, urllib.parse, urllib.request
from datetime import datetime, timedelta

BASE = "https://graph.facebook.com/v21.0/"
MEDIA_LIMIT = 50          # plenty for a young account
WEEK_DAYS = 7
BASELINE_DAYS = 180


def api(path, **params):
    url = BASE + path
    if params:
        url += "?" + urllib.parse.urlencode(params)
    try:
        with urllib.request.urlopen(url, timeout=45) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        try:
            msg = json.loads(e.read()).get("error", {}).get("message", "?")
        except Exception:
            msg = "http %s" % e.code
        return {"ERR": msg[:300]}
    except Exception as e:
        return {"ERR": str(e)[:300]}


def die(msg):
    """Fail loudly. A brief built from missing data is worse than no brief."""
    print(json.dumps({"error": msg}, indent=1))
    sys.exit(1)


def find_account():
    r = api("me/accounts", limit=25,
            fields="id,name,instagram_business_account"
                   "{id,username,followers_count,media_count}")
    if "ERR" in r:
        die("Could not reach the Instagram API: %s. Most likely the token has "
            "expired — see README.md, 'Every 60 days'." % r["ERR"])

    found = []
    for page in r.get("data", []):
        ig = page.get("instagram_business_account")
        if ig:
            found.append({"page": page.get("name"), "ig_id": ig["id"],
                          "username": ig.get("username"),
                          "followers": ig.get("followers_count"),
                          "media_count": ig.get("media_count")})
    if not found:
        die("The token works but no Instagram Business account is linked to any "
            "Page. Check that the Instagram account is set to Business or Creator "
            "and is connected to the ReMind Facebook Page.")
    return found[0]


def pull_posts(ig_id):
    m = api("%s/media" % ig_id, limit=MEDIA_LIMIT,
            fields="id,caption,media_type,media_product_type,permalink,timestamp,"
                   "like_count,comments_count")
    if "ERR" in m:
        die("Could not list posts: %s" % m["ERR"])

    posts = []
    for it in m.get("data", []):
        cap = (it.get("caption") or "").replace("\n", " ").strip()
        p = {"posted_at": it.get("timestamp"),
             "type": it.get("media_product_type") or it.get("media_type"),
             "permalink": it.get("permalink"),
             "name": cap[:90] or "(no caption)",     # first line = the post's name
             "caption": cap[:400],
             "likes": it.get("like_count"),
             "comments_count": it.get("comments_count")}

        ins = api("%s/insights" % it["id"],
                  metric="views,reach,likes,comments,shares,saved,total_interactions")
        if "ERR" not in ins:
            for x in ins.get("data", []):
                try:
                    p[x["name"]] = x["values"][0]["value"]
                except Exception:
                    pass

        # The insights metric named "comments" is an int; keep it from being
        # mistaken for a list of comment text further down the pipeline.
        p["comment_interactions"] = p.pop("comments", None)

        reach = p.get("reach") or 0
        p["share_rate"] = round((p.get("shares") or 0) / reach, 4) if reach else None
        p["save_rate"] = round((p.get("saved") or 0) / reach, 4) if reach else None
        posts.append(p)
    return posts


def totals(posts):
    if not posts:
        return {"posts": 0}
    tot = lambda k: sum(p.get(k) or 0 for p in posts)
    reach = tot("reach")
    return {"posts": len(posts), "reach": reach, "views": tot("views"),
            "likes": tot("likes"), "shares": tot("shares"), "saves": tot("saved"),
            "comments": tot("comments_count"),
            "share_rate": round(tot("shares") / reach, 4) if reach else None,
            "save_rate": round(tot("saved") / reach, 4) if reach else None,
            "reach_per_post": round(reach / len(posts))}


def main():
    acct = find_account()
    posts = pull_posts(acct["ig_id"])
    if not posts:
        die("No posts came back for @%s. If the account really has posted, this is "
            "an API problem — do not report it as 'a quiet week'." % acct["username"])

    now = datetime.utcnow()
    week_start = now - timedelta(days=WEEK_DAYS)
    base_start = now - timedelta(days=BASELINE_DAYS)

    def when(p):
        try:
            return datetime.strptime((p.get("posted_at") or "")[:19], "%Y-%m-%dT%H:%M:%S")
        except Exception:
            return None

    this_week, baseline = [], []
    for p in posts:
        t = when(p)
        if t and t >= week_start:
            this_week.append(p)
        elif t and t >= base_start:
            baseline.append(p)

    oldest = min([w for w in (when(p) for p in posts) if w], default=now)
    account_age_days = (now - oldest).days

    print(json.dumps({
        "pulled_at": now.isoformat(timespec="seconds") + "Z",
        "account": acct,
        "account_history_days": account_age_days,
        "enough_history_for_trend": account_age_days >= 60 and len(baseline) >= 8,
        "this_week": totals(this_week),
        "baseline": totals(baseline),
        "this_week_posts": this_week,
        "baseline_posts": baseline[:15],
    }, indent=1, default=str))


if __name__ == "__main__":
    main()
