"""
test_agent.py — tests for the ReMind Instagram agent.

  python3 test_agent.py

No network. Every Graph API call is stubbed, so this runs anywhere, including in
a routine, and never touches the real account.

What these tests are protecting, in order of how much it would cost to get wrong:

  1. Nothing ever reports on an account we were not pinned to.
  2. A failure never becomes a confident empty report.
  3. An error message never asserts a cause it has not established — the first
     live run blamed the Facebook Page link for what was a stale cached response
     and cost an evening.
  4. Comment triage catches unwanted contact, which is a safety feature.
  5. No credential is ever committed to this repository.
"""
import io, json, contextlib, os, re, sys, traceback
from datetime import datetime, timedelta

import ig, pull, deep_report

HERE = os.path.dirname(os.path.abspath(__file__))
NOW = datetime.utcnow()
iso = lambda d: (NOW - timedelta(days=d)).strftime("%Y-%m-%dT%H:%M:%S+0000")

_results = []


def check(name, cond, detail=""):
    _results.append((name, bool(cond), detail))
    print("%s  %s%s" % ("PASS" if cond else "FAIL", name,
                        ("  — " + detail) if detail and not cond else ""))


def run(fn):
    """Capture stdout and any SystemExit from a main()."""
    buf = io.StringIO()
    code = 0
    try:
        with contextlib.redirect_stdout(buf):
            fn()
    except SystemExit as e:
        code = e.code
    return buf.getvalue(), code


# ---------------------------------------------------------------- fixtures

def fake_graph(posts=None, comments=None, account_id=None, fail=None,
               demo=True, media_empty=False):
    """Build a stub for ig.api covering every endpoint the agent calls."""
    posts = posts if posts is not None else [
        {"id": "m1", "caption": "Why so many people in India put off therapy",
         "media_product_type": "REELS", "permalink": "https://ig/1",
         "timestamp": iso(2), "like_count": 120, "comments_count": 4},
        {"id": "m2", "caption": "What actually happens in a first session",
         "media_product_type": "CAROUSEL_ALBUM", "permalink": "https://ig/2",
         "timestamp": iso(40), "like_count": 60, "comments_count": 1},
    ]
    comments = comments if comments is not None else [
        {"id": "c1", "text": "How much do you charge for a session?",
         "timestamp": iso(1), "replies": {"data": []}},
        {"id": "c2", "text": "i love you beautiful dm me", "timestamp": iso(1),
         "replies": {"data": []}},
        {"id": "c3", "text": "🔥🔥", "timestamp": iso(1),
         "replies": {"data": [{"id": "r", "text": "thanks", "timestamp": iso(1)}]}},
        {"id": "c4", "text": "I have been struggling since March and cannot sleep",
         "timestamp": iso(1), "replies": {"data": []}},
    ]

    def _api(path, **p):
        if fail:
            return {"ERR": fail}
        if path == ig.IG_ID:
            return {"id": account_id or ig.IG_ID, "username": "remind.abad",
                    "followers_count": 248, "follows_count": 12, "media_count": 7,
                    "biography": "Trauma informed therapy", "website": "https://x"}
        if path.endswith("/media"):
            return {"data": [] if media_empty else posts}
        if path.endswith("/insights") and path.startswith(ig.IG_ID):
            m = p.get("metric", "")
            if "demographics" in m:
                if not demo:
                    return {"ERR": "not enough followers"}
                br = p.get("breakdown")
                vals = {"gender": [("M", 700), ("F", 300)] if m.startswith("engaged")
                                  else [("M", 90), ("F", 158)],
                        "age": [("18-24", 120), ("25-34", 128)],
                        "city": [("Ahmedabad", 140)],
                        "country": [("IN", 240)]}[br]
                return {"data": [{"total_value": {"breakdowns": [
                    {"results": [{"dimension_values": [k], "value": v}
                                 for k, v in vals]}]}}]}
            return {"data": [{"total_value": {"value": 15646}}]}
        if path.endswith("/insights"):
            return {"data": [{"name": "reach", "values": [{"value": 3129}]},
                             {"name": "views", "values": [{"value": 4000}]},
                             {"name": "shares", "values": [{"value": 17}]},
                             {"name": "saved", "values": [{"value": 4}]},
                             {"name": "comments", "values": [{"value": 4}]},
                             {"name": "total_interactions", "values": [{"value": 145}]}]}
        if path.endswith("/comments"):
            return {"data": comments}
        return {"ERR": "unexpected path %s" % path}
    return _api


# ---------------------------------------------------------------- 1. pinning

def test_pinning():
    ig.api = fake_graph()
    a = ig.account()
    check("pinned account is read directly", a["ig_id"] == ig.IG_ID)
    check("pinned account carries follower count", a["followers"] == 248)

    # The whole point: if Graph hands back a different account, refuse.
    ig.api = fake_graph(account_id="99999999")
    try:
        ig.account()
        check("refuses a mismatched account", False, "no IGError raised")
    except ig.IGError as e:
        check("refuses a mismatched account", "not pointed at" in str(e))

    # And we must never call me/accounts again — that edge is cached and lied.
    calls = []
    base = fake_graph()
    ig.api = lambda path, **p: (calls.append(path), base(path, **p))[1]
    ig.account()
    check("never calls me/accounts", not any("me/accounts" in c for c in calls),
          "called: %s" % calls)


# ------------------------------------------------------- 2. honest failure

def test_no_false_emptiness():
    ig.api = fake_graph(fail="Please reduce the amount of data you're asking for")
    out, code = run(pull.main)
    check("transient failure exits non-zero", code == 1)
    err = json.loads(out)["error"]
    check("does not blame the Page link",
          "no Instagram Business account is linked" not in err)
    check("offers transient cause first",
          err.index("transient") < err.index("expired") < err.index("no longer linked"))

    ig.api = fake_graph(media_empty=True)
    out, code = run(pull.main)
    check("empty media list is a failure, not a quiet week", code == 1)
    check("empty-media message says it is probably an API problem",
          "API problem" in json.loads(out)["error"])

    ig.api = fake_graph(media_empty=True)
    out, code = run(lambda: deep_report.main())
    check("deep report also refuses to audit an empty account", code == 1)


def test_degrades_not_dies():
    """One unavailable metric must not take out the run — it must be recorded."""
    ig.api = fake_graph(demo=False)
    out, code = run(pull.main)
    check("survives unavailable demographics", code == 0)
    d = json.loads(out)
    check("records why the metric was unavailable",
          bool(d.get("_unavailable")) and
          any("demographics" in k for k in d["_unavailable"]),
          str(d.get("_unavailable"))[:120])


# ------------------------------------------------------- 3. comment triage

def test_classify():
    cases = {
        "i love you beautiful": "advance",
        "dm me dear": "advance",
        "send your number": "advance",
        "your number please": "advance",
        # Genuinely ambiguous text must land in 'other' and get read by a human,
        # rather than being confidently mis-sorted either way.
        "can we talk": "other",
        "this is fake and a scam": "abuse",
        "How much do you charge?": "question",
        "what are your timings": "question",
        "kitna charge karte ho": "question",
        "so true, needed this": "praise",
        "🔥🔥": "praise",
        "I have been struggling since March": "other",
    }
    bad = {t: (ig.classify(t), want) for t, want in cases.items()
           if ig.classify(t) != want}
    check("comment classifier", not bad, str(bad))

    # An advance dressed as a compliment must triage as an advance.
    check("compliment + advance triages as advance",
          ig.classify("gorgeous, dm me") == "advance")


def test_comment_summary():
    ig.api = fake_graph()
    payload = {}
    posts = ig.enrich(ig.media(), payload)
    s = ig.comment_summary(posts)
    check("counts unwanted contact", s["unwanted"] >= 2, str(s))
    check("computes unwanted share", 0 < s["unwanted_share"] <= 1, str(s))
    check("counts unanswered questions", s["open_questions"] >= 1, str(s))
    check("an answered comment is not an open question",
          s["open_questions"] < s["total_read"])


# ------------------------------------------------------- 4. audience fit

def test_audience_fit():
    ig.api = fake_graph()
    out, code = run(pull.main)
    check("weekly pull succeeds", code == 0, out[:200])
    d = json.loads(out)
    fol = d["audience"]["follower_demographics"]["gender"]
    eng = d["audience"]["engaged_audience_demographics"]["gender"]
    check("follower gender breakdown flattened", fol == {"M": 90, "F": 158}, str(fol))
    check("engaged gender breakdown flattened", eng == {"M": 700, "F": 300}, str(eng))

    fit = deep_report.audience_fit(d)
    check("computes gender skew", "gender_skew" in fit, str(fit)[:150])
    # Followers are majority women; engagement is majority men. That mismatch is
    # the entire problem, and it must show up as a large positive M skew.
    check("detects the wrong-audience mismatch",
          fit["gender_skew"]["M"] > 0.3,
          "skew=%s" % fit.get("gender_skew"))


# ------------------------------------------------------- 5. trend gating

def test_trend_gate():
    ig.api = fake_graph()
    out, _ = run(pull.main)
    d = json.loads(out)
    check("young account does not claim a trend",
          d["enough_history_for_trend"] is False)

    many = [{"id": "p%d" % i, "caption": "post %d about anxiety" % i,
             "media_product_type": "REELS", "permalink": "https://ig/%d" % i,
             "timestamp": iso(20 + i * 5), "like_count": 10, "comments_count": 0}
            for i in range(12)]
    many.append({"id": "new", "caption": "this week", "media_product_type": "REELS",
                 "permalink": "https://ig/new", "timestamp": iso(1),
                 "like_count": 5, "comments_count": 0})
    ig.api = fake_graph(posts=many)
    out, _ = run(pull.main)
    check("mature account does claim a trend",
          json.loads(out)["enough_history_for_trend"] is True)


# ------------------------------------------------------- 6. deep report

def test_deep_report():
    ig.api = fake_graph()
    out, code = run(lambda: deep_report.main())
    check("deep report runs", code == 0, out[:200])
    d = json.loads(out)
    for block in ("by_month", "by_format", "by_topic", "by_hour_ist", "by_weekday",
                  "audience_fit", "unwanted_by_month", "hygiene",
                  "posts_attracting_unwanted_contact", "top_by_save_rate"):
        check("deep report has %s" % block, block in d)
    check("topic tagging finds therapy myths",
          "therapy_myths" in d["by_topic"] or "how_therapy_works" in d["by_topic"],
          str(list(d["by_topic"])))
    check("names posts that attract unwanted contact",
          len(d["posts_attracting_unwanted_contact"]) >= 1)


def test_hygiene_typo_detection():
    """The remimd/remind case: two near-identical addresses in live captions."""
    posts = [
        {"id": "a", "caption": "reach us at remindstartyourjourney@gmail.com",
         "media_product_type": "IMAGE", "permalink": "https://ig/a",
         "timestamp": iso(5), "like_count": 1, "comments_count": 0},
        {"id": "b", "caption": "reach us at remimdstartyourjourney@gmail.com",
         "media_product_type": "IMAGE", "permalink": "https://ig/b",
         "timestamp": iso(6), "like_count": 1, "comments_count": 0},
    ]
    ig.api = fake_graph(posts=posts)
    payload = {}
    enriched = ig.enrich(ig.media(), payload)
    h = deep_report.hygiene(enriched, {})
    check("finds both contact addresses", len(h["contact_addresses_found"]) == 2)
    check("flags the near-duplicate as a likely typo",
          any("typo" in i["issue"] for i in h["issues"]),
          str(h["issues"])[:200])

    # A single address must NOT be flagged.
    ig.api = fake_graph(posts=posts[:1])
    h2 = deep_report.hygiene(ig.enrich(ig.media(), {}), {})
    check("does not cry typo on a single address",
          not any("typo" in i["issue"] for i in h2["issues"]))


def test_hygiene_other_issues():
    posts = [
        {"id": "x", "caption": "", "media_product_type": "REELS",
         "permalink": "https://ig/x", "timestamp": iso(3),
         "like_count": 1, "comments_count": 0},
        {"id": "y", "caption": "#a #b #c #d #e #f #g", "media_product_type": "REELS",
         "permalink": "https://ig/y", "timestamp": iso(4),
         "like_count": 1, "comments_count": 0},
    ]
    ig.api = fake_graph(posts=posts)
    h = deep_report.hygiene(ig.enrich(ig.media(), {}), {})
    kinds = " ".join(i["issue"] for i in h["issues"])
    check("flags a missing caption", "no caption" in kinds)
    check("flags hashtag overuse", "hashtags" in kinds)


# ------------------------------------------------------- 7. no credentials

def test_no_credentials_in_repo():
    pat = re.compile(r"EAA[A-Za-z0-9]{20,}|access_token\s*=\s*['\"]|"
                     r"client_secret\s*=\s*['\"]")
    offenders = []
    for fn in sorted(os.listdir(HERE)):
        if not fn.endswith((".py", ".md", ".txt", ".json", ".yml", ".yaml")):
            continue
        body = open(os.path.join(HERE, fn), encoding="utf-8").read()
        if pat.search(body):
            offenders.append(fn)
    check("no credential-shaped string in any tracked file", not offenders,
          "check: %s" % offenders)

    src = open(os.path.join(HERE, "ig.py")).read()
    check("ig.py never sends an access_token parameter",
          "access_token" not in src.replace("access_token parameter", ""))


# ---------------------------------------------------------------- rates

def test_rates():
    check("rate divides by reach", ig._rate(17, 3129) == round(17 / 3129, 4))
    check("rate on zero reach is None, not a crash", ig._rate(5, 0) is None)
    check("rate on missing numerator is 0.0", ig._rate(None, 100) == 0.0)
    t = ig.totals([{"reach": 100, "shares": 5, "saved": 2, "likes": 10,
                    "views": 200, "comments_count": 1}])
    check("totals computes share rate", t["share_rate"] == 0.05, str(t))
    check("totals on empty list is safe", ig.totals([]) == {"posts": 0})


# ---------------------------------------------------------------- main

def main():
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for t in tests:
        print("\n--- %s ---" % t.__name__)
        try:
            t()
        except Exception:
            check(t.__name__ + " raised", False, traceback.format_exc()[-300:])

    passed = sum(1 for _, ok, _ in _results if ok)
    total = len(_results)
    print("\n" + "=" * 60)
    print("%d/%d passed" % (passed, total))
    for name, ok, detail in _results:
        if not ok:
            print("  FAIL  %s  %s" % (name, detail[:200]))
    print("=" * 60)
    sys.exit(0 if passed == total else 1)


if __name__ == "__main__":
    main()
