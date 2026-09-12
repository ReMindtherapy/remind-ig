"""
ig.py — Instagram Graph API layer shared by pull.py (weekly) and deep_report.py.

THERE IS NO ACCESS TOKEN IN THIS REPOSITORY, AND THERE MUST NEVER BE ONE.
The token lives in the Claude cloud environment as an API credential. Anthropic's
proxy attaches `Authorization: Bearer ...` to requests to graph.facebook.com after
they leave the session, so nothing here sends a token and Claude never sees one.

Two rules this module exists to enforce:

1. PIN, DON'T DISCOVER. An earlier version walked me/accounts and took whatever
   Instagram account came back. On the first live run the Page was correctly
   linked but that edge served a stale cached response, and the agent reported a
   broken link that was in fact fine. We ask for the account we want.

2. DEGRADE, DON'T DIE. One unavailable metric must not take out a whole report —
   safe() records the failure in the payload so the brief can say "this was not
   available" instead of silently omitting it or crashing.
"""
import json, os, time, urllib.error, urllib.parse, urllib.request
from datetime import datetime, timedelta

BASE = "https://graph.facebook.com/v21.0/"

# PINNED. @remind.abad.
IG_ID = os.environ.get("IG_ID", "17841434173646667")

MEDIA_PAGE = 50           # per API page
COMMENTS_PER_POST = 30

# Backoff between retries. Tests set this to 0 — otherwise a suite that
# deliberately fails every call spends minutes asleep.
RETRY_WAIT = float(os.environ.get("IG_RETRY_WAIT", "5"))


class IGError(RuntimeError):
    """A failure we must not paper over."""


# ---------------------------------------------------------------- transport

def api(path, **params):
    url = BASE + path
    if params:
        url += "?" + urllib.parse.urlencode(params)
    try:
        with urllib.request.urlopen(url, timeout=60) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        try:
            msg = json.loads(e.read()).get("error", {}).get("message", "?")
        except Exception:
            msg = "http %s" % e.code
        return {"ERR": msg[:300]}
    except Exception as e:
        return {"ERR": str(e)[:300]}


def api_retry(path, attempts=3, wait=None, **params):
    """For calls where a transient failure should not end the run."""
    last = None
    for i in range(attempts):
        r = api(path, **params)
        if "ERR" not in r:
            return r
        last = r["ERR"]
        w = RETRY_WAIT if wait is None else wait
        if i < attempts - 1 and w:
            time.sleep(w * (i + 1))
    return {"ERR": last}


def safe(label, fn, into):
    """Run fn(); on failure record why in into['_unavailable'] and return None.
    A report that says "follower demographics were unavailable: <reason>" is
    honest. One that silently omits them is not."""
    try:
        r = fn()
        if isinstance(r, dict) and "ERR" in r:
            into.setdefault("_unavailable", {})[label] = r["ERR"]
            return None
        return r
    except Exception as e:
        into.setdefault("_unavailable", {})[label] = str(e)[:200]
        return None


# ---------------------------------------------------------------- account

def account():
    """Read the pinned account. No discovery."""
    r = api_retry(IG_ID, fields="id,username,followers_count,follows_count,"
                                "media_count,biography,website")
    if "ERR" in r:
        raise IGError(
            "Could not read Instagram account %s. The request reached "
            "graph.facebook.com and came back with: %s\n\n"
            "In rough order of likelihood:\n"
            "  1. A transient Meta error, or a setting changed in the last few "
            "minutes that has not propagated — wait and re-run before changing "
            "anything.\n"
            "  2. The token has expired (they last ~60 days) — see README.md.\n"
            "  3. The account is no longer linked to the ReMind Facebook Page, "
            "or is no longer a Business/Creator account." % (IG_ID, r["ERR"]))
    if r.get("id") != str(IG_ID):
        raise IGError("Asked for account %s, got %r. Refusing to report on an "
                      "account we were not pointed at." % (IG_ID, r.get("id")))
    return {"ig_id": r["id"], "username": r.get("username"),
            "followers": r.get("followers_count"),
            "following": r.get("follows_count"),
            "media_count": r.get("media_count"),
            "bio": r.get("biography"), "website": r.get("website")}


# ---------------------------------------------------------------- audience

DEMO_BREAKDOWNS = ("gender", "age", "city", "country")


def demographics(into, timeframe="this_month"):
    """Who follows them vs who actually engages.

    This is the block that answers "our Reels reached the wrong people". Comparing
    engaged_audience_demographics against follower_demographics shows whether the
    audience Instagram is serving them to matches the audience they want.

    Requires >=100 followers; Meta returns nothing below that.
    """
    out = {"timeframe": timeframe}
    for metric in ("follower_demographics", "engaged_audience_demographics"):
        out[metric] = {}
        for br in DEMO_BREAKDOWNS:
            r = safe("%s/%s" % (metric, br),
                     lambda m=metric, b=br: api_retry(
                         "%s/insights" % IG_ID, metric=m, period="lifetime",
                         timeframe=timeframe, metric_type="total_value",
                         breakdown=b),
                     into)
            out[metric][br] = _flatten_breakdown(r) if r else None
    return out


def _flatten_breakdown(r):
    """Graph returns breakdowns nested in total_value.breakdowns[].results[].
    Flatten to {dimension_value: count} so a prompt can read it."""
    try:
        tv = r["data"][0]["total_value"]
        if "breakdowns" not in tv:
            return {"_total": tv.get("value")}
        out = {}
        for b in tv["breakdowns"]:
            for res in b.get("results", []):
                key = "/".join(res.get("dimension_values", []))
                out[key] = res.get("value")
        return out
    except Exception:
        return None


def account_activity(into, days=7):
    """Account-level totals for the window: reach, profile visits, follows.

    profile_views and follows are the metrics that matter for a practice — they
    are the closest thing to intent the API exposes. Reach without profile views
    is the signature of the wrong audience.
    """
    since = int((datetime.utcnow() - timedelta(days=days)).timestamp())
    until = int(datetime.utcnow().timestamp())
    out = {"days": days}
    for metric in ("reach", "profile_views", "accounts_engaged",
                   "total_interactions", "follows_and_unfollows", "views"):
        r = safe("activity/%s" % metric,
                 lambda m=metric: api_retry(
                     "%s/insights" % IG_ID, metric=m, period="day",
                     metric_type="total_value", since=since, until=until),
                 into)
        if r:
            try:
                out[metric] = r["data"][0]["total_value"]["value"]
            except Exception:
                out[metric] = None
    return out


# ---------------------------------------------------------------- media

def media(limit_pages=6, since=None):
    """All posts, paginated, newest first. since = datetime cutoff."""
    posts, url_params = [], dict(
        limit=MEDIA_PAGE,
        fields="id,caption,media_type,media_product_type,permalink,timestamp,"
               "like_count,comments_count")
    r = api_retry("%s/media" % IG_ID, **url_params)
    pages = 0
    while True:
        if "ERR" in r:
            raise IGError("Could not list posts: %s" % r["ERR"])
        batch = r.get("data", [])
        posts.extend(batch)
        pages += 1
        nxt = (r.get("paging") or {}).get("next")
        if not nxt or pages >= limit_pages or not batch:
            break
        if since and batch:
            oldest = _dt(batch[-1].get("timestamp"))
            if oldest and oldest < since:
                break
        try:
            with urllib.request.urlopen(nxt, timeout=60) as resp:
                r = json.loads(resp.read())
        except Exception as e:
            r = {"ERR": str(e)[:200]}
    return posts


POST_METRICS = "views,reach,likes,comments,shares,saved,total_interactions"


def enrich(raw_posts, into, with_comments=True):
    """Attach insights and (optionally) comments to each post."""
    out = []
    for it in raw_posts:
        cap = (it.get("caption") or "").replace("\n", " ").strip()
        p = {"id": it["id"], "posted_at": it.get("timestamp"),
             "type": it.get("media_product_type") or it.get("media_type"),
             "permalink": it.get("permalink"),
             "name": cap[:90] or "(no caption)",
             "caption": cap[:600],
             "caption_len": len(cap),
             "likes": it.get("like_count"),
             "comments_count": it.get("comments_count")}

        ins = api("%s/insights" % it["id"], metric=POST_METRICS)
        if "ERR" not in ins:
            for x in ins.get("data", []):
                try:
                    p[x["name"]] = x["values"][0]["value"]
                except Exception:
                    pass
        else:
            into.setdefault("_unavailable", {})["insights/%s" % it["id"]] = ins["ERR"]

        # The insights metric named "comments" is an int and would collide with
        # the comment list attached below. Park it.
        p["comment_interactions"] = p.pop("comments", None)

        reach = p.get("reach") or 0
        p["share_rate"] = _rate(p.get("shares"), reach)
        p["save_rate"] = _rate(p.get("saved"), reach)
        p["like_rate"] = _rate(p.get("likes"), reach)
        p["engagement_rate"] = _rate(p.get("total_interactions"), reach)

        p["comments"] = []
        if with_comments and (it.get("comments_count") or 0) > 0:
            p["comments"] = comments_for(it["id"], into)
        out.append(p)
    return out


def comments_for(media_id, into):
    """Comment text, classified.

    We DO read comment text here, and that is a deliberate change from the first
    version of this repo, which read only counts. The reason is safety: the
    practitioners were receiving unwanted advances in comments and DMs, and you
    cannot triage what you cannot see.

    The obligation that comes with it is in BRIEF.md and AUDIT.md: a commenter's
    personal disclosure is never quoted back, only characterised. Harassment may
    be quoted, because they need to know what to report.
    """
    c = api("%s/comments" % media_id, limit=COMMENTS_PER_POST,
            fields="id,text,timestamp,like_count,replies{id,text,timestamp}")
    if "ERR" in c:
        into.setdefault("_unavailable", {})["comments/%s" % media_id] = c["ERR"]
        return []
    out = []
    for x in c.get("data", []):
        text = (x.get("text") or "")[:300]
        reps = (x.get("replies") or {}).get("data", [])
        out.append({
            "text": text,
            "at": x.get("timestamp"),
            # The API does not return `username` on comments (privacy), so a
            # reply cannot be attributed. On your own post a reply is almost
            # always the owner's — treat "has a reply" as "handled".
            "already_replied": bool(reps),
            "kind": classify(text),
        })
    return out


# ------------------------------------------------------- comment triage

# Deliberately conservative and transparent. This is a first-pass sort so the
# model and the clinicians can see the shape of the inbox; it is NOT a judgement
# about any individual. Anything uncertain lands in "other" and gets read.
_ADVANCE = ("i love you", "love u", "luv u", "marry me", "beautiful", "gorgeous",
            "sexy", "hot", "cute", "pretty", "handsome", "gf", "girlfriend",
            "boyfriend", "dm me", "inbox me", "hi dear", "hello dear", "frndship",
            "friendship", "frnd", "wanna talk", "ur no", "your number", "num plz")
_ABUSE = ("fake", "fraud", "scam", "stupid", "idiot", "nonsense", "shut up",
          "useless", "bakwas", "chutiya", "pagal")
_QUESTION = ("?", "how much", "fees", "fee", "charge", "cost", "price", "book",
             "appointment", "session", "timing", "online", "offline", "address",
             "contact", "available", "kaise", "kitna", "kya")
_PRAISE = ("nice", "good", "great", "amazing", "love this", "helpful", "true",
           "so true", "needed this", "thank")


def classify(text):
    """-> 'advance' | 'abuse' | 'question' | 'praise' | 'other'

    Order matters: unwanted advances and abuse are checked first, because a
    message that is both a compliment and an advance ("beautiful, dm me") is an
    advance for triage purposes.
    """
    t = (text or "").lower().strip()
    if not t:
        return "other"
    if any(k in t for k in _ADVANCE):
        return "advance"
    if any(k in t for k in _ABUSE):
        return "abuse"
    if any(k in t for k in _QUESTION):
        return "question"
    if any(k in t for k in _PRAISE) and len(t) < 60:
        return "praise"
    if _emoji_only(t):
        return "praise"
    return "other"


def _emoji_only(t):
    stripped = "".join(ch for ch in t if ch.isalnum())
    return not stripped and len(t) > 0


def comment_summary(posts):
    """Counts by kind across all posts, plus the audience-safety signal."""
    kinds = {}
    total = 0
    for p in posts:
        for c in p.get("comments", []):
            kinds[c["kind"]] = kinds.get(c["kind"], 0) + 1
            total += 1
    unwanted = kinds.get("advance", 0) + kinds.get("abuse", 0)
    return {"total_read": total, "by_kind": kinds,
            "unwanted": unwanted,
            "unwanted_share": round(unwanted / total, 3) if total else None,
            "open_questions": sum(
                1 for p in posts for c in p.get("comments", [])
                if c["kind"] == "question" and not c["already_replied"])}


# ---------------------------------------------------------------- helpers

def _rate(n, d):
    return round((n or 0) / d, 4) if d else None


def _dt(ts):
    try:
        return datetime.strptime((ts or "")[:19], "%Y-%m-%dT%H:%M:%S")
    except Exception:
        return None


def totals(posts):
    if not posts:
        return {"posts": 0}
    tot = lambda k: sum(p.get(k) or 0 for p in posts)
    reach = tot("reach")
    n = len(posts)
    return {"posts": n, "reach": reach, "views": tot("views"),
            "likes": tot("likes"), "shares": tot("shares"),
            "saves": tot("saved"), "comments": tot("comments_count"),
            "share_rate": _rate(tot("shares"), reach),
            "save_rate": _rate(tot("saved"), reach),
            "like_rate": _rate(tot("likes"), reach),
            "reach_per_post": round(reach / n) if n else None}


def split_window(posts, days=7):
    """(this window, everything older) by posted_at."""
    cut = datetime.utcnow() - timedelta(days=days)
    cur, old = [], []
    for p in posts:
        t = _dt(p.get("posted_at"))
        (cur if (t and t >= cut) else old).append(p)
    return cur, old
