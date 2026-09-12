"""
deep_report.py — the one-off strategic audit. Run it when you want the full
picture rather than the weekly diff.

  python3 deep_report.py            # 6 months
  python3 deep_report.py --months 12

Prints JSON on stdout. Claude reads it, follows AUDIT.md, does live research on
what mental-health practices post in India and elsewhere, and writes the report.

The weekly brief answers "what happened last week". This answers a different set
of questions:

  * Who is Instagram actually showing this account to, and is that the audience
    they want? (the audience-fit block)
  * Which formats and subjects earn saves — the signal that matters for a
    practice — rather than reach?
  * How much of the incoming contact is unwanted, and is it getting worse?
  * When do they post, how often, and does any of it correlate with anything?
  * What is broken or embarrassing in what is already published?

Re-run it any time. It is not scheduled — this is a report you commission.
"""
import argparse, json, re, sys
from collections import Counter, defaultdict
from datetime import datetime, timedelta

import ig


def month_of(p):
    t = ig._dt(p.get("posted_at"))
    return t.strftime("%Y-%m") if t else "unknown"


def hour_ist(p):
    """Posted hour in IST. Instagram timestamps are UTC; India is UTC+5:30."""
    t = ig._dt(p.get("posted_at"))
    return (t + timedelta(hours=5, minutes=30)).hour if t else None


def weekday(p):
    t = ig._dt(p.get("posted_at"))
    return t.strftime("%A") if t else None


def by(posts, keyfn):
    """Group and total. Used for month / format / weekday / hour cuts."""
    groups = defaultdict(list)
    for p in posts:
        groups[keyfn(p)].append(p)
    return {str(k): ig.totals(v) for k, v in sorted(groups.items(),
                                                    key=lambda kv: str(kv[0]))}


# Topic tagging is keyword-based and deliberately crude. It exists to give the
# model a starting hypothesis about subject matter, not to be authoritative —
# AUDIT.md tells it to read the captions itself and correct this.
TOPICS = {
    "anxiety":       ("anxiety", "anxious", "panic", "worry", "overthink"),
    "depression":    ("depress", "low mood", "sad", "hopeless"),
    "relationships": ("relationship", "partner", "couple", "marriage", "boundary",
                      "boundaries", "family", "parents"),
    "trauma":        ("trauma", "ptsd", "abuse", "childhood"),
    "therapy_myths": ("myth", "misconception", "stigma", "log kya kahenge",
                      "what will people say", "need therapy"),
    "how_therapy_works": ("session", "first session", "what happens", "process",
                          "confidential", "cbt", "evidence"),
    "self_care":     ("sleep", "routine", "breathe", "breathing", "journal",
                      "grounding", "self care", "self-care"),
    "work_stress":   ("work", "burnout", "job", "career", "student", "exam"),
    "addiction":     ("addiction", "de-addiction", "substance", "gaming", "phone"),
}


def topics_of(p):
    cap = (p.get("caption") or "").lower()
    hits = [t for t, kws in TOPICS.items() if any(k in cap for k in kws)]
    return hits or ["untagged"]


def topic_table(posts):
    agg = defaultdict(list)
    for p in posts:
        for t in topics_of(p):
            agg[t].append(p)
    return {t: ig.totals(v) for t, v in sorted(agg.items())}


CONTACT_RE = re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+")
URL_RE = re.compile(r"https?://\S+|www\.\S+")


def hygiene(posts, acct):
    """Mechanical problems in what is already published. Cheap to find, and
    embarrassing to leave — a misspelt contact address in a live caption sends
    people to a mailbox nobody reads."""
    issues = []
    emails = Counter()
    for p in posts:
        cap = p.get("caption") or ""
        for e in CONTACT_RE.findall(cap):
            emails[e.lower()] += 1
        if not cap.strip():
            issues.append({"post": p["name"], "permalink": p.get("permalink"),
                           "issue": "no caption at all — nothing for Instagram to "
                                    "index and nothing for a reader to act on"})
        if len(cap) < 40 and cap.strip():
            issues.append({"post": p["name"], "permalink": p.get("permalink"),
                           "issue": "caption under 40 characters — very little "
                                    "topical signal for the recommendation system"})
        if "#" in cap and cap.count("#") > 5:
            issues.append({"post": p["name"], "permalink": p.get("permalink"),
                           "issue": "more than 5 hashtags — hashtags no longer "
                                    "help reach and may slightly hurt it"})

    # Near-duplicate contact addresses are almost always typos. This is how the
    # remimd/remind misspelling was caught.
    if len(emails) > 1:
        variants = list(emails)
        for a in variants:
            for b in variants:
                if a < b and _close(a, b):
                    issues.append({
                        "post": "(multiple)", "permalink": None,
                        "issue": "two near-identical contact addresses appear in "
                                 "captions: %r and %r. One is almost certainly a "
                                 "typo sending people to a dead mailbox." % (a, b)})
    return {"contact_addresses_found": dict(emails), "issues": issues}


def _close(a, b):
    """Cheap edit-distance-1-ish check for typo'd addresses."""
    if abs(len(a) - len(b)) > 1:
        return False
    diffs = sum(1 for x, y in zip(a, b) if x != y)
    return diffs <= 2


def audience_fit(payload):
    """Turn the demographics blocks into the single question that matters:
    does the audience Instagram engages match the audience they want?"""
    aud = payload.get("audience") or {}
    fol = (aud.get("follower_demographics") or {}).get("gender")
    eng = (aud.get("engaged_audience_demographics") or {}).get("gender")
    out = {"follower_gender": fol, "engaged_gender": eng}

    if fol and eng:
        def pct(d):
            tot = sum(v for v in d.values() if isinstance(v, (int, float)))
            return {k: round(v / tot, 3) for k, v in d.items()
                    if isinstance(v, (int, float))} if tot else {}
        fp, ep = pct(fol), pct(eng)
        out["follower_gender_pct"] = fp
        out["engaged_gender_pct"] = ep
        out["gender_skew"] = {
            k: round(ep.get(k, 0) - fp.get(k, 0), 3) for k in set(fp) | set(ep)}
        out["note"] = ("gender_skew is engaged-share minus follower-share. A "
                       "large positive number for one gender means Instagram is "
                       "serving this content to people who are not the existing "
                       "audience — the mechanism behind reach that produces no "
                       "bookings.")
    out["age"] = {
        "followers": (aud.get("follower_demographics") or {}).get("age"),
        "engaged": (aud.get("engaged_audience_demographics") or {}).get("age")}
    out["city"] = {
        "followers": (aud.get("follower_demographics") or {}).get("city"),
        "engaged": (aud.get("engaged_audience_demographics") or {}).get("city")}
    return out


def unwanted_over_time(posts):
    """Is unwanted contact getting worse? Grouped by month so a trend is visible
    rather than a single alarming week."""
    per = defaultdict(lambda: {"comments": 0, "unwanted": 0})
    for p in posts:
        m = month_of(p)
        for c in p.get("comments", []):
            per[m]["comments"] += 1
            if c["kind"] in ("advance", "abuse"):
                per[m]["unwanted"] += 1
    for m, d in per.items():
        d["unwanted_share"] = round(d["unwanted"] / d["comments"], 3) if d["comments"] else None
    return dict(sorted(per.items()))


def worst_offending_posts(posts, n=5):
    """Posts that attracted the most unwanted contact — the ones whose framing
    or subject is pulling the wrong audience."""
    scored = []
    for p in posts:
        bad = sum(1 for c in p.get("comments", [])
                  if c["kind"] in ("advance", "abuse"))
        if bad:
            scored.append({"name": p["name"], "permalink": p.get("permalink"),
                           "type": p.get("type"), "reach": p.get("reach"),
                           "unwanted_comments": bad,
                           "saves": p.get("saved"), "save_rate": p.get("save_rate")})
    return sorted(scored, key=lambda x: -x["unwanted_comments"])[:n]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--months", type=int, default=6)
    args = ap.parse_args()

    payload = {"pulled_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
               "report": "deep", "months_requested": args.months}

    try:
        payload["account"] = ig.account()
    except ig.IGError as e:
        print(json.dumps({"error": str(e)}, indent=1)); sys.exit(1)

    since = datetime.utcnow() - timedelta(days=31 * args.months)
    payload["activity_7d"] = ig.account_activity(payload, days=7)
    payload["activity_28d"] = ig.account_activity(payload, days=28)
    payload["audience"] = ig.demographics(payload, timeframe="this_month")
    payload["audience_prev_month"] = ig.demographics(payload, timeframe="prev_month")

    try:
        raw = ig.media(limit_pages=8, since=since)
    except ig.IGError as e:
        print(json.dumps({"error": str(e)}, indent=1)); sys.exit(1)

    if not raw:
        print(json.dumps({"error":
            "No posts returned. Refusing to write an audit of an account that "
            "appears empty — this is far more likely to be an API failure."},
            indent=1))
        sys.exit(1)

    posts = ig.enrich(raw, payload, with_comments=True)
    posts = [p for p in posts
             if (ig._dt(p.get("posted_at")) or datetime.utcnow()) >= since]

    oldest = min([d for d in (ig._dt(p.get("posted_at")) for p in posts) if d],
                 default=datetime.utcnow())

    payload.update({
        "history_days": (datetime.utcnow() - oldest).days,
        "post_count": len(posts),
        "overall": ig.totals(posts),
        "by_month": by(posts, month_of),
        "by_format": by(posts, lambda p: p.get("type") or "unknown"),
        "by_weekday": by(posts, weekday),
        "by_hour_ist": by(posts, hour_ist),
        "by_topic": topic_table(posts),
        "audience_fit": audience_fit(payload),
        "comment_summary": ig.comment_summary(posts),
        "unwanted_by_month": unwanted_over_time(posts),
        "posts_attracting_unwanted_contact": worst_offending_posts(posts),
        "hygiene": hygiene(posts, payload["account"]),
        "top_by_save_rate": sorted(
            [p for p in posts if p.get("save_rate") is not None],
            key=lambda p: -p["save_rate"])[:8],
        "top_by_reach": sorted(posts, key=lambda p: -(p.get("reach") or 0))[:8],
        "all_posts": posts,
    })

    print(json.dumps(payload, indent=1, default=str))


if __name__ == "__main__":
    main()
