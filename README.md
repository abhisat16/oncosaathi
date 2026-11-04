# OncoSaathi

A Hindi-first voice companion that guides cancer patients and their families through a hospital, one step at a time.
Built for KOITA Health-a-thon 2026 by Team Oslava.

**Try it:** https://oncosaathi.onrender.com
Open it in Chrome, sign in with a mobile number, and press the call button (allow the microphone).
The first visit after a quiet spell can take about a minute while the free server wakes up.

> The hospital map comes from the **Tata Memorial Hospital patient booklet** (5 buildings, 59 departments; see `build_hospital_tmh.py`). OncoSaathi gives
> directions and logistics only. It never gives medical advice: emergencies go to the nearest nurse or help desk,
> and distress to Tele-MANAS 14416.

## What it does
- Voice call in Hindi, English and 9 more Indian languages, with interruption
- Step-by-step directions to 59 real TMH departments across 5 buildings (MB, GJB, AB, HBB, SB)
- Reads a photo of the doctor's referral slip and names the right department
- Real places to stay near the hospital (phone numbers only, never books), and travel from other states
- Remembers the patient with consent; the data can be deleted at any time

## How it works
Speech (Sarvam Saaras v4) → safety rules first → Sarvam-105b picks a label only → answer filled from the hospital
data files (`hospital.json`, `journey.json`, `stay.json`, `travel.json`) → speech (Sarvam Bulbul v3).
The language model never writes room numbers itself, so it cannot invent them.

## Run it yourself
```bash
python -m venv .venv && .venv/bin/pip install -r requirements.txt
cp .env.example .env    # then add your own keys
CALL_ENGINE=local .venv/bin/python server.py
```
Open http://127.0.0.1:7860.

## Tests
`journey_test.py` (journey, memory, consent, deletion), `eval_brain.py` (questions → right place),
`call_test.py` (spoken end-to-end call), `simulate_patients.py` (20 simulated patients).

## Deployment
`render.yaml` deploys this repository on Render. Keys go in a Render Secret File named `.env`. Every push to `main` updates the live link automatically.
Keys are set in Render's dashboard and are never stored in this repository.
