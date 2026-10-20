# AI disclosure

BridgeAI is a hackathon prototype. This note separates the model that can run inside the product from the tools used to build it.

## A. AI used inside the product

### Provider and model

Live mode calls an OpenAI-compatible chat completions endpoint.

- Provider route: Omega / ASI Alliance
- Base URL: `https://llm.c.singularitynet.io/v1`
- Model name configured in this project: `asi1-mini`
- Credential: `ASI_API_KEY`, read from the environment only

The key is not stored in source code, the interface, the tests, or this document. A local `.env` file is gitignored.

On 20 October 2026 a live call with that configuration succeeded. A conflicting-date scenario returned status `CONFLICTING` and kept both dates, 12 March 2026 and 15 March 2026. That single call is not an accuracy benchmark.

If `ASI_API_KEY` is missing or `OMEGA_LLM_ENABLED` is false, the product does not call the model.

No Anthropic model is wired into this repository. No other provider is called.

### Tasks performed by the model

When live mode is selected, the model is asked to:

- write `concise_summary` and `recommended_next_step` in the selected language and reading level
- optionally add a semantic conflict, but only with verbatim excerpts from the supplied sources
- note translation uncertainty in `extra_limitations`

The model is not given tools. It cannot browse, and it is instructed that text inside a source is data, not a command.

### Deterministic processing outside the model

These steps do not use a model:

- input validation
- extraction of dates, times, places, and amounts
- agreement and conflict classification for those values
- evidence quotes copied from the source sentences
- demo-mode explanations in English, Kiswahili, and Sheng
- rejection of phone numbers and links that were not in the sources
- Pydantic validation of the result

Structured conflicts from this layer are kept even if the model describes the notices as consistent.

### External services and dependencies

- Live mode: HTTPS request to the configured Omega-compatible endpoint
- Python packages: Streamlit, Pydantic, python-dotenv, httpx, pytest
- No database, analytics, vector store, or web search

Streamlit usage statistics are turned off in `.streamlit/config.toml`.

### Limitations and fallback

- A schema-valid model response can still be wrong.
- Demo mode does not understand general meaning and does not translate. Kiswahili and Sheng strings are fixed templates and have not been independently validated.
- The prototype does not establish facts outside the pasted text.
- If the live call times out, is rejected, or returns unusable JSON, the status is `ANALYSIS_FAILED`. Demo wording is not substituted under a live label.
- The screen shows **Demo mode — deterministic example analysis** whenever that mode is used.

## B. AI used to build the product

### Coding assistant

Cursor Agent, in the Cursor IDE, wrote and revised this repository from the hackathon brief. The agent model for this session was Grok 4.7.

### Models and tools used during implementation

- Grok 4.7 through Cursor Agent for implementation, tests, and documentation
- Local Python 3.14.2
- pytest  (the suite that shipped with this workspace's system interpreter)
- A live `asi1-mini` request, used once to check the endpoint and once to check a conflicting-date analysis after a response-shape fix
- No separate dataset, benchmark suite, or human evaluation panel was used

### Human decisions and verification

The product shape, challenge, safety limits, and the instruction to commit and push came from the project brief. Engineering choices made while implementing included: one pipeline rather than a multi-agent framework, deterministic comparison as the authority for dates and amounts, demo mode as the default even when a key is present, and fixed templates instead of claiming validated translation.

### Tests actually executed

On 20 October 2026, from this repository:

```text
python3 -m compileall -q app.py bridgeai tests
python3 -m pytest
```

Result: **38 passed** in about 0.3 seconds. The suite does not use a network connection or an API key. Provider calls are stubbed.

A further manual live check, after the test suite, called `asi1-mini` for the conflicting outreach scenario. Status: `CONFLICTING`. Provider mode: `live`. Both source dates remained in the result. This was one check, not a scored evaluation.

Demo mode for all three sample scenarios is covered by `tests/test_fallback.py` and does not require credentials.

## What this disclosure does not claim

- It does not claim a measured accuracy, translation quality score, or user study.
- It does not claim that Sheng or Kiswahili output was reviewed by a language expert.
- It does not claim that the prototype verifies news, health, or emergency information.
