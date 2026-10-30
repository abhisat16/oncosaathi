# ==========================================================
#  OncoSaathi – Digital Kevat | WhatsApp-style voice prototype
#  Team Oslava | Health-a-thon 2026
#
#  CELL 1 (run once):
#     !pip install -q "gradio==6.30.0" requests
#
#  CELL 2: paste everything below, put your Sarvam key, press ▶
#  Then OPEN THE  https://xxxx.gradio.live  LINK IN A NEW TAB
#  (the microphone works best there, not inside the Colab preview).
# ==========================================================

import gradio as gr, requests, base64, tempfile, os, re, html, datetime, json, mimetypes
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))

SARVAM_KEY = os.environ.get("SARVAM_API_KEY", "")  # read from .env, never hardcoded
KEYTERMS = ["CBC", "OPD", "pathology", "biopsy", "chemo", "chemotherapy", "radiation", "PET CT", "CT scan", "MRI", "UHID", "Ayushman"]
SARVAM = "https://api.sarvam.ai"

# ---------------- 1. Knowledge base: sample hospital, English + Hindi ----------------
KB = [
 {"id": "REG-LOC-01", "dept": "Registration",
  "keys": ["registration", "register", "रजिस्ट्रेशन", "पंजीकरण", "पर्चा", "parcha", "नया मरीज", "new patient", "पहली बार", "first time", "uhid"],
  "en": "New patient registration is on the ground floor, main lobby, counters 1 to 6, from 7:30 am to 1 pm. Please bring your Aadhaar card, old reports and referral slip.",
  "hi": "नया रजिस्ट्रेशन ग्राउंड फ़्लोर, मेन लॉबी में काउंटर 1 से 6 पर होता है, सुबह साढ़े सात से दोपहर एक बजे तक। आधार कार्ड, पुरानी रिपोर्ट और रेफ़रल पर्ची साथ लाइए।"},
 {"id": "REG-LOC-02", "dept": "OPD",
  "keys": ["opd", "ओपीडी", "डॉक्टर कहाँ", "doctor kahan", "where is the doctor", "doctor's room", "डॉक्टर से मिल", "consultation"],
  "en": "The Oncology OPD is on the first floor, Wing A, rooms 101 to 115. Your room number is printed on your OPD slip.",
  "hi": "ऑन्कोलॉजी ओपीडी पहली मंज़िल, विंग A में, कमरा 101 से 115 तक है। आपका कमरा नंबर आपकी ओपीडी पर्ची पर छपा है।"},
 {"id": "PATH-LOC-01", "dept": "Pathology",
  "keys": ["blood", "खून", "ब्लड", "cbc", "सीबीसी", "sample", "सैंपल", "pathology", "पैथोलॉजी", "urine", "पेशाब", "टेस्ट", "test", "khoon"],
  "en": "Blood samples are given on the ground floor, Wing B, Room 12, next to the pharmacy under the blue sign. Please pay at the billing counter first and keep the receipt.",
  "hi": "खून की जाँच का सैंपल ग्राउंड फ़्लोर, विंग B, कमरा 12 में दिया जाता है, फ़ार्मेसी के बगल में, नीले बोर्ड के पास। पहले बिलिंग काउंटर पर भुगतान करें और रसीद साथ रखें।"},
 {"id": "PATH-STEP-03", "dept": "Pathology",
  "keys": ["biopsy", "बायोप्सी", "slide", "स्लाइड", "block", "ब्लॉक"],
  "en": "Biopsy slides or blocks from outside are submitted at the Histopathology reception, ground floor, Room 15. Bring the old biopsy report and your doctor's slip.",
  "hi": "बाहर से लाई गई बायोप्सी स्लाइड या ब्लॉक ग्राउंड फ़्लोर, कमरा 15, हिस्टोपैथोलॉजी रिसेप्शन पर जमा होते हैं। पुरानी बायोप्सी रिपोर्ट और डॉक्टर की पर्ची साथ लाइए।"},
 {"id": "PATH-RPT-01", "dept": "Reports",
  "keys": ["report", "रिपोर्ट", "result", "कब मिलेगी", "kab milegi", "when will i get"],
  "en": "Blood reports are usually ready the same evening or the next day. Biopsy reports take 5 to 10 working days. The exact date is on your receipt. Collect a printed copy at the report counter, ground floor, Room 14.",
  "hi": "ब्लड रिपोर्ट आम तौर पर उसी शाम या अगले दिन मिलती है, बायोप्सी रिपोर्ट 5 से 10 कामकाजी दिनों में। सही तारीख़ आपकी रसीद पर लिखी है। प्रिंट कॉपी ग्राउंड फ़्लोर, कमरा 14 के रिपोर्ट काउंटर से लें।"},
 {"id": "RAD-LOC-01", "dept": "Radiology",
  "keys": ["ct", "सीटी", "mri", "एमआरआई", "scan", "स्कैन", "x-ray", "xray", "एक्स रे", "एक्सरे", "ultrasound", "अल्ट्रासाउंड", "सोनोग्राफी", "radiology"],
  "en": "Radiology is on the ground floor, Wing C. Walk past the pharmacy and turn right at the green sign. CT is in Room C5 and MRI in Room C7. Follow the preparation written on your appointment slip.",
  "hi": "रेडियोलॉजी ग्राउंड फ़्लोर, विंग C में है। फ़ार्मेसी के आगे हरे बोर्ड से दाईं ओर मुड़िए। सीटी कमरा C5 में और एमआरआई कमरा C7 में होता है। स्कैन से पहले की तैयारी आपकी अपॉइंटमेंट पर्ची पर लिखी है, उसी का पालन करें।"},
 {"id": "RAD-LOC-02", "dept": "Nuclear Medicine",
  "keys": ["pet", "पेट स्कैन", "पीईटी", "nuclear"],
  "en": "PET-CT is in the Nuclear Medicine department, basement, Wing C. Take the Wing C lift down. Plan for two to three hours in total.",
  "hi": "पेट-सीटी स्कैन न्यूक्लियर मेडिसिन विभाग में होता है, बेसमेंट, विंग C में। विंग C की लिफ़्ट से नीचे जाइए। इसमें कुल दो से तीन घंटे लग सकते हैं।"},
 {"id": "CHEMO-LOC-01", "dept": "Chemotherapy Day Care",
  "keys": ["chemo", "कीमो", "kimo", "किमो", "day care", "डे केयर", "infusion", "ड्रिप"],
  "en": "Chemotherapy Day Care is on the second floor, Wing A, rooms 201 to 210, to the right of the lift under the purple sign. On chemo day, arrive by 8:30 am with your file, latest blood report and a water bottle.",
  "hi": "कीमोथेरेपी डे केयर दूसरी मंज़िल, विंग A में, कमरा 201 से 210 तक है, लिफ़्ट से दाईं ओर बैंगनी बोर्ड। कीमो वाले दिन सुबह साढ़े आठ तक पहुँचें और अपनी फ़ाइल, ताज़ा ब्लड रिपोर्ट और पानी की बोतल साथ लाएँ।"},
 {"id": "RT-LOC-01", "dept": "Radiation Oncology",
  "keys": ["radiation", "रेडिएशन", "सिकाई", "सेकाई", "radiotherapy", "रेडियोथेरेपी", "sikai"],
  "en": "Radiation Oncology is in the basement, Wing D. Take the Wing D lift down and show your RT card at reception, Room D-01. Please arrive 15 minutes before your slot.",
  "hi": "रेडिएशन विभाग बेसमेंट, विंग D में है। विंग D की लिफ़्ट से नीचे जाकर कमरा D-01 रिसेप्शन पर अपना आरटी कार्ड दिखाएँ। अपने टाइम से पंद्रह मिनट पहले पहुँचें।"},
 {"id": "COM-FEE-01", "dept": "Billing / Ayushman",
  "keys": ["fee", "फ़ीस", "फीस", "bill", "बिल", "payment", "pay", "पैसा", "पैसे", "भुगतान", "आयुष्मान", "ayushman", "insurance", "बीमा", "upi", "cost", "paisa"],
  "en": "Billing counters 1 to 4 are on the ground floor; cash, UPI and cards are accepted. Ayushman Bharat card holders should first go to the Ayushman desk at counter 5 with Aadhaar and the doctor's slip.",
  "hi": "बिलिंग काउंटर 1 से 4 ग्राउंड फ़्लोर पर हैं, कैश, यूपीआई और कार्ड चलते हैं। आयुष्मान भारत कार्ड वाले मरीज़ पहले काउंटर 5 पर आयुष्मान डेस्क जाएँ, आधार और डॉक्टर की पर्ची साथ रखें।"},
 {"id": "PHARM-LOC-01", "dept": "Pharmacy",
  "keys": ["pharmacy", "फ़ार्मेसी", "फार्मेसी", "दवाई कहाँ", "दवा कहाँ", "medicine kahan", "where can i buy medicine", "chemist", "मेडिकल स्टोर", "medical store"],
  "en": "The hospital pharmacy is on the ground floor, opposite the main lift, open 8 am to 8 pm. Please bring your doctor's prescription.",
  "hi": "अस्पताल की फ़ार्मेसी ग्राउंड फ़्लोर पर, मुख्य लिफ़्ट के सामने है, सुबह आठ से रात आठ बजे तक। डॉक्टर की पर्ची साथ लाइए।"},
 {"id": "COM-FAC-01", "dept": "Facilities",
  "keys": ["wheelchair", "व्हीलचेयर", "व्हील चेयर", "lift", "लिफ़्ट", "लिफ्ट", "washroom", "बाथरूम", "शौचालय", "toilet", "canteen", "कैंटीन", "water", "पानी", "parking", "पार्किंग"],
  "en": "Wheelchairs are free at the help desk near Gate 1. Lifts are in the centre of each floor, and washrooms and drinking water are at both ends of every corridor. The canteen is on the ground floor behind the main lobby.",
  "hi": "व्हीलचेयर गेट 1 पर हेल्प डेस्क के पास मुफ़्त मिलती है। लिफ़्ट हर मंज़िल के बीच में है, शौचालय और पीने का पानी हर गलियारे के दोनों छोर पर है। कैंटीन ग्राउंड फ़्लोर पर मेन लॉबी के पीछे है।"},
 {"id": "COM-TIME-01", "dept": "Timings",
  "keys": ["timing", "timings", "टाइम", "समय", "कब खुल", "open", "sunday", "रविवार", "छुट्टी", "बंद", "closed"],
  "en": "OPD runs Monday to Saturday, 8:30 am to 2 pm. On Sundays only Emergency is open.",
  "hi": "ओपीडी सोमवार से शनिवार, सुबह साढ़े आठ से दोपहर दो बजे तक चलती है। रविवार को सिर्फ़ इमरजेंसी खुली रहती है।"},
]

# ---------------- 2. Patient journey state (MOCK data) ----------------
PATIENTS = {
 "1001": {"name": "Sunita Devi", "stage": "DIAGNOSTICS → OPD REVIEW",
          "en": "Your biopsy report is ready. Your next step: meet the doctor tomorrow at 10 am, first floor, OPD Room 104. Please bring your full report file.",
          "hi": "आपकी बायोप्सी रिपोर्ट तैयार है। आपका अगला कदम: कल सुबह दस बजे पहली मंज़िल, ओपीडी कमरा 104 में डॉक्टर से मिलना। अपनी सारी रिपोर्ट की फ़ाइल साथ लाइए।"},
 "1002": {"name": "Ramesh Kumar", "stage": "TREATMENT – CHEMO CYCLE 3",
          "en": "Your third chemo session is the day after tomorrow. That morning, give your blood sample at 7:30 am in Pathology, Room 12, then reach Day Care on the second floor by 8:30.",
          "hi": "आपका तीसरा कीमो सत्र परसों है। उसी दिन सुबह साढ़े सात बजे पैथोलॉजी, कमरा 12 में खून का सैंपल दें, फिर साढ़े आठ तक दूसरी मंज़िल डे केयर पहुँचें।"},
 "1003": {"name": "Fatima Begum", "stage": "TREATMENT – RADIATION (DAY 12 of 25)",
          "en": "Today is day 12 of your radiation, at 12 noon. Please reach basement Wing D, Room D-01, 15 minutes early with your RT card.",
          "hi": "आज आपका रेडिएशन का बारहवाँ दिन है, समय दोपहर बारह बजे। बेसमेंट विंग D, कमरा D-01 पर पंद्रह मिनट पहले पहुँचें और आरटी कार्ड साथ रखें।"},
}
PERSONAL_WORDS = ["अगला", "आगे क्या", "अब क्या", "अब कहाँ", "next", "my ", "मेरा", "मेरी", "मुझे कहाँ", "aage kya", "ab kya", "mera", "meri"]

# ---------------- 3. Guardrails (checked BEFORE the knowledge base) ----------------
EMERGENCY = ["सांस नहीं", "साँस नहीं", "सांस फूल", "बेहोश", "खून बह", "सीने में दर्द", "chest pain", "can't breathe",
             "cannot breathe", "not breathing", "unconscious", "bleeding", "emergency", "इमरजेंसी", "तेज़ बुखार",
             "तेज बुखार", "दौरा", "seizure", "behosh", "saans nahi",
             "tez bukhar", "tej bukhar", "high fever", "khoon beh", "saans phool", "seene mein dard", "seene me dard", "dora pad"]
CLINICAL  = ["कितनी दवा", "कौन सी दवा", "कौनसी दवा", "दवा लूँ", "दवा लू", "which medicine", "what medicine", "dose", "dosage",
             "डोज़", "डोज", "tablet", "गोली", "दर्द", "pain", "बुखार", "fever", "उल्टी", "vomit", "side effect",
             "साइड इफेक्ट", "साइड इफ़ेक्ट", "ठीक हो जा", "will i survive", "बचूँगा", "बचेंगे", "stage", "स्टेज",
             "रिपोर्ट का मतलब", "रिपोर्ट में क्या", "what does my report", "कैंसर फैल", "spread", "क्या मुझे कैंसर",
             "do i have cancer", "हीमोग्लोबिन", "haemoglobin", "hemoglobin", "शुगर बढ़", "क्या खाऊँ", "what should i eat",
             "dawa", "dard", "bukhar"]
EMOTIONAL = ["डर लग", "डर रहा", "डरी", "घबराहट", "घबरा", "अकेला", "अकेली", "रोना", "टूट गया", "टूट गई", "scared",
             "afraid", "frightened", "depressed", "anxious", "परेशान हूँ", "dar lag"]

REPLIES = {
 "EMERGENCY": {"en": "This sounds like an emergency. Please go to Emergency at Gate 2 right now or tell the nearest staff member. If you are at home, call 108. I am alerting the duty nurse.",
               "hi": "यह इमरजेंसी लगती है। तुरंत गेट 2 पर इमरजेंसी विभाग जाइए या पास के किसी स्टाफ़ को बताइए। घर पर हैं तो 108 पर कॉल करें। मैं ड्यूटी नर्स को सूचना भेज रहा हूँ।"},
 "CLINICAL":  {"en": "That's an important question for your doctor or nurse. I can't give medical advice. I'm sending your question to the nurse navigator, who will contact you shortly.",
               "hi": "यह सवाल आपके डॉक्टर या नर्स से पूछना ही सही रहेगा, मैं मेडिकल सलाह नहीं दे सकता। मैं आपका सवाल नर्स नेविगेटर को भेज रहा हूँ, वो जल्द आपसे बात करेंगी।"},
 "EMOTIONAL": {"en": "I understand, this is a hard time, and you are not alone. Shall I connect you to our counsellor? They can speak with you today.",
               "hi": "मैं समझ सकता हूँ, यह मुश्किल समय है, और आप अकेले नहीं हैं। क्या मैं आपको हमारे काउंसलर से जोड़ दूँ? वो आज ही आपसे बात कर सकते हैं।"},
 "UNKNOWN":   {"en": "Sorry, I'm not sure about that. Let me connect you to the help desk.",
               "hi": "माफ़ कीजिए, मुझे इसकी पक्की जानकारी नहीं है। मैं आपको हेल्प डेस्क से जोड़ रहा हूँ।"},
 "EMPTY":     {"en": "Please speak or type your question.", "hi": "कृपया अपना सवाल बोलें या लिखें।"},
 "GREET":     {"en": "Namaste! How can I help you today? You can ask where a department is, what to bring, or what your next step is.",
               "hi": "नमस्ते! आज मैं आपकी क्या मदद करूँ? आप पूछ सकते हैं कि कोई विभाग कहाँ है, क्या साथ लाना है, या आपका अगला कदम क्या है।"},
}
TAGS = {"EMERGENCY": "🚨 EMERGENCY → duty nurse alerted", "CLINICAL": "🩺 CLINICAL → nurse navigator handoff",
        "EMOTIONAL": "💛 EMOTIONAL → counsellor", "UNKNOWN": "❓ LOW CONFIDENCE → help desk", "EMPTY": "—"}

HINGLISH = ["kahan", "kaha", "kya", "hai", "mera", "meri", "mujhe", "kab", "kaise", "karna", "jana", "jaana",
            "milegi", "dawa", "dard", "nahi", "aage", "chahiye", "kitna", "paisa", "khoon", "likha"]

def pick_lang(text, setting, stt_lang=None):
    if setting == "English":
        return "en"
    if setting == "हिंदी":
        return "hi"
    if re.search(r"[ऀ-ॿ]", text or ""):          # Devanagari script → Hindi
        return "hi"
    words = re.findall(r"[a-z]+", (text or "").lower())
    if sum(w in HINGLISH for w in words) >= 1:              # romanised Hinglish → Hindi
        return "hi"
    if stt_lang and stt_lang.startswith("hi"):
        return "hi"
    return "en"

def hit(k, t):
    # short English keys (ct, pet, opd, pay...) must match a whole word, so "doctor" doesn't trigger "ct"
    if k.isascii() and len(k) <= 4:
        return re.search(r"\b" + re.escape(k) + r"\b", t) is not None
    return k in t

def answer(q, uhid, lang):
    if not q or not q.strip():
        return REPLIES["EMPTY"][lang], TAGS["EMPTY"]
    t = " " + q.lower() + " "
    for kind, words in (("EMERGENCY", EMERGENCY), ("CLINICAL", CLINICAL), ("EMOTIONAL", EMOTIONAL)):
        if any(w in t for w in words):                       # 1. safety first
            return REPLIES[kind][lang], TAGS[kind]
    if re.fullmatch(r"\W*(hi|hello|hey|namaste|namaskar|नमस्ते|नमस्कार|हेलो|हाय)\W*", q.strip().lower()):
        return REPLIES["GREET"][lang], "👋 GREETING"
    if uhid in PATIENTS and any(w in t for w in PERSONAL_WORDS) and \
       any(w in t for w in ["next", "अगला", "आगे", "अब", "aage", "ab ", "step", "कदम", "kadam", "what should i do", "where should i go", "कहाँ जाना", "kahan jana"]):
        p = PATIENTS[uhid]                                   # 2. personalised next step
        hello = f"Hello {p['name']}. " if lang == "en" else f"नमस्ते {p['name']} जी। "
        return hello + p[lang], f"👤 PERSONALISED · journey: {p['stage']}"
    best, score = None, 0                                    # 3. knowledge base
    for item in KB:
        s = sum(1 for k in item["keys"] if hit(k, t))
        if s > score:
            best, score = item, s
    if best:
        return best[lang], f"📚 KB: {best['dept']} [{best['id']}]"
    return REPLIES["UNKNOWN"][lang], TAGS["UNKNOWN"]

# ---------------- 4. Sarvam voice ----------------
def stt(path):
    ext = os.path.splitext(path)[1].lower() or ".wav"
    with open(path, "rb") as f:
        r = requests.post(f"{SARVAM}/speech-to-text", headers={"api-subscription-key": SARVAM_KEY},
                          files={"file": ("audio" + ext, f, mimetypes.guess_type("a" + ext)[0] or "application/octet-stream")}, data={"model": "saaras:v4", "language_code": "unknown", "mode": "codemix", "keyterms": json.dumps(KEYTERMS)}, timeout=60)
    r.raise_for_status()
    j = r.json()
    return j.get("transcript", ""), (j.get("language_code") or "")

def tts(text, lang):
    r = requests.post(f"{SARVAM}/text-to-speech",
                      headers={"api-subscription-key": SARVAM_KEY, "Content-Type": "application/json"},
                      json={"text": text[:1400], "target_language_code": "hi-IN" if lang == "hi" else "en-IN",
                            "model": "bulbul:v3", "speaker": "priya", "speech_sample_rate": 16000,
                            "enable_preprocessing": True}, timeout=60)
    r.raise_for_status()
    j = r.json()
    b64 = (j.get("audios") or j.get("audio"))[0]
    path = tempfile.NamedTemporaryFile(delete=False, suffix=".wav").name
    with open(path, "wb") as f:
        f.write(base64.b64decode(b64))
    return path, b64

# ---------------- 5. WhatsApp-style chat rendering ----------------
def now():
    return datetime.datetime.now().strftime("%H:%M")

def render(msgs, show_route):
    out = ['<div class="wa-header"><div class="wa-avatar">🛶</div><div><div class="wa-name">OncoSaathi</div>'
           '<div class="wa-status">online · Sample Cancer Centre</div></div></div>',
           '<div class="wa-chat"><div class="wa-inner">',
           '<div class="wa-day">TODAY</div>',
           '<div class="wa-note">🔒 Prototype with sample hospital data. OncoSaathi guides you around the hospital; it never gives medical advice.</div>']
    for m in msgs:
        side = "me" if m["role"] == "user" else "bot"
        body = ""
        if m.get("voice"):
            body += '<div class="wa-vlabel">🎤 Voice message</div>'
        if m.get("audio_b64"):
            body += f'<audio controls preload="none" src="data:audio/wav;base64,{m["audio_b64"]}"></audio>'
        body += f'<div class="wa-text">{html.escape(m["text"])}</div>'
        if side == "bot" and show_route and m.get("route"):
            body += f'<div class="wa-route">{html.escape(m["route"])}</div>'
        ticks = ' <span class="wa-ticks">✓✓</span>' if side == "me" else ""
        out.append(f'<div class="wa-row {side}"><div class="wa-bubble {side}">{body}'
                   f'<div class="wa-time">{m["time"]}{ticks}</div></div></div>')
    out.append('</div></div>')
    return "\n".join(out)

WELCOME = {"role": "bot", "time": "", "route": "",
           "text": "Namaste! I'm OncoSaathi, your hospital guide. 🙏\n"
                   "Ask me where to go, what to bring, or what your next step is, in English or Hindi. "
                   "\n\nनमस्ते! मैं ओन्कोसाथी हूँ। बोलकर या लिखकर पूछिए, कहाँ जाना है या अगला कदम क्या है।"}

def respond(q, history, uhid, lang_setting, show_route, voice=False, stt_lang=None, note=""):
    lang = pick_lang(q, lang_setting, stt_lang)
    ans, route = answer(q, uhid, lang)
    if note:
        route = route + "\n" + note
    history = history + [{"role": "user", "text": q or "(no speech detected)", "time": now(), "voice": voice}]
    bot = {"role": "bot", "text": ans, "time": now(), "route": route}
    audio_path = None
    if SARVAM_KEY:
        try:
            audio_path, b64 = tts(ans, lang)
            bot["audio_b64"] = b64
        except Exception as e:
            bot["route"] += f"\n⚠️ Voice reply error: {e}"
    history = history + [bot]
    for m in history[:-6]:                    # keep the page light: only the last 3 replies keep audio
        m.pop("audio_b64", None)
    return render(history, show_route), history, audio_path

def on_text(q, history, uhid, lang_setting, show_route):
    if not q or not q.strip():
        return gr.update(), history, None, ""
    chat, history, audio = respond(q.strip(), history, uhid, lang_setting, show_route)
    return chat, history, audio, ""

def on_voice(audio, history, uhid, lang_setting, show_route):
    if not audio:
        return gr.update(), history, None, None
    if not SARVAM_KEY:
        note = "⚠️ Add your Sarvam key to use voice. For now, please type."
        chat, history, a = respond("", history, uhid, lang_setting, show_route, voice=True, note=note)
        return chat, history, a, None
    try:
        q, stt_lang = stt(audio)
        note = f"🗣️ detected language: {stt_lang or '?'}"
    except Exception as e:
        q, stt_lang, note = "", None, f"⚠️ Speech-to-text error: {e}"
    chat, history, a = respond(q, history, uhid, lang_setting, show_route, voice=True, stt_lang=stt_lang, note=note)
    return chat, history, a, None

def reset(show_route):
    return render([WELCOME], show_route), [WELCOME], None

def rerender(history, show_route):
    return render(history, show_route)

# ---------------- 6. UI ----------------
CSS = """
.gradio-container {max-width: 480px !important; margin: auto !important; padding: 8px !important;}
.wa-header {background:#075E54; border-radius:12px 12px 0 0; padding:10px 14px; display:flex; align-items:center; gap:10px;}
.wa-header * {color:#fff !important;}
.wa-avatar {width:40px; height:40px; border-radius:50%; background:#25D366; display:flex; align-items:center; justify-content:center; font-size:22px;}
.wa-name {font-weight:600; font-size:16px;} .wa-status {font-size:12px; opacity:.85;}
.wa-chat {background:#ECE5DD; background-image:radial-gradient(#d9d2c5 1px, transparent 1px); background-size:18px 18px;
          height:470px; overflow-y:auto; display:flex; flex-direction:column-reverse;
          font-family: Helvetica, Arial, sans-serif;}
.wa-inner {padding:10px 8px; display:flex; flex-direction:column; gap:4px;}
.wa-day {align-self:center; background:#E1F2FB; color:#555; font-size:11px; padding:3px 10px; border-radius:8px; margin:4px 0;}
.wa-note {align-self:center; background:#FFF5C4; color:#555; font-size:11px; padding:5px 10px; border-radius:8px; text-align:center; max-width:90%; margin-bottom:6px;}
.wa-row {display:flex;} .wa-row.me {justify-content:flex-end;} .wa-row.bot {justify-content:flex-start;}
.wa-bubble {max-width:80%; padding:6px 9px 4px; border-radius:8px; box-shadow:0 1px 0.5px rgba(0,0,0,.13); font-size:14.5px; line-height:1.35; color:#111;}
.wa-bubble.me {background:#DCF8C6; border-top-right-radius:0;} .wa-bubble.bot {background:#fff; border-top-left-radius:0;}
.wa-text {white-space:pre-wrap;}
.wa-vlabel {font-size:12px; color:#075E54; font-weight:600; margin-bottom:2px;}
.wa-bubble audio {width:230px; height:34px; margin:2px 0 4px;}
.wa-time {text-align:right; font-size:10.5px; color:#667781; margin-top:2px;}
.wa-ticks {color:#34B7F1;}
.wa-route {margin-top:5px; font-size:11px; color:#075E54; background:#E7F6EE; border-radius:6px; padding:3px 6px; white-space:pre-wrap;}
#wa-input {background:#F0F0F0; border-radius:0 0 12px 12px; padding:6px;}
#send-btn {background:#25D366 !important; color:#fff !important; border:none !important; min-width:48px !important; border-radius:24px !important; font-size:18px !important;}
#wa-input textarea, #wa-input input {background:#fff !important; color:#111 !important; border-radius:20px !important;}
#wa-input textarea::placeholder {color:#667781 !important;}
#wa-reply-audio {position:absolute !important; width:1px !important; height:1px !important; overflow:hidden !important; opacity:0 !important;}
"""

with gr.Blocks(title="OncoSaathi – WhatsApp") as demo:
    history = gr.State([WELCOME])
    chat = gr.HTML(render([WELCOME], False))
    with gr.Group(elem_id="wa-input"):
        with gr.Row(equal_height=True):
            txt = gr.Textbox(placeholder="Type a message", show_label=False, scale=6, container=False)
            send = gr.Button("➤", elem_id="send-btn", scale=1)
        mic = gr.Audio(sources=["microphone"], type="filepath", show_label=False, elem_id="wa-mic")
    reply_audio = gr.Audio(autoplay=True, interactive=False, show_label=False, elem_id="wa-reply-audio")
    with gr.Accordion("Settings", open=False):
        uhid = gr.Dropdown(["1001", "1002", "1003", "New patient"], value="1001",
                           label="Logged-in patient (mock: 1001 Sunita · 1002 Ramesh · 1003 Fatima)")
        lang_setting = gr.Radio(["Auto", "English", "हिंदी"], value="Auto", label="Reply language")
        show_route = gr.Checkbox(value=False, label="Show routing tags (for mentors)")
        clear = gr.Button("Clear chat", size="sm")

    ins = [history, uhid, lang_setting, show_route]
    txt.submit(on_text, [txt] + ins, [chat, history, reply_audio, txt])
    send.click(on_text, [txt] + ins, [chat, history, reply_audio, txt])
    mic.stop_recording(on_voice, [mic] + ins, [chat, history, reply_audio, mic])
    clear.click(reset, [show_route], [chat, history, reply_audio])
    show_route.change(rerender, [history, show_route], [chat])

FORCE_LIGHT = """<script>
const u = new URL(window.location.href);
if (u.searchParams.get('__theme') !== 'light') { u.searchParams.set('__theme', 'light'); window.location.replace(u.href); }
</script>"""

demo.launch(share=os.environ.get("SHARE") == "1", server_port=7860, css=CSS, head=FORCE_LIGHT)
