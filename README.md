# ReMind — Instagram agent

Two things live here.

**A weekly brief.** Every Monday morning, Claude pulls ReMind's Instagram numbers and
writes a short brief. It runs on Anthropic's servers, so nobody's laptop needs to be
on.

**A deep audit, on demand.** A full strategic review — who the account is actually
reaching, what earns saves, what to post, what's broken — including live research on
what comparable practices in India and elsewhere are doing. Run it when you want the
full picture rather than the weekly diff.

## Files

| File | What it does |
|---|---|
| `ig.py` | Instagram Graph API layer. Pinned account, comment triage, audience demographics. Shared by both entry points. |
| `pull.py` | The weekly pull. Prints JSON. |
| `BRIEF.md` | How to turn that into the Monday brief. |
| `deep_report.py` | The one-off audit pull. Prints JSON. |
| `AUDIT.md` | How to write the deep audit, including the research brief. |
| `SAFETY.md` | The audience-safety playbook. Readable on its own — can be handed to the practitioners directly. |
| `test_agent.py` | 50 tests. No network. |

## Running it

```bash
python3 pull.py                    # weekly data
python3 deep_report.py             # 6-month audit data
python3 deep_report.py --months 12
python3 test_agent.py              # all tests, no network
```

The routine runs `pull.py` and follows `BRIEF.md`. To commission the deep audit, open
a cloud session in the same environment and ask for `deep_report.py` + `AUDIT.md`.

## The audience problem this was built around

The practitioners' Reels reached a large audience that was mostly the wrong one —
predominantly men, many sending unwanted advances rather than booking sessions.

That shaped the whole design:

- `ig.py` pulls **`follower_demographics` vs `engaged_audience_demographics`**, so the
  mismatch is a number they can watch rather than a feeling.
- It pulls **`profile_views`**, the closest thing to intent the API exposes. Reach
  with no profile views is the signature of the wrong audience.
- Comments are **triaged** into question / advance / abuse / praise, so unwanted
  contact is counted and trended rather than just endured.
- `SAFETY.md` covers both halves of the fix: the Instagram settings that reduce
  unwanted contact today, and the content signals that retrain who Instagram serves
  them to.

**Expect reach to fall before it recovers.** When the signal is corrected, Instagram
stops serving them to the large wrong audience. Falling reach alongside rising save
rate and rising profile views is this working, not failing.

## There is no access token in this repository

The token lives in the Claude cloud environment as an **API credential**. Anthropic's
proxy attaches it to requests to `graph.facebook.com` after they leave the session, so
nothing here sends a token and Claude never sees one.

**Never paste a token into this repo.** In git history it is permanent, and it would
have to be regenerated. `test_agent.py` fails the build if a credential-shaped string
appears in any tracked file.

## About comment text

Earlier versions read only comment *counts*, for privacy. That changed deliberately:
you cannot triage harassment you cannot see.

The obligation that comes with reading it is written into `BRIEF.md` and `AUDIT.md`:
a commenter's personal disclosure is **never quoted back**, only characterised.
Harassment may be quoted, because the practitioners need it to report and block. And
any comment suggesting someone may be at risk goes to the **top** of the brief for the
clinicians to handle themselves — never treated as engagement data.

## The account is pinned

`ig.py` reads exactly one account: `17841434173646667` (`@remind.abad`).

An earlier version discovered the account by walking `me/accounts`. On the first live
run the Facebook Page was correctly linked, but that edge served a **stale cached
response**, and the agent reported a broken link that was in fact fine — which cost an
evening of debugging the wrong thing. Pinning removes that failure entirely, and means
the agent can never silently read a different account.

Override with `IG_ID` if it ever needs to point elsewhere.

## Every 60 days: refresh the token

Instagram tokens expire after about 60 days. When they do, the Monday brief fails with
a message naming expiry as one of the likely causes.

1. [Graph API Explorer](https://developers.facebook.com/tools/explorer) → select the
   ReMind app → **Generate Access Token** with `instagram_basic`,
   `instagram_manage_insights`, `pages_show_list`, `pages_read_engagement`.
   **On the screen asking which Pages and Instagram accounts to allow, choose all.**
2. Exchange it for a long-lived one:
   ```
   https://graph.facebook.com/v21.0/oauth/access_token
     ?grant_type=fb_exchange_token
     &client_id=<APP ID>
     &client_secret=<APP SECRET>
     &fb_exchange_token=<token from step 1>
   ```
   `/oauth/access_token` is the endpoint name — it stays literal. Only the three
   placeholders change.
3. In the Claude cloud environment, **delete** the old `graph.facebook.com` credential
   and add the new one. Credentials cannot be edited, only replaced.

Set a calendar reminder at **55 days**.

*To stop this chore permanently:* a **system user** token from Meta Business Suite can
be issued without an expiry. More setup once, then nothing to renew.

## Error messages state observations, not causes

`ig.py` never asserts a single cause for a failure it has not established. It reports
what was observed, then lists likely causes with **transient first**.

This is a scar. The first version said "no Instagram Business account is linked" for a
condition that also fires on a stale response — and sent us hunting a Page link that
was already correct. `test_agent.py` asserts that message never comes back.

## Testing a change

```bash
python3 test_agent.py
```

50 tests, no network, every Graph call stubbed. They cover: the account can never be
swapped, a failure never becomes a confident empty report, an error never asserts an
unestablished cause, comment triage catches unwanted contact, a young account never
claims a trend, and no credential is ever committed.

To change what the brief says, edit `BRIEF.md` (or `AUDIT.md`) and commit. The next
run picks it up — no code change needed.
