"""Write hospital.json from the Tata Memorial Hospital patient booklet ("TMH_Brochure_ patient booklet.pdf").

Every location below is copied from the booklet: the Departments/Services Location Directory (sections 2 and 2.1),
the Kevat table (section 26), Dispensary locations (12.6), Other facilities (22), Useful extension numbers (27) and
the OPD, investigations, day-care and emergency sections. "src" on each unit names the booklet section.
The booklet gives buildings, floors and room numbers, not walking routes between buildings, so the walking path
only says: which building, which floor, which room, and to ask a Kevat or a security counter if lost.

Unit IDs are internal labels used by brain.py, core.py and server.py; they are kept stable so the code keeps working.
Run:  .venv/bin/python build_hospital_tmh.py
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))

BLOCKS = [
    {"id": "MB", "name": "Main Building (MB)", "name_hi": "मेन बिल्डिंग (MB)", "role": "Casualty, OT, ICU, palliative care"},
    {"id": "GJB", "name": "Golden Jubilee Building (GJB)", "name_hi": "गोल्डन जुबिली बिल्डिंग (GJB)", "role": "General OPDs, registration, dispensary"},
    {"id": "AB", "name": "Annexe Building (AB)", "name_hi": "एनेक्स बिल्डिंग (AB)", "role": "Laboratories, day-care, medical records"},
    {"id": "HBB", "name": "Homi Bhabha Building (HBB)", "name_hi": "होमी भाभा बिल्डिंग (HBB)", "role": "Private OPDs, Rotunda help desk, admissions"},
    {"id": "SB", "name": "Service Building (SB)", "name_hi": "सर्विस बिल्डिंग (SB)", "role": "Billing, blood bank, preventive oncology"},
]
FLOOR_NAMES = [("B", "Basement", "बेसमेंट"), ("G", "Ground floor", "ग्राउंड फ़्लोर"), ("1", "First floor", "पहली मंज़िल"),
               ("2", "Second floor", "दूसरी मंज़िल"), ("3", "Third floor", "तीसरी मंज़िल"), ("4", "Fourth floor", "चौथी मंज़िल"),
               ("5", "Fifth floor", "पाँचवीं मंज़िल"), ("6", "Sixth floor", "छठी मंज़िल"), ("7", "Seventh floor", "सातवीं मंज़िल"),
               ("8", "Eighth floor", "आठवीं मंज़िल")]
FLOORS = [{"id": i, "name": n, "name_hi": h} for i, n, h in FLOOR_NAMES]
FL = {i: (n, h) for i, n, h in FLOOR_NAMES}
BL = {b["id"]: b for b in BLOCKS}
ENQ = "Enquiry counter: GJB ground floor (General, ext. 4522) or HBB first floor (Private, ext. 7301)."
ENQ_HI = "इंक्वायरी काउंटर: GJB ग्राउंड फ़्लोर (जनरल, एक्सटेंशन 4522) या HBB पहली मंज़िल (प्राइवेट, एक्सटेंशन 7301)।"


def rooms_hi(r, name_hi=""):
    if r.startswith("the "):                              # a named place, not a room number: "the MRI room"
        return f"{name_hi} का साइनबोर्ड"
    return (r.replace("Rooms", "कमरा").replace("Room", "कमरा").replace("Counters", "काउंटर").replace("Counter", "काउंटर")
            .replace(" to ", " से ").replace(" and ", " और ").replace("Rotunda", "रोटुंडा"))


def path(block, floor, rooms, name_hi):
    b = BL[block]
    en = [f"Go to the {b['name']}."]
    hi = [f"{b['name_hi']} पहुँचिए।"]
    if floor == "B":
        en.append("Take the lift or stairs down to the basement.")
        hi.append("लिफ़्ट या सीढ़ी से बेसमेंट में नीचे जाइए।")
    elif floor != "G":
        en.append(f"Take the lift to the {FL[floor][0].lower()}.")
        hi.append(f"लिफ़्ट से {FL[floor][1]} पर जाइए।")
    en.append(f"Then look for {rooms[0].lower() + rooms[1:] if rooms.startswith(('Room', 'Counter')) else rooms}.")
    hi.append(f"फिर {rooms_hi(rooms, name_hi)} देखिए।")
    return " ".join(en), " ".join(hi)


def U(id, block, floor, cat, name, name_hi, rooms, src, hours=None, hours_hi=None, bring=None, bring_hi=None,
      note=None, note_hi=None, public=True):
    u = {"id": id, "block": block, "floor": floor, "cat": cat, "name": name, "name_hi": name_hi,
         "rooms": rooms, "rooms_hi": rooms_hi(rooms, name_hi), "src": src}
    for k, v in (("hours", hours), ("hours_hi", hours_hi), ("bring", bring), ("bring_hi", bring_hi),
                 ("note", note), ("note_hi", note_hi)):
        if v:
            u[k] = v
    if public:
        u["path"], u["path_hi"] = path(block, floor, rooms, name_hi)
    else:
        u["public"] = False
    return u


def C(id, cat, name, name_hi, note, note_hi, src):
    """A place without one fixed room in the booklet (spread over buildings, or the room is on the patient's slip)."""
    return {"id": id, "cat": cat, "name": name, "name_hi": name_hi, "note": note, "note_hi": note_hi, "src": src}


DMG_NOTE = "Your OPD room is printed on your appointment slip; the OPD is chosen by your cancer type (DMG)."
DMG_NOTE_HI = "आपका ओपीडी कमरा अपॉइंटमेंट पर्ची पर छपा होता है; ओपीडी आपके कैंसर के प्रकार (DMG) से तय होती है।"

UNITS = [
    # ---- arrival, registration, money (sections 2, 3.1, 3.2, 14, 22, 27)
    U("A-G-HELP", "HBB", "1", "support", "Help desk (Rotunda)", "हेल्प डेस्क (रोटुंडा)", "the Rotunda help desk", "2 #24",
      note="Run by NGOs: general information about the hospital. For wheelchairs, stretchers and lunch, call the Helpline (Annexe Building, ext. 7099). "
           "Wheelchair staff stand at the HBB, MB and GJB entrance gates, 7 am to 7 pm.",
      note_hi="एनजीओ चलाते हैं: अस्पताल की सामान्य जानकारी। व्हीलचेयर, स्ट्रेचर और खाने के लिए हेल्पलाइन (एनेक्स बिल्डिंग, एक्सटेंशन 7099)। "
              "HBB, MB और GJB के प्रवेश द्वार पर सुबह 7 से शाम 7 बजे तक व्हीलचेयर स्टाफ़ रहता है।"),
    U("A-G-REG", "GJB", "G", "support", "New patient registration (General)", "नए मरीज़ का रजिस्ट्रेशन (जनरल)", "the OPD registration counters", "3.1, 3.6",
      hours="New patients: 8 am to 11 am", hours_hi="नए मरीज़: सुबह 8 से 11 बजे तक",
      bring="referral letter (if any); Aadhaar or another government photo ID of the patient and the nominee; all previous reports, scans, "
            "pathology slides and blocks", bring_hi="डॉक्टर का रेफ़रल लेटर (अगर हो); मरीज़ और नॉमिनी का आधार या कोई सरकारी फ़ोटो पहचान पत्र; "
            "पुरानी सारी रिपोर्ट, स्कैन, पैथोलॉजी स्लाइड और ब्लॉक",
      note="Private category registers on HBB first floor. The patient must come in person; a token is given and you are called by number. "
           "To save time, register online first (tmc.gov.in, New Registration) and give the 13-digit WPRN at the counter. "
           "You get a Smart card and a case file. Fee: General Rs 100 + Rs 4,000 deposit; Private Rs 500 + Rs 20,000 deposit.",
      note_hi="प्राइवेट कैटेगरी का रजिस्ट्रेशन HBB पहली मंज़िल पर होता है। मरीज़ का ख़ुद आना ज़रूरी है; टोकन मिलता है और नंबर से बुलाते हैं। "
              "समय बचाने के लिए पहले ऑनलाइन रजिस्टर कीजिए (tmc.gov.in, New Registration) और काउंटर पर 13 अंकों का WPRN बताइए। "
              "स्मार्ट कार्ड और केस फ़ाइल मिलती है। फ़ीस: जनरल 100 रुपये + 4,000 जमा; प्राइवेट 500 रुपये + 20,000 जमा।"),
    U("A-G-BILL", "GJB", "G", "support", "Cash deposit counter (Smart card top-up)", "कैश डिपॉज़िट काउंटर (स्मार्ट कार्ड टॉप-अप)", "the cash deposit counter", "2 #9, 13",
      hours="General: 8 am to 4:30 pm", hours_hi="जनरल: सुबह 8 से शाम 4:30 बजे तक",
      note="TMH takes no cash at billing counters: top up your Smart card here, then pay with the card. Private patients: HBB first floor, "
           "8 am to 7 pm (Saturday 8 am to 1:30 pm). After hours, deposit at Casualty, MB ground floor. Card refunds and accounts: Service Building, first floor. "
           "Check your balance at any kiosk or on WhatsApp 9869451796.",
      note_hi="TMH में बिलिंग काउंटर पर नक़द नहीं लेते: यहाँ स्मार्ट कार्ड में पैसे डालिए, फिर कार्ड से भुगतान कीजिए। प्राइवेट मरीज़: HBB पहली मंज़िल, "
              "सुबह 8 से शाम 7 (शनिवार सुबह 8 से दोपहर 1:30)। समय के बाद कैज़ुअल्टी, MB ग्राउंड फ़्लोर पर जमा कीजिए। रिफ़ंड और अकाउंट्स: सर्विस बिल्डिंग, पहली मंज़िल। "
              "बैलेंस किसी भी कियोस्क पर या व्हाट्सऐप 9869451796 पर देखिए।"),
    U("NEW-CARD", "GJB", "G", "support", "New Smart card for old patients", "पुराने मरीज़ों के लिए नया स्मार्ट कार्ड", "the Smart card counter", "2 #37",
      note="Private patients: HBB first floor.", note_hi="प्राइवेट मरीज़: HBB पहली मंज़िल।"),
    U("A-G-PMJAY", "GJB", "G", "support", "Government schemes (Ayushman Bharat PM-JAY, MJPJAY)", "सरकारी योजनाएँ (आयुष्मान भारत PM-JAY, MJPJAY)",
      "the Medical Social Services department", "17, 2 #32",
      note="Enrol in the scheme before the online prescription is made and before admission (pre-authorisation). Also: Biju Swasthya Kalyan Yojana, ESIC, "
           "PM and CM relief funds.",
      note_hi="ऑनलाइन पर्ची बनने और भर्ती से पहले योजना में नाम दर्ज कराइए (प्री-ऑथराइज़ेशन)। बीजू स्वास्थ्य कल्याण योजना, ESIC, प्रधानमंत्री और मुख्यमंत्री राहत कोष भी।"),
    U("A-G-SW", "GJB", "G", "support", "Medical social workers & financial help", "मेडिकल सोशल वर्कर और आर्थिक मदद", "the Medical Social Services department", "17, 2 #32",
      note="Help with treatment costs, donors and government schemes.", note_hi="इलाज के ख़र्च, दानदाताओं और सरकारी योजनाओं में मदद।"),
    U("REIMB", "HBB", "1", "support", "Reimbursement & insurance (Mediclaim, LIC)", "रीइम्बर्समेंट और बीमा (मेडिक्लेम, LIC)", "the CRO reimbursement counter", "16, 27",
      note="Extension 6180.", note_hi="एक्सटेंशन 6180।"),
    U("CONCESSION", "HBB", "1", "support", "Travel concession letters (railway, bus, air)", "यात्रा रियायत पत्र (रेल, बस, हवाई)", "the concession letter counter", "19",
      hours="9:30 am to 5:30 pm", hours_hi="सुबह 9:30 से शाम 5:30 बजे तक",
      note="Also given on GJB ground floor.", note_hi="GJB ग्राउंड फ़्लोर पर भी मिलता है।"),
    U("ADMIT", "HBB", "1", "support", "Admissions desk", "भर्ती (एडमिशन) डेस्क", "the admissions desk", "7.1, 27",
      hours="9:30 am to 5:30 pm", hours_hi="सुबह 9:30 से शाम 5:30 बजे तक",
      bring="the doctor's written admission order", bring_hi="डॉक्टर का लिखित भर्ती आदेश",
      note="After hours, the Casualty admissions desk on MB ground floor (until 7 pm). Extension 6177.",
      note_hi="समय के बाद, MB ग्राउंड फ़्लोर पर कैज़ुअल्टी का एडमिशन डेस्क (शाम 7 बजे तक)। एक्सटेंशन 6177।"),
    U("A-G-CANT", "GJB", "G", "support", "Eatery & cafeteria", "कैंटीन / खाना", "the eatery", "22",
      hours="9:30 am to 5:30 pm", hours_hi="सुबह 9:30 से शाम 5:30 बजे तक",
      note="Also an eatery on HBB first floor, 8 am to 7 pm. Tea and coffee kiosks: HBB second floor, GJB ground floor, and MB ground floor (24x7). Paid service.",
      note_hi="HBB पहली मंज़िल पर भी कैंटीन है, सुबह 8 से शाम 7 बजे तक। चाय-कॉफ़ी कियोस्क: HBB दूसरी मंज़िल, GJB ग्राउंड फ़्लोर, और MB ग्राउंड फ़्लोर (24 घंटे)। पैसे लगते हैं।"),
    U("CLOAK", "GJB", "G", "support", "Cloak room (luggage storage)", "क्लॉक रूम (सामान रखने की जगह)", "the back-side gate", "22",
      hours="8 am to 5 pm", hours_hi="सुबह 8 से शाम 5 बजे तक",
      note="Free, for outstation patients' luggage during the OPD visit; daytime only, nothing overnight.",
      note_hi="मुफ़्त, बाहर से आए मरीज़ों का सामान ओपीडी के दौरान रखने के लिए; सिर्फ़ दिन में, रात भर नहीं।"),
    U("ATM", "HBB", "G", "support", "ATM (Central Bank of India)", "एटीएम (सेंट्रल बैंक ऑफ़ इंडिया)", "the ATM", "22",
      hours="24x7", hours_hi="चौबीसों घंटे", note="Also on HBB first floor and GJB ground floor. Central Bank branch: Annexe Building ground floor.",
      note_hi="HBB पहली मंज़िल और GJB ग्राउंड फ़्लोर पर भी। सेंट्रल बैंक की शाखा: एनेक्स बिल्डिंग ग्राउंड फ़्लोर।"),
    U("CORE-G-PHARM", "GJB", "G", "support", "Dispensary (pharmacy)", "डिस्पेंसरी (दवा की दुकान)", "Rooms 54 and 55", "12.6",
      hours="Mon–Fri 7 am to 10 pm; Sat 7 am to 7 pm; holidays 7 am to 5:30 pm",
      hours_hi="सोमवार से शुक्रवार सुबह 7 से रात 10; शनिवार सुबह 7 से शाम 7; छुट्टी के दिन सुबह 7 से शाम 5:30",
      bring="your Smart card with enough balance, and the online prescription", bring_hi="पर्याप्त बैलेंस वाला स्मार्ट कार्ड, और ऑनलाइन पर्ची",
      note="For General patients. The HBB ground-floor dispensary is open 24x7 for Private and General patients. Take a token at the kiosk with your "
           "Smart card, then go to the counter number shown on the screen.",
      note_hi="जनरल मरीज़ों के लिए। HBB ग्राउंड फ़्लोर की डिस्पेंसरी प्राइवेट और जनरल दोनों के लिए चौबीसों घंटे खुली है। कियोस्क पर स्मार्ट कार्ड से टोकन लीजिए, "
              "फिर स्क्रीन पर दिखे काउंटर नंबर पर जाइए।"),
    # ---- tests and scans (2, 6.2, 27)
    U("B-G-SAMPLE", "GJB", "1", "diagnostic", "Blood & sample collection", "ख़ून / सैंपल जाँच", "the sample collection area", "2 #6, #54",
      note="Private patients: HBB first floor. Reports of common blood tests come on WhatsApp and in the Web-EMR.",
      note_hi="प्राइवेट मरीज़: HBB पहली मंज़िल। आम ख़ून की जाँच की रिपोर्ट व्हाट्सऐप और वेब-EMR पर आती है।"),
    U("C-1-RADREC", "HBB", "1", "diagnostic", "Scan appointments (CT, MRI, PET, SPECT)", "स्कैन अपॉइंटमेंट (CT, MRI, PET, SPECT)", "Counters 129 to 131, Rotunda", "6.2",
      hours="8:30 am to 5:30 pm", hours_hi="सुबह 8:30 से शाम 5:30 बजे तक",
      bring="the scan requisition from your doctor and your Smart card", bring_hi="डॉक्टर की स्कैन वाली पर्ची और स्मार्ट कार्ड",
      note="Take a token at the Rotunda; counter 129 for CT, 130 for MRI, 131 for PET and SPECT. The charge is taken from your Smart card at the same counter.",
      note_hi="रोटुंडा पर टोकन लीजिए; CT के लिए काउंटर 129, MRI के लिए 130, PET और SPECT के लिए 131। पैसे उसी काउंटर पर स्मार्ट कार्ड से कटते हैं।"),
    U("C-1-CT", "MB", "B", "diagnostic", "CT scan", "सीटी स्कैन", "the CT scan room", "2 #11",
      note="There is also a CT scanner in the GJB basement; your appointment slip says which one. Book first at counter 129, Rotunda, HBB first floor.",
      note_hi="GJB बेसमेंट में भी सीटी स्कैन है; अपॉइंटमेंट पर्ची पर लिखा होता है कौन सा। पहले रोटुंडा, HBB पहली मंज़िल के काउंटर 129 पर बुक कीजिए।"),
    U("C-1-MRI", "GJB", "B", "diagnostic", "MRI scan", "एमआरआई स्कैन", "the MRI room", "2 #36",
      note="Private patients: MB basement. Book first at counter 130, Rotunda, HBB first floor. Remove all metal; tell the staff about any pacemaker or implant.",
      note_hi="प्राइवेट मरीज़: MB बेसमेंट। पहले रोटुंडा, HBB पहली मंज़िल के काउंटर 130 पर बुक कीजिए। सारा धातु का सामान उतारिए; पेसमेकर या इम्प्लांट हो तो स्टाफ़ को बताइए।"),
    U("C-G-XRAY", "GJB", "B", "diagnostic", "X-ray (general radiology)", "एक्स-रे (जनरल रेडियोलॉजी)", "the general radiology department", "2 #20",
      note="Private patients: MB ground floor.", note_hi="प्राइवेट मरीज़: MB ग्राउंड फ़्लोर।"),
    U("C-1-USG", "MB", "G", "diagnostic", "Mammography", "मैमोग्राफ़ी", "the mammography room", "2 #29",
      note="Private patients: HBB first floor.", note_hi="प्राइवेट मरीज़: HBB पहली मंज़िल।"),
    U("IR", "GJB", "B", "diagnostic", "Interventional radiology OPD", "इंटरवेंशनल रेडियोलॉजी ओपीडी", "Room 18", "2 #27, 26",
      hours="Mon–Fri 8 am to 5:30 pm", hours_hi="सोमवार से शुक्रवार सुबह 8 से शाम 5:30",
      note="Private patients: HBB third floor.", note_hi="प्राइवेट मरीज़: HBB तीसरी मंज़िल।"),
    U("B-3-CARDIO", "GJB", "7", "diagnostic", "ECG", "ईसीजी", "the ECG room", "2 #17",
      note="Private patients: HBB ground floor. 2D Echo: GJB basement (Private: MB first floor or HBB ground floor). Lung function test: MB first floor.",
      note_hi="प्राइवेट मरीज़: HBB ग्राउंड फ़्लोर। 2D इको: GJB बेसमेंट (प्राइवेट: MB पहली मंज़िल या HBB ग्राउंड फ़्लोर)। फेफड़ों की जाँच (PFT): MB पहली मंज़िल।"),
    U("ECHO", "GJB", "B", "diagnostic", "2D Echo", "2D इको", "the 2D Echo room", "2 #16",
      note="Private patients: MB first floor or HBB ground floor.", note_hi="प्राइवेट मरीज़: MB पहली मंज़िल या HBB ग्राउंड फ़्लोर।"),
    U("PFT", "MB", "1", "diagnostic", "Pulmonary function test (lung test)", "फेफड़ों की जाँच (PFT)", "the PFT room", "2 #48"),
    U("B-3-PAC", "GJB", "B", "diagnostic", "Pre-anaesthesia check-up (PAC)", "एनेस्थीसिया से पहले की जाँच (PAC)", "the PAC clinic", "2 #44",
      note="Private patients: HBB ground floor.", note_hi="प्राइवेट मरीज़: HBB ग्राउंड फ़्लोर।"),
    U("B-1-PATH", "AB", "8", "diagnostic", "Pathology", "पैथोलॉजी", "the Pathology department", "2 #42",
      note="Cytopathology and Clinical Biochemistry: AB fifth floor. Molecular pathology and Haematopathology: AB seventh floor. Microbiology: AB sixth floor.",
      note_hi="साइटोपैथोलॉजी और क्लिनिकल बायोकेमिस्ट्री: AB पाँचवीं मंज़िल। मॉलिक्यूलर पैथोलॉजी और हीमैटोपैथोलॉजी: AB सातवीं मंज़िल। माइक्रोबायोलॉजी: AB छठी मंज़िल।"),
    U("CYTO", "AB", "5", "diagnostic", "Cytopathology", "साइटोपैथोलॉजी", "the Cytopathology department", "2 #12"),
    U("BIOCHEM", "AB", "5", "diagnostic", "Clinical Biochemistry lab", "क्लिनिकल बायोकेमिस्ट्री लैब", "the Biochemistry lab", "2 #10"),
    U("MOLPATH", "AB", "7", "diagnostic", "Molecular pathology & Haematopathology lab", "मॉलिक्यूलर पैथोलॉजी और हीमैटोपैथोलॉजी लैब", "the lab", "2 #22, #35"),
    U("MICRO", "AB", "6", "diagnostic", "Microbiology", "माइक्रोबायोलॉजी", "the Microbiology department", "2 #33"),
    U("B-G-REPORT", "MB", "G", "diagnostic", "CT / MRI report enquiry", "सीटी / एमआरआई रिपोर्ट पूछताछ", "Room 62", "6.3, 27",
      hours="Helpline 24x7: 022 6953 7300, ext. 4299", hours_hi="हेल्पलाइन चौबीसों घंटे: 022 6953 7300, एक्सटेंशन 4299",
      note="TMH does not hand out printed reports: lab reports come on WhatsApp, and all reports are in the Web-EMR (Investigations, All Requisitions). "
           "The expected report time is printed on your billing memo.",
      note_hi="TMH छपी हुई रिपोर्ट नहीं देता: लैब रिपोर्ट व्हाट्सऐप पर आती है, और सारी रिपोर्ट वेब-EMR में (Investigations, All Requisitions)। "
              "रिपोर्ट कब मिलेगी, यह बिलिंग मेमो पर छपा होता है।"),
    U("MEDREC", "AB", "6", "support", "Medical records", "मेडिकल रिकॉर्ड", "the Medical Records department", "2 #30"),
    U("BLOODBANK", "SB", "5", "diagnostic", "Blood bank & transfusion medicine", "ब्लड बैंक / ट्रांसफ़्यूज़न मेडिसिन", "the Blood Centre", "2 #7, #61, 13",
      note="Blood donation: Service Building sixth floor. Also a blood bank on MB third floor.",
      note_hi="रक्तदान: सर्विस बिल्डिंग छठी मंज़िल। MB तीसरी मंज़िल पर भी ब्लड बैंक है।"),
    # ---- disease-wise OPDs, General category (2.1 table, Kevat table)
    U("A-3-BR", "GJB", "5", "opd", "Breast cancer OPD", "ब्रेस्ट (स्तन) कैंसर ओपीडी", "Rooms 508 to 510", "2.1, 26",
      hours="All days, 8 am to 7 pm", hours_hi="सभी दिन, सुबह 8 से शाम 7",
      note="Medical oncology 508, radiation oncology 509, surgical oncology 510. Private: HBB first floor, counters 109 and 112. Kevat: GJB 506.",
      note_hi="मेडिकल ऑन्कोलॉजी 508, रेडिएशन ऑन्कोलॉजी 509, सर्जिकल ऑन्कोलॉजी 510। प्राइवेट: HBB पहली मंज़िल, काउंटर 109 और 112। केवट: GJB 506।"),
    U("A-3-HN", "GJB", "1", "opd", "Head & Neck cancer OPD", "हेड एंड नेक (मुँह-गले) कैंसर ओपीडी", "Rooms 108A to 111", "2.1, 26",
      hours="8 am to 7 pm", hours_hi="सुबह 8 से शाम 7",
      note="Private: HBB second floor, counters 207 and 210. Kevat: GJB 107.", note_hi="प्राइवेट: HBB दूसरी मंज़िल, काउंटर 207 और 210। केवट: GJB 107।"),
    U("GI", "GJB", "1", "opd", "GI (stomach and gut) cancer OPD", "पेट / आँत (GI) कैंसर ओपीडी", "Rooms 120 to 124", "2.1, 26",
      hours="8 am to 7 pm", hours_hi="सुबह 8 से शाम 7",
      note="Private: HBB third floor, counters 312 and 314. Kevat: GJB 119.", note_hi="प्राइवेट: HBB तीसरी मंज़िल, काउंटर 312 और 314। केवट: GJB 119।"),
    U("A-3-GYN", "GJB", "5", "opd", "Gynaecologic & Uro cancer OPD", "स्त्री रोग (गायनेक) और यूरो कैंसर ओपीडी", "Rooms 502 to 504", "2.1, 26",
      hours="8 am to 7 pm", hours_hi="सुबह 8 से शाम 7",
      note="Private gynaecology: HBB ground floor, counter 61. Private uro: HBB second floor, counter 214. Kevat counselling: GJB 512.",
      note_hi="प्राइवेट गायनेक: HBB ग्राउंड फ़्लोर, काउंटर 61। प्राइवेट यूरो: HBB दूसरी मंज़िल, काउंटर 214। केवट काउंसलिंग: GJB 512।"),
    U("HEME", "GJB", "1", "opd", "Adult haematology (leukaemia, lymphoma, myeloma) OPD", "वयस्क हीमैटोलॉजी (ल्यूकेमिया, लिम्फ़ोमा, मायलोमा) ओपीडी", "Rooms 140 to 142", "2.1, 26",
      note="Acute leukaemia 140, lymphoma 141, CML and myeloma 142. Private: MB ground floor, counter 81.",
      note_hi="एक्यूट ल्यूकेमिया 140, लिम्फ़ोमा 141, CML और मायलोमा 142। प्राइवेट: MB ग्राउंड फ़्लोर, काउंटर 81।"),
    U("BST", "GJB", "G", "opd", "Bone, soft tissue & thoracic (lung) cancer OPD", "हड्डी, सॉफ़्ट टिशू और थोरेसिक (फेफड़े) कैंसर ओपीडी", "Rooms 65 to 69", "2.1, 26",
      hours="8 am to 7 pm", hours_hi="सुबह 8 से शाम 7",
      note="Private thoracic: HBB third floor, counters 307 and 310. Private bone and soft tissue: MB ground floor, counter 93.",
      note_hi="प्राइवेट थोरेसिक: HBB तीसरी मंज़िल, काउंटर 307 और 310। प्राइवेट हड्डी और सॉफ़्ट टिशू: MB ग्राउंड फ़्लोर, काउंटर 93।"),
    U("A-2-PEDS", "MB", "G", "opd", "Paediatric (children's) cancer OPD", "बच्चों का कैंसर ओपीडी", "Counters 80 and 88", "2.1",
      note="Solid tumours: counter 80. Blood cancers and lymphoma: counter 88.", note_hi="सॉलिड ट्यूमर: काउंटर 80। ख़ून का कैंसर और लिम्फ़ोमा: काउंटर 88।"),
    U("NEURO", "HBB", "G", "opd", "Neuro-oncology (brain tumour) OPD", "न्यूरो-ऑन्कोलॉजी (ब्रेन ट्यूमर) ओपीडी", "Counter 58", "2.1"),
    U("DENTAL", "GJB", "1", "opd", "Dental department", "डेंटल (दाँत) विभाग", "Room 130", "2 #15, 2.1",
      note="Private: HBB second floor, counter 212.", note_hi="प्राइवेट: HBB दूसरी मंज़िल, काउंटर 212।"),
    U("A-4-TOB", "SB", "3", "opd", "Preventive oncology (cancer screening)", "प्रिवेंटिव ऑन्कोलॉजी (कैंसर स्क्रीनिंग)", "the Preventive Oncology department", "5, 2 #45"),
    # ---- treatment and support (2, 8.2, 10, 26)
    U("A-2-DC", "AB", "6", "treatment", "Chemotherapy Day-care", "कीमोथेरेपी डे-केयर", "the Day-care unit", "2 #13, 8.2",
      hours="Open 24x7 by appointment", hours_hi="अपॉइंटमेंट से, चौबीसों घंटे",
      bring="your appointment slip or confirmation message (shown at the entrance gate)", bring_hi="अपॉइंटमेंट पर्ची या कन्फ़र्मेशन मैसेज (प्रवेश द्वार पर दिखाना होता है)",
      note="Private: HBB fifth floor. Book at the Day-care appointment counter, or by WhatsApp message (no calls): 9869451766 General, 9869451802 Private. "
           "The token is given 1 hour before your time; please don't come more than 1 hour early.",
      note_hi="प्राइवेट: HBB पाँचवीं मंज़िल। डे-केयर अपॉइंटमेंट काउंटर पर बुक कीजिए, या व्हाट्सऐप मैसेज से (कॉल नहीं): जनरल 9869451766, प्राइवेट 9869451802। "
              "टोकन समय से 1 घंटा पहले मिलता है; 1 घंटे से ज़्यादा पहले मत आइए।"),
    U("D-G-RT", "AB", "B", "treatment", "Radiotherapy (radiation treatment)", "रेडियोथेरेपी (सिकाई)", "the Radiotherapy department", "2 #52, 10",
      note="Radiotherapy machines are in the basements of AB, MB and HBB; your treatment schedule says which. Your radiation oncology doctor plans the treatment first.",
      note_hi="रेडियोथेरेपी मशीनें AB, MB और HBB के बेसमेंट में हैं; आपके ट्रीटमेंट शेड्यूल पर लिखा होता है कौन सी। पहले रेडिएशन ऑन्कोलॉजी के डॉक्टर इलाज की योजना बनाते हैं।"),
    U("A-4-PALL", "MB", "G", "treatment", "Palliative care", "पैलिएटिव केयर (आराम देने वाली देखभाल)", "Room 75", "2 #41, 26",
      hours="9 am to 5:30 pm", hours_hi="सुबह 9 से शाम 5:30",
      note="Pain clinic: GJB basement (Private: HBB ground floor).", note_hi="पेन क्लिनिक: GJB बेसमेंट (प्राइवेट: HBB ग्राउंड फ़्लोर)।"),
    U("PAIN", "GJB", "B", "treatment", "Pain clinic", "पेन (दर्द) क्लिनिक", "the Pain clinic", "2 #40",
      note="Private patients: HBB ground floor.", note_hi="प्राइवेट मरीज़: HBB ग्राउंड फ़्लोर।"),
    U("A-4-NUT", "GJB", "1", "support", "Nutrition clinic", "न्यूट्रिशन (खान-पान) क्लिनिक", "the Nutrition clinic", "2 #38",
      note="Private patients: HBB third floor.", note_hi="प्राइवेट मरीज़: HBB तीसरी मंज़िल।"),
    U("A-4-PSY", "GJB", "7", "support", "Psychiatry department", "मनोरोग (साइकियाट्री) विभाग", "the Psychiatry department", "2 #46",
      note="For counselling and hand-holding, meet a Kevat (patient navigator, green coat): counselling rooms GJB 512, HBB 138 and HBB 226; Kevat office 022 2147 7296.",
      note_hi="काउंसलिंग और साथ के लिए केवट (पेशेंट नेविगेटर, हरा कोट) से मिलिए: काउंसलिंग रूम GJB 512, HBB 138 और HBB 226; केवट ऑफ़िस 022 2147 7296।"),
    U("KEVAT", "GJB", "5", "support", "Kevat (patient navigator) counselling room", "केवट (पेशेंट नेविगेटर) काउंसलिंग रूम", "Room 512", "26",
      note="Kevats wear green coats. Other counselling rooms: HBB 138 (breast, private) and HBB 226 (head and neck, private). Kevat office: 022 2147 7296.",
      note_hi="केवट हरे कोट में होते हैं। दूसरे काउंसलिंग रूम: HBB 138 (ब्रेस्ट, प्राइवेट) और HBB 226 (हेड एंड नेक, प्राइवेट)। केवट ऑफ़िस: 022 2147 7296।"),
    U("PHYSIO", "MB", "G", "treatment", "Physiotherapy & occupational therapy", "फ़िज़ियोथेरेपी और ऑक्यूपेशनल थेरेपी", "the Physiotherapy department", "2 #39, #43"),
    U("SPEECH", "GJB", "B", "treatment", "Speech therapy", "स्पीच थेरेपी", "the Speech therapy room", "2 #56"),
    U("STOMA", "HBB", "3", "treatment", "Stoma clinic", "स्टोमा क्लिनिक", "the Stoma clinic", "2 #58"),
    U("MEDICINE", "GJB", "7", "opd", "General medicine / physician", "जनरल मेडिसिन / फ़िज़िशियन", "the General Medicine OPD", "2 #21",
      note="Private patients: MB first floor.", note_hi="प्राइवेट मरीज़: MB पहली मंज़िल।"),
    U("TELECONSULT", "GJB", "G", "support", "Teleconsultation enquiry", "टेलीकंसल्टेशन पूछताछ", "the Teleconsultation desk", "3.4, 2 #59",
      note="Book by phone 022 2417 7337, WhatsApp 9321470561 or teleconsult@tmc.gov.in.",
      note_hi="फ़ोन 022 2417 7337, व्हाट्सऐप 9321470561 या teleconsult@tmc.gov.in पर बुक कीजिए।"),
    # ---- emergency, OT, wards, admin
    U("D-G-ER", "MB", "G", "emergency", "Casualty (Emergency)", "कैज़ुअल्टी (इमरजेंसी)", "the Casualty department", "23, 27",
      hours="24x7", hours_hi="चौबीसों घंटे",
      note="Board line 022 2417 7000; Casualty extension 4116 or 4117; cardiac emergency extension 11. If you live far away, go to the nearest hospital first.",
      note_hi="बोर्ड नंबर 022 2417 7000; कैज़ुअल्टी एक्सटेंशन 4116 या 4117; दिल की इमरजेंसी एक्सटेंशन 11। दूर रहते हों तो पहले पास के अस्पताल जाइए।"),
    U("D-1-OT", "MB", "2", "ward", "Main operation theatre", "मुख्य ऑपरेशन थिएटर", "the OT complex", "2 #28", public=False),
    U("D-2-ICU", "MB", "1", "ward", "ICU", "आईसीयू", "the ICU", "2 #25",
      note="ICU is on MB first and second floors. Visitors for admitted patients: 4 pm to 7 pm.",
      note_hi="आईसीयू MB की पहली और दूसरी मंज़िल पर है। भर्ती मरीज़ से मिलने का समय: शाम 4 से 7 बजे।"),
    U("D-4-ADMIN", "HBB", "1", "support", "Medical Superintendent's office", "मेडिकल सुपरिंटेंडेंट ऑफ़िस", "the Medical Superintendent's office", "2 #31",
      note="Administration office: Service Building fourth floor. Public Relations Officer: HBB first floor (ext. 6168).",
      note_hi="प्रशासन ऑफ़िस: सर्विस बिल्डिंग चौथी मंज़िल। जनसंपर्क अधिकारी: HBB पहली मंज़िल (एक्सटेंशन 6168)।"),
    U("ENQUIRY", "GJB", "G", "support", "Enquiry counter (General)", "इंक्वायरी काउंटर (जनरल)", "the Enquiry counter", "27",
      note="Extension 4522. Private enquiry: HBB first floor, extension 7301.", note_hi="एक्सटेंशन 4522। प्राइवेट इंक्वायरी: HBB पहली मंज़िल, एक्सटेंशन 7301।"),
]

CAMPUS = [
    C("A-1-MED", "opd", "OPD (your disease clinic)", "ओपीडी (आपकी बीमारी का क्लिनिक)",
      "At TMH each cancer type has its own OPD (DMG). General OPDs are mostly in the Golden Jubilee Building, private ones in the Homi Bhabha Building. "
      "Your room is on your appointment slip; tell me your cancer type and I'll tell you the room.",
      "TMH में हर कैंसर की अपनी ओपीडी (DMG) होती है। जनरल ओपीडी ज़्यादातर गोल्डन जुबिली बिल्डिंग में हैं, प्राइवेट होमी भाभा बिल्डिंग में। "
      "आपका कमरा अपॉइंटमेंट पर्ची पर होता है; अपने कैंसर का प्रकार बताइए, मैं कमरा बता दूँगी।", "2.1, 3"),
    C("A-1-SURG", "opd", "Surgical oncology OPD", "सर्जिकल ऑन्कोलॉजी ओपीडी",
      "Surgical oncology sits inside each disease OPD (DMG), next to medical and radiation oncology. Tell me your cancer type and I'll tell you the room.",
      "सर्जिकल ऑन्कोलॉजी हर बीमारी की ओपीडी (DMG) के अंदर होती है। अपने कैंसर का प्रकार बताइए, मैं कमरा बता दूँगी।", "2.1"),
    C("A-1-RTC", "opd", "Radiation oncology OPD", "रेडिएशन ऑन्कोलॉजी ओपीडी",
      "Radiation oncology doctors sit inside each disease OPD (DMG). Tell me your cancer type and I'll tell you the room.",
      "रेडिएशन ऑन्कोलॉजी के डॉक्टर हर बीमारी की ओपीडी (DMG) के अंदर बैठते हैं। अपने कैंसर का प्रकार बताइए, मैं कमरा बता दूँगी।", "2.1"),
    C("B-2-ENDO", "diagnostic", "Endoscopy", "एंडोस्कोपी",
      "The booklet doesn't list the endoscopy room. Your doctor's requisition or appointment slip will say where; or ask the " + ENQ,
      "बुकलेट में एंडोस्कोपी का कमरा नहीं दिया है। डॉक्टर की पर्ची या अपॉइंटमेंट पर्ची पर लिखा होगा; या " + ENQ_HI, "—"),
    C("C-2-PET", "diagnostic", "PET-CT & SPECT", "पेट-सीटी और स्पेक्ट स्कैन",
      "Book at counter 131, Rotunda, Homi Bhabha Building first floor (8:30 am to 5:30 pm). The scan room is printed on your appointment slip.",
      "होमी भाभा बिल्डिंग पहली मंज़िल के रोटुंडा पर काउंटर 131 में बुक कीजिए (सुबह 8:30 से शाम 5:30)। स्कैन का कमरा अपॉइंटमेंट पर्ची पर छपा होता है।", "6.2"),
    C("D-1-OTWAIT", "support", "Family waiting during surgery", "ऑपरेशन के समय परिवार के रुकने की जगह",
      "The main OT is on the Main Building second floor (Private: HBB fourth floor). Please ask the ward nurse or the OT reception where the family should wait.",
      "मुख्य ऑपरेशन थिएटर मेन बिल्डिंग की दूसरी मंज़िल पर है (प्राइवेट: HBB चौथी मंज़िल)। परिवार कहाँ रुके, यह वार्ड की नर्स या ओटी रिसेप्शन से पूछिए।", "2 #28"),
    C("HELPLINE", "support", "Helpline (wheelchair, stretcher, lunch)", "हेल्पलाइन (व्हीलचेयर, स्ट्रेचर, खाना)",
      "Wheelchair staff stand at the HBB, MB and GJB entrance gates, 7 am to 7 pm. Helpline: Annexe Building premises, extension 7099 "
      "(from outside call 022 2417 7000 and dial 7099).",
      "HBB, MB और GJB के प्रवेश द्वार पर सुबह 7 से शाम 7 बजे तक व्हीलचेयर स्टाफ़ रहता है। हेल्पलाइन: एनेक्स बिल्डिंग परिसर, एक्सटेंशन 7099 "
      "(बाहर से 022 2417 7000 पर कॉल करके 7099 डायल कीजिए)।", "22, 2 #23, 27"),
    C("SECURITY", "support", "Security counters", "सिक्योरिटी काउंटर",
      "On the ground floor of AB, MB, SB and HBB. They can point you to any building.",
      "AB, MB, SB और HBB के ग्राउंड फ़्लोर पर। ये किसी भी बिल्डिंग का रास्ता बता देंगे।", "2 #55"),
    C("CHARGING", "support", "Mobile charging", "मोबाइल चार्जिंग",
      "Charging points in all OPD waiting areas, 24x7. Please keep your phone with you.",
      "सभी ओपीडी वेटिंग एरिया में चार्जिंग पॉइंट, चौबीसों घंटे। फ़ोन अपने पास रखिए।", "22"),
]

out = {
    "name": "Tata Memorial Hospital, Parel",
    "name_hi": "टाटा मेमोरियल हॉस्पिटल, परेल",
    "city": "Mumbai",
    "source": "Tata Memorial Hospital patient booklet (TMH_Brochure_ patient booklet.pdf): sections 2, 2.1, 3, 6, 8, 12, 17, 19, 22, 23, 26, 27.",
    "disclaimer": "Locations are from the Tata Memorial Hospital patient booklet. Rooms can change; if something doesn't match, ask the " + ENQ,
    "enquiry": ENQ, "enquiry_hi": ENQ_HI,
    "categories": {"opd": {"label": "OPD / consultation", "label_hi": "ओपीडी / डॉक्टर से परामर्श"},
                   "diagnostic": {"label": "Tests & diagnostics", "label_hi": "जाँच"},
                   "treatment": {"label": "Treatment", "label_hi": "इलाज"},
                   "emergency": {"label": "Emergency", "label_hi": "इमरजेंसी"},
                   "support": {"label": "Patient services", "label_hi": "मरीज़ सेवाएँ"},
                   "ward": {"label": "Wards & restricted", "label_hi": "वार्ड / सीमित प्रवेश"}},
    "blocks": [dict(b, floors=sorted({u["floor"] for u in UNITS if u["block"] == b["id"]}, key=[f[0] for f in FLOOR_NAMES].index),
                    role_hi=b["role"]) for b in BLOCKS],
    "floors": FLOORS,
    "lifts": [],
    "campus": CAMPUS,
    "units": UNITS,
}
ids = [u["id"] for u in UNITS + CAMPUS]
assert len(ids) == len(set(ids)), "duplicate id"
json.dump(out, open(os.path.join(HERE, "hospital.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(f"hospital.json: {len(UNITS)} rooms in {len(BLOCKS)} buildings, {len(CAMPUS)} general places")
