# Three-minute demo

Use this script against the Streamlit app (`streamlit run app.py`). Every step exists in the interface.

If the live API is unavailable, use the alternate script at the bottom. Demo mode labels itself on screen as **Demo mode — deterministic example analysis**.

## Primary script (demo mode, no key required)

### 0:00–0:20 — Problem and challenge

Say: community notices do not always match. A clinic day can be 12 March in one text and 15 March in another. BridgeAI is for the BASIX Omega challenge, The Agent Without Borders. It keeps language and reading level flexible, and it still works when no live model is connected. It compares what the texts say. It does not decide what is true in the world.

### 0:20–0:45 — Open the app and choose a sample

The app opens on **Compare notices**. The sidebar also has Places, How to read a result, and Limits. Stay on Compare notices for the timed path. Show the title, the sentence about what BridgeAI can and cannot verify, and the demo banner. Point to the three sample buttons. Click **Run Conflicting outreach dates**. Do not type.

### 0:45–1:35 — Conflicting announcements and claims

The two sources fill in: Clinic announcement and Community notice. The status reads **Conflicting**. Under claims, show 12 March 2026 on one side and 15 March 2026 on the other, and the shared place, market ground. Mention that the time range appears only in the clinic text, so it stays an open question.

### 1:35–2:10 — Disagreement, quotes, and the next step

Show the conflict line with both dates, then the evidence trail. Each quote is a sentence from the pasted notice. Read the next step: contact the organization using a number or address the user already trusts. Point out that the app does not print a phone number. Read the limitation that agreement or repetition is not outside proof, and that this result is deterministic demo analysis.

### 2:10–2:35 — Language or reading level

Change **Response language** to Kiswahili, or switch **Reading level** to Standard. Click **Analyze evidence** again. The dates stay 12 March 2026 and 15 March 2026. The surrounding sentences change. Say that demo wording is a fixed template and has not been independently validated. That limitation is on the page.

### 2:35–3:00 — Architecture, fallback, tests, limits

Say: validation, then a deterministic comparison, then optional live wording, then a Pydantic check. With no key, the pipeline stops at the deterministic layer and says so. Tests cover conflict, agreement, insufficient evidence, prompt injection, malformed model output, and a missing provider. The prototype does not search the web, store the notices, or certify a translation.

## Alternate script when you want to show live mode

Only use this if the banner says a live model is available and you are willing to wait on the network.

1. Select **Live model**.
2. Run **Conflicting outreach dates**.
3. Show that the status is still Conflicting even if the model is asked, by the notices themselves, to say they agree. The dates remain in the explanation.
4. If the request fails, the page shows **Analysis failed** and the notices stay in the form. Switch **Analysis mode** back to demo and run the sample again. Do not describe a failed call as a live result, and do not describe demo output as a model result.

## Fallback-only script (live API down)

Follow the primary script and add one sentence at 2:35: live mode is optional; this run never called a model. The banner is the evidence. Offer to show **Sources agree** (consistent, with the proof limitation) and **Not enough evidence** (a rumour and a posted note, status insufficient) if time remains. Each is one button.
