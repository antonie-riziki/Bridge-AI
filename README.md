# BridgeAI

BridgeAI is an accessible evidence-reconciliation assistant for community notices. A person can paste two short texts — in English, Kiswahili, or Sheng — and see what those texts agree on, where they contradict, and what they do not establish.

This is a prototype for the **BASIX State of the Art Hackathon**, **Omega AI Agents** track, challenge **The Agent Without Borders**: reasoning that holds across languages, literacy levels, and connectivity constraints.

BridgeAI is an evidence assistant. It is not a news verifier, a medical service, or an emergency line.

## Problem

Clinic days, water notices, and school announcements often circulate as more than one text. The dates or details do not always match, and the reader may want a short explanation in another language or in simpler sentences. Repeating a claim does not make it true, and a missing detail is not the same as a confirmed one.

## Who it is for

Community members, clinic volunteers, and local organizers who need to compare notices before they act. A judge can also run the three built-in scenarios without typing.

## What it does

1. Accepts two labelled sources and rejects empty or oversized text.
2. Extracts comparable dates, times, places, and amounts with deterministic rules.
3. Marks the result as consistent, conflicting, or insufficient. It does not treat silence as agreement.
4. Quotes the supplied text in an evidence trail.
5. Writes the explanation in English, Kiswahili, or best-effort Sheng, at a simple or standard reading level.
6. Recommends a verification step without inventing phone numbers or links.
7. Runs a clearly labelled demo mode when no live model is configured.
8. Keeps the text in the form when a check fails.

A consistent result means the supplied texts do not contradict each other on the points this check can compare. It does not mean those points are true in the world.

## Architecture

```text
sources → validation → deterministic comparison → optional live wording → schema check → Streamlit
```

| Module | Responsibility |
| --- | --- |
| `app.py` | Streamlit entry point (`streamlit run app.py`) |
| `bridgeai/app.py` | Form, sample scenarios, result layout |
| `bridgeai/config.py` | Environment settings. The API key is never displayed |
| `bridgeai/schemas.py` | Pydantic models |
| `bridgeai/services/evidence.py` | Date, time, place, and amount comparison |
| `bridgeai/services/language.py` | Fixed wording for language and reading level |
| `bridgeai/services/providers.py` | Omega / ASI Alliance client (OpenAI-compatible) |
| `bridgeai/services/agent.py` | Pipeline, grounding checks, failure results |
| `bridgeai/services/scenarios.py` | Three documented demo scenarios |

Details and trust boundaries are in [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md). Model use is disclosed in [docs/AI_DISCLOSURE.md](docs/AI_DISCLOSURE.md). The judge walkthrough is in [docs/DEMO_SCRIPT.md](docs/DEMO_SCRIPT.md).

## Setup

Python 3.11 or newer is required. This repository was exercised with Python 3.14.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Leave `ASI_API_KEY` empty to stay in demo mode. Never commit `.env`.

## Run the application

```bash
streamlit run app.py
```

The app binds to `0.0.0.0` so a hosted container can receive traffic. Locally, open the URL Streamlit prints (usually `http://localhost:8501`).

On a host that sets `PORT`:

```bash
streamlit run app.py --server.port "$PORT" --server.address 0.0.0.0
```

## Demo mode

Demo mode is the default when no API key is configured. The screen shows:

**Demo mode — deterministic example analysis**

Choose one of the sample buttons. Each button loads the texts and runs the check:

| Sample | What you should see |
| --- | --- |
| Conflicting outreach dates | Status **Conflicting**. 12 March 2026 versus 15 March 2026. The place matches. |
| Sources agree | Status **Consistent**. Shared date, place, and time. The screen says agreement is not outside proof. |
| Not enough evidence | Status **Insufficient evidence**. No shared checkable fact. |

Demo mode does not understand general meaning and does not call a translation model. Kiswahili and Sheng wording comes from fixed templates. Dates stay in the form extracted from the source so they are not silently rewritten.

You can also paste your own notices. The same rules apply: dates, times, places, and amounts. Other disagreements need the live model, and only when it can quote both sources.

## Live model

BridgeAI can call an OpenAI-compatible chat endpoint. The intended provider is the Omega / ASI Alliance route:

```text
OMEGA_LLM_BASE_URL=https://llm.c.singularitynet.io/v1
OMEGA_LLM_MODEL=asi1-mini
OMEGA_LLM_ENABLED=true
ASI_API_KEY=...
```

Put the key only in `.env` or the host's secret store. The app reads `ASI_API_KEY` from the environment. It does not print the key, and the key is not part of the result.

When live mode is on:

- Deterministic rules still decide structured conflicts. The model cannot hide a date conflict.
- The model may write the explanation in the selected language.
- The model may add a conflict only when both excerpts appear in the pasted sources.
- A phone number or link that was not in the sources is removed.
- If the call fails or the JSON is unusable, the status is **Analysis failed**. The form text stays. The app does not silently switch to demo mode.

## Tests

```bash
pytest
```

The tests do not call the live API. Provider calls are stubbed. A syntax check:

```bash
python -m compileall -q app.py bridgeai tests
```

## Sample behaviour

**Conflict**

- Clinic announcement: outreach on 12 March 2026 at the market ground, 9:00 to 13:00.
- Community notice: outreach on 15 March 2026 at the market ground.

Expected: conflicting dates, shared place, an open question about the time, and a next step that says to use a contact you already trust.

**Agreement**

- Both texts: vaccination day on 4 April 2026 at the school hall, doors at 8:00.

Expected: consistent on those points, with a limitation that agreement is not external proof.

**Insufficient evidence**

- "Some people say the water is unsafe."
- "A notice was posted near the tap."

Expected: insufficient evidence. The gap is not filled in.

## Limitations

- Demo mode only compares dates, times, places, and amounts. It will miss many real disagreements.
- Numeric dates are read as day/month/year unless one number can only be a month.
- Kiswahili and Sheng templates were written for this prototype. They have not been independently validated.
- Live model wording can be wrong. A valid JSON result is not a measure of accuracy.
- The prototype does not search the web, store sources, or identify which notice is newer.
- No phone number, URL, or official contact is invented.

## Privacy and security

- Source text is untrusted data. Instructions inside a notice cannot change the status rules or call tools.
- Sources are kept in the browser session for the current visit. They are not written to a database.
- There is no analytics call and no account system.
- Do not log source text in production. This prototype does not.
- `.env` is gitignored. `.env.example` contains empty placeholders.

## AI tools and APIs

See [docs/AI_DISCLOSURE.md](docs/AI_DISCLOSURE.md).

- In the product, live mode calls the configured Omega-compatible model when `ASI_API_KEY` is set. Demo mode does not.
- The implementation in this repository was written with Cursor Agent.

## GitHub and demo

- GitHub repository: https://github.com/antonie-riziki/Bridge-AI
- Hosted demo URL: not deployed yet. Local command: `streamlit run app.py`.

## License

MIT. See [LICENSE](LICENSE).
