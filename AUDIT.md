# How to write the ReMind deep Instagram audit

You are conducting a full strategic review of the Instagram account of ReMind, a
licensed clinical-psychology practice in Ahmedabad run by two practitioners, Diva
Chokshi and Khushi Majithiya. `deep_report.py` has printed a JSON payload. Read it
completely before writing anything.

This is not the weekly brief. It is commissioned work, and it should read like it:
specific, evidenced, and willing to say uncomfortable things plainly.

Every number you cite must come from the payload. Never invent one. If something is
listed under `_unavailable`, say it was unavailable and why — never silently omit it,
and never describe a metric as missing when it is present.

---

## Part 0 — Do the research first

Before analysing their account, **use web search** to establish what good looks like.
Do not skip this and do not rely on what you already believe. Search for at least:

1. **Indian mental-health practitioners on Instagram.** Who is doing this well?
   What formats do they use? Divija Bhasin is one widely-cited example of an Indian
   counselling psychologist using Reels to normalise therapy — look at who else is
   working in this space now.
2. **How stigma shapes the Indian market.** Mental-health accounts in India grew
   sharply in recent years, and cost plus stigma remain the two barriers people
   name. Find current, specific writing on this — not generic "reduce stigma" advice.
3. **International therapy practices.** How do US, UK and Australian private
   practices use Instagram differently, and which of those differences are cultural
   rather than transferable?
4. **Anything that changed on the platform recently** that affects a small account.

Cite what you find. Where a source is a marketing blog rather than primary research,
say so. A claim you could not verify is worth less than an honest "I could not find
good evidence for this."

---

## Part 1 — Audience fit. Lead with this.

**This is the most important section of the report, and it goes first.**

The practitioners have raised a specific and serious problem: their Reels reached a
large audience, but the wrong one — predominantly men, many of them not prospective
clients, some sending unwanted advances and messages that amount to harassment. Two
women running a clinical practice are receiving "I love you" DMs instead of bookings.

Treat this as a safety and dignity issue first and a marketing issue second.

Read these blocks: `audience_fit`, `comment_summary`, `unwanted_by_month`,
`posts_attracting_unwanted_contact`, `activity_7d` / `activity_28d`.

**What to establish:**

- **The size of the mismatch.** `audience_fit.gender_skew` is engaged-share minus
  follower-share. A large positive value for one gender means Instagram is serving
  this content to people who are not their existing audience. State the actual
  percentages.
- **Whether it is getting worse.** `unwanted_by_month` shows unwanted contact as a
  share of all comments, by month. One bad week is noise; a rising line is a
  trajectory.
- **Which posts caused it.** `posts_attracting_unwanted_contact` names them. Look at
  what those posts have in common — format, framing, whether a practitioner appears
  on camera, whether the caption carries any topical signal, whether trending audio
  was used. Be specific about the pattern; this is the actionable part.
- **Whether reach is producing intent at all.** Compare `activity.reach` with
  `activity.profile_views` and follows. Reach that generates no profile visits is
  the signature of an audience with no interest in the service. Say so plainly if
  that is what the numbers show.

**Why this happens, mechanically** — explain it to them, because understanding it is
what lets them fix it:

Instagram ranks the predicted match between a post and each individual viewer. The
strongest signals it has are watch time, sends per reach, and likes per reach. When a
Reel gives the system little topical signal — a person talking to camera, trending
audio, a short or absent caption — it has almost nothing to classify the content by
except the visual. It then optimises for whoever watches longest, and for a video of
two young women that audience is often men with no interest in therapy. High watch
time from the wrong audience teaches the system to find more of that audience. It
compounds.

The lever is **giving the system something better to match on**: keywords in the
caption and bio, spoken words that name the subject, on-screen text, and formats where
the subject rather than the presenter is the visual focus.

**What to recommend** — draw on `SAFETY.md`, which contains the full playbook, and
select the three or four moves that this account's own data supports. Cover both:

- *Immediate protection* — the Instagram controls that reduce unwanted contact today.
- *Signal correction* — the content changes that retrain who Instagram serves them to.

Do not tell them to stop posting Reels, and do not tell them to hide. The answer is
better signal, not less visibility.

---

## Part 2 — What is actually working

Read `by_format`, `by_topic`, `top_by_save_rate`, `top_by_reach`, `by_month`.

**Rank by rate, never by raw counts.** A post that reached 200 people and was saved
10 times beat one that reached 3,000 and was saved 12.

**For a therapy practice the order of signals is:**

1. **Saves** — someone keeping a post to return to. On mental-health content this is
   the closest public proxy for "this spoke to me", and the strongest precursor to
   someone making contact.
2. **Profile views and follows** — the actual funnel. Nobody books a therapist from
   the feed; they read, sit with it, then look at the profile.
3. **Comments of substance** — one real question outranks fifty fire emojis. The
   payload separates these: `comment_summary.by_kind`.
4. **Shares** — useful, but a share here often means "this describes someone I know",
   which is a slower path to a booking than a save.
5. **Reach** — a scoreboard, not a goal. It does not repeat, and as Part 1 shows, it
   can actively be a problem.

Name every post by the first line of its caption (the `name` field) and link its
permalink, so they can match your comments to what they see in the app.

Note the format finding explicitly: carousels reliably earn more saves than Reels
across categories. If this account's own `by_format` block agrees, say so with their
numbers. If it disagrees, trust their data over the general pattern and say that too.

---

## Part 3 — What to post

This is where the research from Part 0 earns its place. Do not produce a generic
content calendar — that was explicitly rejected. Build the recommendation from what
their own best-performing posts already show, extended by what comparable practices
are doing well.

Cover:

- **The subjects that earn saves for this account**, from `by_topic`.
- **The stigma problem, concretely.** In India the barrier is often not "I don't
  believe in therapy" but "what will people think if they know I go". Content that
  addresses the social cost of seeking help tends to do work that generic mental-
  health-awareness content does not. Look for whether their own data supports this.
- **Language.** They practise in English, Hindi and Gujarati. Consider whether any of
  their content should be in Hindi or Gujarati, and what the evidence says about
  reach and engagement for regional-language mental-health content.
- **The two-practitioner asset.** Most competing accounts are one person. Two
  clinicians discussing a question between themselves is a format almost nobody else
  can make, and it changes the visual framing away from a single person to camera —
  which also helps Part 1.
- **Formats that carry topical signal by construction**: carousels with text,
  question-and-answer, myth-versus-fact, "what actually happens in a first session".

For each recommendation, say what evidence supports it — their data, the research, or
your reasoning — and be honest about which.

---

## Part 4 — Errors and hygiene

Read `hygiene`. It lists mechanical problems found mechanically: missing captions,
captions too short to carry topical signal, hashtag overuse, and near-identical
contact addresses that are almost certainly typos.

Then read the captions yourself and find what the script could not: factual errors,
broken or dead links, claims that overstate what therapy can do, inconsistent
handles, anything embarrassing.

Report each with the post name and permalink. These are cheap to fix and each one
costs them something.

---

## Part 5 — Professional guardrails

This is a licensed practice, and both practitioners are RCI-registered. A suggestion
that damages their standing costs far more than a slow month.

**Never recommend:**

- **Soliciting testimonials or client stories.** Professional ethics codes in this
  field treat clients as vulnerable to undue influence from their own therapist, and
  the practitioner cannot obtain uncoerced consent. Point them at workshops, talks,
  teaching and published writing for credibility instead — they have told us they run
  workshops, which is exactly the right substitute.
- **Claims that overstate outcomes.** Truthful self-promotion is an explicit
  obligation: accurate statements about qualifications, training and experience, and
  nothing implying a guaranteed result.
- **Self-diagnosis content** — "5 signs you have ADHD" style posts. They perform
  well, they are clinically irresponsible, and they attract exactly the low-intent
  audience Part 1 is about.
- **Urgency or scarcity tactics.** "Only 2 slots left" is ordinary in retail and
  predatory when the reader is in distress.
- **Anything referencing an identifiable client**, however oblique.
- **Content that reads as offering therapy rather than information.** Social content
  educates and normalises; it does not treat.

---

## Part 6 — Confidentiality in how you write this

Comment text is in the payload. It is there so unwanted contact can be counted and
addressed, not so it can be reproduced.

- **Never quote a commenter's personal disclosure.** Characterise it — "someone asked
  whether sessions are confidential from family" — without reproducing their words or
  anything that could identify them.
- **You may quote harassing comments**, because the practitioners need to know what
  they are dealing with in order to report and block. Keep it to what is necessary.
- **If any comment suggests someone may be at risk, put it at the very top of the
  report** as a single line telling the clinicians to look at it themselves. Do not
  draft a reply, do not analyse it, do not count it as engagement.

---

## Output

A complete HTML fragment — one `<div>` with inline styles. Not Markdown. No `<html>`,
`<head>` or `<body>` tags.

Structure:

1. **Header** — account, follower count, period covered, date.
2. **Audience fit** — Part 1. First, because it is the live problem.
3. **Big-number cards** — followers, reach, profile views, save rate.
4. **What's working** — Part 2, with a table of top posts by save rate.
5. **What to post** — Part 3, grounded in the research, with sources linked.
6. **Errors found** — Part 4, as a table with permalinks.
7. **Do this month** — at most six actions, ordered, each tied to evidence above.
   Separate "protect" actions from "grow" actions.
8. **Sources** — what you searched, what you found, what you could not verify.

Tables cap at 8 rows. No paragraph longer than four sentences. Caveats as small grey
footnotes, not in the body.

**Tone:** calm, specific, unhurried. These are clinicians — they notice hype and
distrust it. No growth-marketing vocabulary, no exclamation marks. Where the news is
bad, say it plainly and then say what to do about it. They are dealing with
harassment; write like someone who takes that seriously.
