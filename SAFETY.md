# Audience safety — the playbook

Written for a specific situation: ReMind's Reels reached a large audience that was
mostly the wrong one, and the practitioners started receiving unwanted advances in
comments and DMs.

Two things are true at once. This is a **safety problem**, and it needs settings
changed today. It is also a **signal problem**, and it needs content changes that
retrain who Instagram serves them to. Do both; neither alone is enough.

Referenced by `AUDIT.md` and `BRIEF.md`. Also readable on its own — this section is
written so it can be handed to the practitioners directly.

---

## Part A — Protection. Do this today.

These are Instagram settings. They take about ten minutes and cost nothing.

### 1. Turn on Limits

**Settings and privacy → Restrictions / Limits → Limit unwanted comments and messages**

Limits automatically hides comments and DM requests from people who **don't follow
you, or who only recently followed you**. That is precisely the population arriving
from a Reel that reached beyond the intended audience. It is designed for exactly
this situation and it is reversible — turn it on for a few weeks, see what changes.

Their existing followers and clients are unaffected.

### 2. Turn on Hidden Words

**Settings and privacy → Hidden Words**

- Switch on **Hide comments** (Instagram's own offensive-terms filter)
- Switch on **Advanced comment filtering**
- Switch on **Hide message requests**
- Add a **custom word list** of the specific terms arriving in their DMs and
  comments. The words that show up in the account's own comment triage are the right
  starting list — everything classified as `advance` or `abuse` in the report.

Filtered comments go to a hidden folder rather than being deleted, so nothing is lost
if they want to review it.

### 3. Use Restrict rather than Block for the ambiguous ones

**On the profile → ⋯ → Restrict**

A restricted person's comments are visible only to them. They can't tell they have
been restricted, so it avoids the escalation that blocking sometimes provokes. Block
is still the right answer for anything threatening.

### 4. Know what Instagram already does

DM invitations from people who don't follow you are limited to **text only** — no
images, video or voice notes until the request is accepted. So an unaccepted request
cannot be used to send an unwanted picture. Worth knowing, because it removes one
specific fear.

### 5. Report, don't just delete

Reporting trains the platform. Deleting does not. For anything sustained or
threatening, report the account and then block.

---

## Part B — Signal. This is the actual fix.

Protection stops the damage arriving. It does not change who Instagram shows them to.
That requires changing what the ranking system has to work with.

### Why this happened

Instagram ranks the predicted match between a post and each individual viewer. The
three strongest signals are **watch time**, **sends per reach**, and **likes per
reach**. It is not primarily demographic targeting — it is behavioural.

When a Reel offers little topical signal — a person talking to camera, trending
audio, a short or absent caption — the system has almost nothing to classify it by
except the visual. It falls back on optimising for whoever watches longest. For a
video of two young women, that audience often includes a large number of men with no
interest in therapy. Their watch time then teaches the system to find more of them.

It compounds. Left alone, it gets worse, which is why `unwanted_by_month` in the
report is worth watching.

### What actually moves it

**Give the system words to work with.** Keywords in the caption and in the bio are
how Instagram determines what content is about and who should see it. A caption that
says *"why so many people in India put off therapy for years"* is classifiable. A
caption that says *"✨ new reel ✨"* is not.

**Say the subject out loud.** Instagram reads the audio. If the first five seconds
contain the words "anxiety", "therapy", "relationship", that is signal. Silent Reels
over trending audio give it nothing.

**Put text on screen.** It is read, and it also holds the right viewer longer while
losing the wrong one faster — which is the watch-time signal working in their favour.

**Change the visual subject.** Formats where the subject rather than the presenter is
the focus: carousels with text, hands writing, objects, illustration, b-roll with
voiceover. Carousels also reliably earn more saves than Reels, which for a practice
is the metric that matters most anyway. This is the single highest-leverage change.

**Use the two-practitioner format.** Two clinicians discussing a question between
themselves is something almost no competing account can make. It also shifts the
framing from a single person to camera towards a conversation — which is both better
content and better signal.

**Drop the hashtags.** They no longer help reach and may slightly hurt it. Keywords in
the caption do the work now.

**Stop optimising for reach.** A Reel with 15,000 reach, four saves and a stream of
unwanted DMs is a worse outcome than 800 reach with 40 saves. If reach is the number
being celebrated, the account will keep being pushed toward the audience that
produces reach and nothing else.

### What not to do

- **Don't stop posting Reels.** They are how a new account gets found. The problem is
  the signal, not the format.
- **Don't go private or hide.** That solves the symptom by ending the business case.
- **Don't buy followers or engagement.** It makes the audience-match problem worse by
  feeding the system more noise.
- **Don't run ads to fix this yet.** Ads let you target, but they will not correct the
  organic signal, and the organic audience is what the recommendation system has
  learned. Fix the signal first; ads are a separate decision afterwards.

---

## Part C — How to tell whether it is working

From the weekly pull, in order of usefulness:

| Watch | Where | What good looks like |
|---|---|---|
| Gender skew | `audience_fit.gender_skew` | Moving toward the follower base, not away |
| Profile views per 1,000 reach | `activity.profile_views` ÷ reach | Rising. This is intent. |
| Save rate | `this_week.save_rate` | Rising. The signal that matters for a practice. |
| Unwanted share of comments | `comment_summary.unwanted_share` | Falling |
| Reach | `activity.reach` | **May fall, and that can be fine** |

That last row matters. When the signal is corrected, reach often drops before it
recovers, because the system stops serving them to the large, wrong audience. Falling
reach alongside rising save rate and rising profile views is the shape of this
working. Expect it, so nobody panics and reverts.

Give it four weeks. The recommendation system needs repeated signal to relearn an
account, and a single well-tagged post will not undo months of the opposite.
