# ReMind — weekly Instagram brief

Every Monday morning, Claude pulls ReMind's Instagram numbers and writes a short
brief. It runs on Anthropic's servers, so nobody's laptop needs to be on.

## What's in here

| File | What it does |
|---|---|
| `pull.py` | Fetches the account, the week's posts and their metrics. Prints JSON. |
| `BRIEF.md` | How to turn that JSON into the brief — what matters for a therapy practice, and what must never be suggested. |

## How a run works

1. The routine wakes up on Monday morning and clones this repo.
2. It runs `python3 pull.py`.
3. It reads `BRIEF.md` and writes the brief from the JSON.
4. The brief appears in the session at [claude.ai/code](https://claude.ai/code).

## There is no access token in this repository

The Instagram token is stored in the Claude cloud environment as an **API
credential**. Anthropic's proxy attaches it to requests to `graph.facebook.com` after
they leave the session, so `pull.py` sends no token, Claude never sees one, and
nothing sensitive is ever committed here.

**Never paste a token into this repo.** If you do, it is in git history permanently
and must be regenerated.

## Comments are deliberately not collected

`pull.py` reads the *number* of comments on each post, never the text. People
sometimes disclose personal things in comments on a mental-health account, and that
should not pass through an analytics tool.

To change that later, add a `{media-id}/comments` call in `pull_posts()` — but discuss
it first; it is a decision about clients' privacy, not a feature.

## Every 60 days: refresh the token

Instagram tokens expire after about 60 days. When they do, the Monday brief fails with
a message saying the token has expired. To fix it:

1. Go to [developers.facebook.com/tools/explorer](https://developers.facebook.com/tools/explorer),
   select the ReMind app, and generate a new user token with the same permissions:
   `instagram_basic`, `instagram_manage_insights`, `pages_show_list`,
   `pages_read_engagement`. **On the screen asking which Pages and Instagram accounts
   to allow, choose all of them.**
2. Exchange it for a long-lived token:
   ```
   https://graph.facebook.com/v21.0/oauth/access_token
     ?grant_type=fb_exchange_token
     &client_id=<APP ID>
     &client_secret=<APP SECRET>
     &fb_exchange_token=<the token from step 1>
   ```
3. At [claude.ai/code](https://claude.ai/code), open the environment, delete the old
   `graph.facebook.com` credential and add the new one. Credentials can't be edited,
   only replaced.

Put a recurring calendar reminder at 55 days so this happens before it breaks.

*To stop this chore entirely:* a **system user** token from Meta Business Suite can be
issued without an expiry. It's more setup once, and then nothing to renew. Worth doing
if the brief proves useful.

## Testing a change

Open a cloud session in the same environment and run `python3 pull.py` to see the raw
JSON, then ask Claude to write the brief from it. That exercises exactly what the
Monday run does, without waiting for Monday.

To change what the brief says, edit `BRIEF.md` and commit. The next run picks it up.
