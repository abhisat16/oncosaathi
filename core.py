"""OncoSaathi core: hospital directory (hospital.json), safety keyword lists, language pick, Sarvam STT/TTS helpers.

The conversation logic lives in brain.py; the patient memory in patient_store.py. Nothing here invents a room:
every place comes from hospital.json.
"""
import base64
import json
import mimetypes
import os
import re
import tempfile

import requests
from dotenv import load_dotenv

HERE = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(HERE, ".env"))

SARVAM_KEY = os.environ.get("SARVAM_API_KEY", "")  # read from .env, never hardcoded
# bulbul:v3 "ritu": ~1.5 s per sentence. bulbul:v4-flash (ritu_hi_medical) measured 6-14 s per sentence on 20 Oct 2026,
# too slow for a live call. Switch back with ONCO_TTS_MODEL=bulbul:v4-flash in .env.
TTS_MODEL = os.environ.get("ONCO_TTS_MODEL", "bulbul:v3").strip()
TTS_VOICE = ({"hi": "ritu_hi_medical", "en": "ritu_en_medical"} if TTS_MODEL.startswith("bulbul:v4")
             else {"hi": "ritu", "en": "ritu"})
STT_MODEL = "saaras:v4"                                          # latest Sarvam STT
KEYTERMS = ["CBC", "OPD", "pathology", "biopsy", "chemo", "chemotherapy", "radiation", "PET CT", "CT scan", "MRI", "UHID",
            "Ayushman", "Tata Memorial", "endoscopy", "dharamshala"]
SARVAM = "https://api.sarvam.ai"

# ---------------- Safety keywords (checked before anything else, deterministic) ----------------
SELF_HARM = ["suicide", "kill myself", "end my life", "want to die", "jeena nahi", "jina nahi", "mar jana", "mar jaun", "mar jaaun",
             "khud ko khatam", "zindagi khatam", "आत्महत्या", "जीना नहीं", "मर जाना", "मर जाऊँ", "मर जाऊं", "ख़ुद को ख़त्म", "खुद को खत्म",
             "ज़िंदगी ख़त्म", "जिंदगी खत्म"]
EMERGENCY = ["सांस नहीं", "साँस नहीं", "सांस फूल", "साँस फूल", "बेहोश", "खून बह", "सीने में दर्द", "chest pain", "can't breathe",
             "cannot breathe", "not breathing", "unconscious", "bleeding", "emergency", "इमरजेंसी", "तेज़ बुखार",
             "तेज बुखार", "दौरा", "seizure", "behosh", "saans nahi", "tez bukhar", "tej bukhar", "high fever", "saans lene",
             "sans lene", "सांस लेने", "साँस लेने", "breathing problem", "difficulty breathing", "khoon beh", "saans phool",
             "seene mein dard", "seene me dard", "dora pad", "faint", "एमरजेंसी", "इमर्जेंसी", "emergency"]
CLINICAL = ["कितनी दवा", "कौन सी दवा", "कौनसी दवा", "दवा लूँ", "दवा लू", "which medicine", "what medicine", "dose", "dosage",
            "डोज़", "डोज", "गोली", "दर्द", "pain", "बुखार", "fever", "उल्टी", "vomit", "side effect", "साइड इफेक्ट",
            "साइड इफ़ेक्ट", "ठीक हो जा", "will i survive", "बचूँगा", "बचेंगे", "stage", "स्टेज", "रिपोर्ट का मतलब",
            "रिपोर्ट में क्या", "what does my report", "कैंसर फैल", "spread", "क्या मुझे कैंसर", "do i have cancer",
            "हीमोग्लोबिन", "haemoglobin", "hemoglobin", "शुगर बढ़", "क्या खाऊँ", "what should i eat", "dawa lu", "dawa le",
            "kaun si dawa", "kaunsi dawa", "dawa kab", "dawa kitni", "tablet kab", "dard", "bukhar", "report saying",
            "report says", "report mean", "is my report", "report me kya", "report mein kya", "report normal", "report theek",
            "report thik", "theek ho jaung", "thik ho jaung", "theek ho jaaung", "बच जाऊँ", "bach jaung", "रिपोर्ट ठीक",
            "रिपोर्ट नॉर्मल", " ulti ", "chakkar"]
EMOTIONAL = ["डर लग", "डर रहा", "डरी", "डर गई", "डर गया", "dar lag", "dar gayi", "dar gaya", "ghabra", "akela", "akeli", "ro rahi",
             "ro raha", "घबराहट", "घबरा", "अकेला", "अकेली", "रोना", "टूट गया", "टूट गई", "scared", "afraid", "frightened",
             "depressed", "anxious", "परेशान हूँ", "himmat nahi", "हिम्मत नहीं", "tension"]

HINGLISH = ["kahan", "kaha", "kya", "hai", "mera", "meri", "mujhe", "kab", "kaise", "karna", "jana", "jaana", "milegi", "dawa",
            "dard", "nahi", "aage", "chahiye", "kitna", "paisa", "khoon", "likha", "naam", "hoon", "aaj", "kal", "ho", "gaya",
            "ki", "ka", "ke", "mein", "se", "hain", "batao", "bataiye", "jagah", "liye", "aur", "bhi", "toh", "karo", "wala",
            "wali", "koi", "kuch", "abhi", "yahan", "wahan", "rehne", "rahne", "sasta", "sasti", "saste", "lana", "laana",
            "kidhar", "jaun", "jaana", "hum", "aap", "mujhe", "accha", "achha", "theek", "thik", "haan", "ji"]


# Sarvam language codes. Hindi and English answers are written by our templates; the others are translated
# (sarvam-translate:v1) from the English answer, so the facts stay the same in every language.
LANG_CODE = {"hi": "hi-IN", "en": "en-IN", "mr": "mr-IN", "od": "od-IN", "bn": "bn-IN", "gu": "gu-IN", "pa": "pa-IN",
             "ta": "ta-IN", "te": "te-IN", "kn": "kn-IN", "ml": "ml-IN"}
SCRIPTS = [("od", "\u0B00", "\u0B7F"), ("bn", "\u0980", "\u09FF"), ("gu", "\u0A80", "\u0AFF"), ("pa", "\u0A00", "\u0A7F"),
           ("ta", "\u0B80", "\u0BFF"), ("te", "\u0C00", "\u0C7F"), ("kn", "\u0C80", "\u0CFF"), ("ml", "\u0D00", "\u0D7F")]
MARATHI = re.compile(r"(?<![\u0900-\u097F])(आहे|आहेत|काय|कुठे|मला|मी|तुम्ही|कसे|कधी|नाही|पाहिजे|जायचे|सांगा)(?![\u0900-\u097F])")


def pick_lang(text, setting="Auto", stt_lang=None):
    if setting == "English":
        return "en"
    if setting == "हिंदी":
        return "hi"
    for code, lo, hi_ in SCRIPTS:                    # Odia, Bengali, Tamil… by script
        if re.search(f"[{lo}-{hi_}]", text or ""):
            return code
    if re.search(r"[ऀ-ॿ]", text or ""):          # Devanagari: Marathi if it reads like Marathi, else Hindi
        if (stt_lang or "").startswith("mr") or len(MARATHI.findall(text)) >= 1:
            return "mr"
        return "hi"
    words = re.findall(r"[a-z]+", (text or "").lower())
    if sum(w in HINGLISH for w in words) >= 1:              # romanised Hinglish -> Hindi
        return "hi"
    if stt_lang and stt_lang.startswith("hi"):
        return "hi"
    return "en"


def hit(k, t):
    # short keys must match a whole word: "doctor" mustn't trigger "ct", and "साइकोलॉजिकल" mustn't trigger "इको" (echo)
    if k.isascii() and len(k) <= 4:
        return re.search(r"\b" + re.escape(k) + r"\b", t) is not None
    if not k.isascii() and len(k) <= 5:
        return re.search(r"(?<![\u0900-\u097F])" + re.escape(k) + r"(?![\u0900-\u097F])", t) is not None
    return k in t


# ---------------- Hospital directory (hospital.json) ----------------
with open(os.path.join(HERE, "hospital.json"), encoding="utf-8") as _f:
    HOSPITAL = json.load(_f)
BLOCKS = {b["id"]: b for b in HOSPITAL["blocks"]}
FLOORS = {f["id"]: f for f in HOSPITAL["floors"]}
NAME_STOP = {"scan", "test", "tests", "clinic", "room", "rooms", "ward", "wards", "desk", "counter", "department", "unit",
             "area", "lounge", "hall", "centre", "center", "main", "oncology", "care", "and", "with", "office", "lab", "labs",
             "treatment", "before", "after", "only", "exit", "क्लिनिक", "वार्ड", "कक्ष", "और", "लैब", "डेस्क", "केंद्र", "विभाग", "ऑफ़िस",
             "इलाज", "रास्ता", "जाने", "आने", "बाहर", "पहले", "बाद", "लिए", "वाले", "सभी", "समय", "जाँच", "जांच", "सिर्फ़", "करना",
             "गेट", "मुख्य", "बैठने", "जगह", "परिवार", "स्कैन", "काउंटर", "कमरा", "hospital", "अस्पताल", "हॉस्पिटल"}
# Colloquial / Hinglish ways people ask for each department (matched in addition to the department's own name words).
SYNONYMS = {
    "A-G-HELP": ["help desk", "helpdesk", "rotunda", "रोटुंडा", "हेल्प डेस्क", "lost", "khoya"],
    "ENQUIRY": ["enquiry", "inquiry", "information counter", "पूछताछ", "इंक्वायरी", "इन्क्वायरी"],
    "HELPLINE": ["wheelchair", "stretcher", "helpline", "व्हीलचेयर", "स्ट्रेचर", "हेल्पलाइन"],
    "A-G-REG": ["registration", "register", "parcha", "parchi banani", "naya parcha", "new patient", "case file", "wprn", "रजिस्ट्रेशन", "पर्चा", "नया मरीज़", "नया पर्चा", "केस फ़ाइल"],
    "A-G-BILL": ["billing", "bill", "payment", "pay", "paise jama", "fees", "deposit", "top up", "recharge", "card balance", "smart card balance",
                 "बिल", "पैसे जमा", "फ़ीस", "डिपॉज़िट", "बैलेंस"],
    "NEW-CARD": ["new smart card", "card kho", "card lost", "lost card", "naya card", "कार्ड खो", "नया कार्ड"],
    "A-G-PMJAY": ["ayushman", "pmjay", "pm-jay", "mjpjay", "jan arogya", "आयुष्मान"],
    "A-G-SW": ["financial", "paisa nahi", "paise nahi", "aarthik", "free treatment", "ngo", "scheme", "yojana", "social worker", "आर्थिक", "योजना", "पैसे नहीं"],
    "REIMB": ["reimbursement", "insurance", "mediclaim", "claim", "lic", "बीमा", "क्लेम", "इंश्योरेंस"],
    "CONCESSION": ["concession letter", "concession", "railway concession", "रियायत", "कंसेशन"],
    "ADMIT": ["admission", "admit", "bharti", "bed kab", "भर्ती", "एडमिशन"],
    "A-G-CANT": ["canteen", "cafeteria", "eatery", "khana", "food", "coffee", "chai", "कैंटीन", "खाना", "चाय", "paani", "water"],
    "CLOAK": ["cloak room", "luggage", "saman rakhna", "bag rakhna", "सामान रख", "क्लॉक रूम", "लगेज"],
    "ATM": ["atm", "एटीएम", "bank", "बैंक", "cash nikal"],
    "CHARGING": ["charging", "mobile charge", "phone charge", "चार्जिंग", "चार्ज"],
    "SECURITY": ["security", "guard", "सिक्योरिटी"],
    "CORE-G-PHARM": ["pharmacy", "pharmacology", "pharmacist", "dispensary", "फार्माकोलॉजी", "डिस्पेंसरी", "medical store", "chemist", "dawai kahan", "dawa kahan",
                     "दवाई कहाँ", "दवा कहाँ", "फ़ार्मेसी", "फार्मेसी"],
    "B-G-SAMPLE": ["blood collection", "ब्लड कलेक्शन", "blood test", "blood sample", "sample collection", "khoon ki jaanch", "khoon ki janch", "cbc", "urine",
                   "peshab", "खून की जाँच", "ख़ून की जाँच", "खून की जांच", "पेशाब", "सैंपल"],
    "B-G-REPORT": ["report counter", "report kahan", "report kab", "report collect", "ct report", "mri report", "रिपोर्ट कहाँ", "रिपोर्ट कब", "रिपोर्ट कलेक्ट", "रिपोर्ट लेनी"],
    "MEDREC": ["medical records", "record room", "old file", "पुरानी फ़ाइल", "मेडिकल रिकॉर्ड"],
    "C-G-XRAY": ["x-ray", "xray", "x ray", "एक्स-रे", "एक्सरे"],
    "D-G-RT": ["radiation", "radiotherapy", "रेडियोथेरेपी", "रेडियोथेरपी", "sikai", "sekai", "सिकाई", "सेकाई", "रेडिएशन", "rt card", "linac"],
    "D-G-ER": ["emergency", "casualty", "इमरजेंसी", "कैज़ुअल्टी", "कैजुअल्टी"],
    "A-1-MED": ["medical oncology", "chemo doctor", "chemo wale doctor", "medicine department", "मेडिकल ऑन्कोलॉजी"],
    "A-1-SURG": ["surgeon", "surgery opd", "surgery wale doctor", "operation wale doctor", "oncology surgery", "onco surgery", "oncosurgery",
                 "surgery department", "surgical department", "ऑन्कोलॉजी सर्जरी", "सर्जरी डिपार्टमेंट", "सर्जरी विभाग", "सर्जिकल"],
    "A-1-RTC": ["radiation doctor", "radiation consult", "radiation opd"],
    "B-1-PATH": ["pathology", "पैथोलॉजी", "biopsy", "slide", "slides", "block", "fnac", "histopathology", "बायोप्सी", "स्लाइड"],
    "CYTO": ["cytopathology", "cytology", "साइटोपैथोलॉजी"],
    "BIOCHEM": ["biochemistry", "बायोकेमिस्ट्री"],
    "MOLPATH": ["molecular", "hematopathology", "haematopathology", "मॉलिक्यूलर"],
    "MICRO": ["microbiology", "culture test", "माइक्रोबायोलॉजी"],
    "BLOODBANK": ["blood bank", "blood donate", "blood donation", "donor", "platelet", "transfusion", "ब्लड बैंक", "रक्तदान", "प्लेटलेट"],
    "C-1-RADREC": ["radiology", "radiography", "radiographer", "radiodiagnosis", "radio diagnosis", "imaging", "scan booking", "scan appointment",
                   "scan department", "रेडियोलॉजी", "रेडिओलॉजी", "रेडियोलॉजी डिपार्टमेंट", "इमेजिंग", "स्कैन बुकिंग"],
    "C-1-CT": ["ct scan", "ct", "सीटी", "सिटी स्कैन"],
    "C-1-MRI": ["mri", "एमआरआई"],
    "C-1-USG": ["mammography", "mammogram", "मैमोग्राफी", "मैमोग्राफ़ी"],
    "IR": ["interventional radiology", "interventional", "इंटरवेंशनल"],
    "D-1-OTWAIT": ["operation chal", "surgery waiting", "operation ke time", "intezaar", "इंतज़ार", "ऑपरेशन चल", "घरवाले"],
    "A-2-DC": ["chemo", "chemotherapy", "day care", "daycare", "kimo", "कीमो", "डे केयर", "डे-केयर", "drip", "chemo ward", "कीमो वार्ड"],
    "A-2-PEDS": ["children", "child", "bachche", "bachcha", "bachchon", "बच्चे", "बच्चा", "बच्चों", "paediatric", "pediatric"],
    "B-2-ENDO": ["endoscopy", "colonoscopy", "doorbeen", "एंडोस्कोपी", "दूरबीन"],
    "C-2-PET": ["pet scan", "pet-ct", "pet ct", "spect", "nuclear", "पेट-सीटी", "पेट सीटी", "पीईटी"],
    "D-2-ICU": ["icu", "hdu", "आईसीयू"],
    "A-3-HN": ["head and neck", "mouth cancer", "muh ka", "gale ka", "throat", "मुँह", "गले"],
    "A-3-BR": ["breast", "स्तन", "ब्रेस्ट"],
    "A-3-GYN": ["gynae", "gyne", "gynec", "cervix", "uterus", "ovary", "bachchedani", "uro", "kidney cancer", "prostate", "bladder",
                "बच्चेदानी", "स्त्री रोग", "गायनेक", "प्रोस्टेट"],
    "GI": ["gastro", "stomach cancer", "pet ka cancer", "liver", "colon", "rectum", "food pipe", "आँत", "पेट का कैंसर", "लिवर"],
    "HEME": ["leukemia", "leukaemia", "lymphoma", "myeloma", "blood cancer", "हीमैटोलॉजी", "ल्यूकेमिया", "लिम्फोमा", "ब्लड कैंसर", "खून का कैंसर"],
    "BST": ["bone cancer", "sarcoma", "soft tissue", "lung cancer", "thoracic", "फेफड़े का कैंसर", "हड्डी का कैंसर", "थोरेसिक"],
    "NEURO": ["brain tumour", "brain tumor", "neuro", "दिमाग", "ब्रेन ट्यूमर", "न्यूरो"],
    "DENTAL": ["dental", "dentist", "teeth", "daant", "दाँत", "डेंटल"],
    "A-4-TOB": ["preventive oncology", "screening", "cancer screening", "प्रिवेंटिव", "स्क्रीनिंग"],
    "B-3-PAC": ["pac", "fitness", "anaesthesia", "anesthesia", "operation se pehle", "ऑपरेशन से पहले"],
    "B-3-CARDIO": ["ecg", "ईसीजी"],
    "ECHO": ["echo", "2d echo", "इको"],
    "PFT": ["pft", "lung test", "lung function", "फेफड़ों की जाँच"],
    "A-4-PSY": ["psychiatry", "psychiatrist", "psycho", "psychological", "psychology", "psychologist", "साइकोलॉजिकल", "साइकोलॉजी", "मनोवैज्ञानिक", "मनोरोग"],
    "KEVAT": ["kevat", "kewat", "केवट", "navigator", "नेविगेटर", "counselling", "counseling", "counsellor", "काउंसलर", "काउंसलिंग", "mann ki baat"],
    "A-4-PALL": ["palliative", "पैलिएटिव"],
    "PAIN": ["pain clinic", "dard clinic", "पेन क्लिनिक"],
    "A-4-NUT": ["diet", "dietician", "nutrition", "khana kya", "आहार", "डाइट"],
    "PHYSIO": ["physiotherapy", "physio", "occupational therapy", "फ़िज़ियो", "फिजियो"],
    "SPEECH": ["speech therapy", "स्पीच थेरेपी"],
    "STOMA": ["stoma", "colostomy", "स्टोमा"],
    "MEDICINE": ["physician", "general medicine", "फ़िज़िशियन", "जनरल मेडिसिन"],
    "TELECONSULT": ["teleconsultation", "teleconsult", "video consult", "online consult", "टेलीकंसल्टेशन"],
    "D-4-ADMIN": ["admin", "superintendent", "complaint", "shikayat", "public relation", "शिकायत", "प्रशासन"],
}


def _unit_keys(u):
    words = re.findall(r"[a-z0-9-]+|[ऀ-ॿ]+", (u["name"] + " " + u.get("name_hi", "")).lower())
    keys = {w for w in words if w not in NAME_STOP and len(w) >= (4 if w.isascii() else 3)}
    return keys | {s.lower() for s in SYNONYMS.get(u["id"], [])}


DIRECTORY = [(u, _unit_keys(u)) for u in HOSPITAL["units"] + HOSPITAL["campus"]]


def directory_match(t):
    """Best hospital-directory unit for the query text; colloquial synonyms count extra."""
    best, score = None, 0
    for u, keys in DIRECTORY:
        if u.get("public") is False and u["name"].lower() not in t:
            continue                                         # staff-only rooms only when named exactly
        s = 2 * sum(1 for k in keys if hit(k, t))
        if s and any(hit(k.lower(), t) for k in SYNONYMS.get(u["id"], [])):
            s += 1
        if s > score:
            best, score = u, s
    return best, score


def directory_answer(u, lang):
    """Full written answer for chat: where, timings, what to bring, note, and how to walk there."""
    hi = lang == "hi"
    g = lambda f: (u.get(f + "_hi") or u.get(f)) if hi else u.get(f)
    name = u.get("name_hi") if hi else u["name"]
    if "block" not in u:                                     # campus place (gate, taxi stand…)
        return f"{name}: {g('note')}"
    b, f = BLOCKS[u["block"]], FLOORS[u["floor"]]
    wing = b["name_hi"].split("·")[0].strip() if hi else b["name"]
    floor = f["name_hi"] if hi else f["name"].lower()
    if u.get("public") is False:
        return (f"{name} ({wing}, {floor}) सिर्फ़ स्टाफ़ के लिए है। अगर आपको वहाँ जाने को कहा गया है, तो GJB ग्राउंड फ़्लोर के इंक्वायरी काउंटर पर पूछिए।" if hi else
                f"{name} ({wing}, {floor}) is a staff-only area. If you've been asked to go there, please ask at the Enquiry counter on the GJB ground floor.")
    parts = [f"{name}: {wing}, {floor}, {g('rooms')}।" if hi else f"{name}: {wing}, {floor}, {g('rooms')}."]
    if u.get("path"):
        parts.append(("🚶 " + g("path")))
    if u.get("hours"):
        parts.append(f"समय: {g('hours')}।" if hi else f"Timings: {g('hours')}.")
    if u.get("bring"):
        parts.append(f"साथ लाइए: {g('bring')}।" if hi else f"Please bring: {g('bring')}.")
    if u.get("note"):
        parts.append(g("note"))
    return "\n".join(p.replace("।।", "।").replace("..", ".") for p in parts)


# ---------------- Sarvam voice ----------------
def stt(path):
    ext = os.path.splitext(path)[1].lower() or ".wav"
    with open(path, "rb") as f:
        r = requests.post(f"{SARVAM}/speech-to-text", headers={"api-subscription-key": SARVAM_KEY},
                          files={"file": ("audio" + ext, f, mimetypes.guess_type("a" + ext)[0] or "application/octet-stream")},
                          data={"model": STT_MODEL, "language_code": "unknown", "mode": "codemix", "keyterms": json.dumps(KEYTERMS)}, timeout=60)
    r.raise_for_status()
    j = r.json()
    return j.get("transcript", ""), (j.get("language_code") or "")


def voice_for(lang):
    return TTS_VOICE["en" if lang == "en" else "hi"] if TTS_MODEL.startswith("bulbul:v4") else TTS_VOICE["hi"]


def tts(text, lang, codec=None):
    """codec=None gives WAV. codec="opus" gives Ogg/Opus, which WhatsApp plays as a voice note."""
    body = {"text": text[:1400], "target_language_code": LANG_CODE.get(lang, "hi-IN"),
            "model": TTS_MODEL, "speaker": voice_for(lang), "speech_sample_rate": 16000, "enable_preprocessing": True}
    if codec:
        body["output_audio_codec"] = codec
    r = requests.post(f"{SARVAM}/text-to-speech",
                      headers={"api-subscription-key": SARVAM_KEY, "Content-Type": "application/json"},
                      json=body, timeout=60)
    r.raise_for_status()
    j = r.json()
    b64 = (j.get("audios") or j.get("audio"))[0]
    path = tempfile.NamedTemporaryFile(delete=False, suffix=".ogg" if codec == "opus" else f".{codec or 'wav'}").name
    with open(path, "wb") as f:
        f.write(base64.b64decode(b64))
    return path, b64
