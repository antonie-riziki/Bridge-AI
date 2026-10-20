# Architecture

BridgeAI is one pipeline, not a multi-agent framework. Each stage has a narrow job. Later stages may not invent facts that earlier stages did not find in the pasted text.

## Flow

```text
Streamlit form
    │
    ▼
Input validation          empty text, length, at least two sources
    │
    ▼
Deterministic comparison  dates, times, places, amounts
    │
    ├─ demo mode ─────────► fixed language templates ─► Pydantic AnalysisResult
    │
    └─ live mode ─────────► model wording + optional quoted conflict
                                │
                                ▼
                         grounding and contact checks
                                │
                                ▼
                         Pydantic AnalysisResult
```

If the live call fails, the pipeline returns `ANALYSIS_FAILED`. It does not substitute a demo result under a live label.

## Modules

### `app.py` and `bridgeai/compare.py`

`app.py` sets the page config once and registers four sidebar pages. **Compare notices** is the default. It renders the form, sample-scenario buttons, status, claims, conflicts, explanation, next step, and limitations. Session state keeps the text when a run fails. A previous result is hidden once the form changes, so an old check is not read as a result for new text.

The page does not put source text into HTML. Status colour is paired with a written label.

### `bridgeai/ui/` and `bridgeai/services/places.py`

**Places** lists location phrases from the same extractor used by the comparison. It does not send that text to a geocoder. A map pin exists only when the person enters both a latitude and a longitude, and those numbers are in range. **How to read a result** and **Limits** are static explanations. They do not run an analysis.

### `bridgeai/config.py`

Reads `ASI_API_KEY`, `OMEGA_LLM_BASE_URL`, `OMEGA_LLM_MODEL`, and `OMEGA_LLM_ENABLED`. `public_provider_status()` returns only whether a live model is configured and which model name would be used. It never returns the key.

### `bridgeai/schemas.py`

`SourceDocument`, `ExtractedClaim`, `EvidenceComparison`, and `AnalysisResult` are Pydantic models. Conflicts must contain two different values. A consistent result must contain an agreement. A failed result cannot contain findings. Those rules keep a schema-valid object from quietly claiming success.

### `bridgeai/services/evidence.py`

This module does not call a model. It finds:

- dates in English and Kiswahili month names, ISO dates, and numeric dates
- times with a colon or an am/pm marker
- places introduced by "at", "in", "katika", or "kwenye"
- amounts in KES, KSh, or USD

The same normalized value in two sources is an agreement. Different values are a conflict. A value that appears in only one source stays unresolved. No structured overlap becomes `INSUFFICIENT_EVIDENCE`, including when the two texts are identical but contain no comparable fact. Missing information is never labelled consistent.

Every claim excerpt is the sentence copied from that source.

### `bridgeai/services/language.py`

Demo explanations are templates. The selected language and reading level change sentence length and wording. Dates, times, and amounts are inserted unchanged. The file also builds the instruction string sent to a live model. Template wording is not described as a validated translation.

### `bridgeai/services/providers.py`

`OmegaProvider` posts to `{OMEGA_LLM_BASE_URL}/chat/completions` with bearer authentication. Timeouts, auth failures, rate limits, and unreadable bodies become a short `ProviderError`. The user-facing message does not include the response body or the key.

### `bridgeai/services/agent.py`

`analyze` and `analyze_pairs` own the pipeline.

- `demo` always uses the deterministic result and templates.
- `auto` uses live mode only when a provider object was passed or a key is configured. Otherwise it uses demo mode.
- `live` returns `ANALYSIS_FAILED` when no provider is available or the model output cannot be validated.

On a successful live call:

1. Structured conflicts from the deterministic pass remain conflicts. The model cannot downgrade them.
2. A model conflict is kept only when each excerpt is contained in the cited source and the excerpts come from at least two sources.
3. The model summary is kept only when it still contains the compared values and does not add a phone number or URL that was not in the sources.
4. Otherwise the fixed explanation is shown, and the limitations say why.

### `bridgeai/services/scenarios.py`

Three fixed scenarios used by the interface and the tests: conflicting outreach dates, agreement on a vaccination day, and notes that do not establish a fact.

## Status meanings

| Status | Meaning |
| --- | --- |
| `CONSISTENT` | No material contradiction in the comparable points, and at least one shared point. Not external proof. |
| `CONFLICTING` | The supplied texts disagree on a compared point, or a quoted semantic disagreement passed the grounding check. |
| `INSUFFICIENT_EVIDENCE` | The texts do not establish the answer. Silence is not agreement. |
| `ANALYSIS_FAILED` | The live operation failed or returned nothing usable. No findings are attached. |

## Trust boundaries

- **Source text** is data. The system prompt tells the model that instructions inside a source are not commands. The deterministic status does not read those instructions.
- **Model output** is untrusted until it validates against `ModelNarrative` and passes excerpt, value, and contact checks.
- **Environment** is the only place for the API key. Logs in this prototype do not record source text or secrets.
- **Browser session** holds the current form and the last matching result. Nothing is written to a database.

## Errors

| Situation | What the person sees |
| --- | --- |
| Empty source, missing label, or text over 8000 characters | A direct `InputError`. The form is unchanged. |
| No API key while live mode was requested | `ANALYSIS_FAILED` explaining that live analysis is not configured. |
| Timeout, HTTP error, or malformed JSON | `ANALYSIS_FAILED` with a short message and no stack trace. |
| Model cites text that is not in a source | That citation is dropped. If the whole result cannot be grounded, the attempt fails. |

Demo mode does not depend on the network.
