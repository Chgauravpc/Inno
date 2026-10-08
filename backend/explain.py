"""Plain-language explainer. Grounded only in the user's computed numbers and the tax rules file.
Rule-based retrieval today; the same grounded context can be passed to an LLM later."""
from __future__ import annotations

from . import llm
from .fmt import inr
from .engine import analyse, class_real_return
from .tax_rules import RULES




INTENTS = [
    ("slab", ["slab", "bond", " fd", "best", "स्लैब", "स्लॅब"]),
    ("ltcg", ["ltcg", "capital gain", "stcg", "tax", "कर", "टॅक्स", "टैक्स"]),
    ("reit", ["reit", "invit", "rent", "toll", "रीट"]),
    ("twin", ["twin", "risk", "diversif", "concentr", "जोखिम", "जोखीम"]),
    ("inflation", ["inflation", "महंगाई", "महागाई"]),
    ("why", ["why", "lower", "less", "overstat", "real", "क्यों", "कम", "का"]),
]

TEXT = {
    "en": {
        "why": "Apps show market value only. For you that is {mv}. If you sold everything today you would pay {tax} tax and {costs} in charges, leaving {after}. Adjusted for {infl}% yearly inflation over your holding periods, that is {real} in real terms.",
        "ltcg": "Gains on shares, REIT and InvIT units held 12 months or more are taxed at {ltcg}% (above ₹1.25 lakh a year). Under 12 months it is 20%. Add 4% cess. Your estimated tax today is {tax}.",
        "reit": "REITs own offices and malls, InvITs own roads and power lines. They pay out rent or toll income, taxed at your slab. Your REIT and InvIT units earn you about {income} a year after tax.",
        "twin": "Your largest holding is {top} at {toppct}% of the portfolio and stocks are {eq}%. The Twin moves a part into REITs, InvITs and bonds and compares both in real terms. Open the Twin tab to see it.",
        "inflation": "Inflation makes the same rupee buy less. We divide your after-tax value by {infl}% a year for how long you held each lot, so {after} becomes {real}.",
        "slab": "The best asset depends on your tax slab. At your {slab}% slab, a 7.5% bond earns about {bond:.1f}% real a year and Nifty 50 stocks about {eqr:.1f}%. See the Slab tab.",
        "fallback": "I can explain why your real value is lower, how LTCG tax works, what REITs and InvITs are, inflation, your slab, and the Twin. Try one of those questions.",
    },
    "hi": {
        "why": "ऐप सिर्फ बाज़ार मूल्य दिखाते हैं, आपके लिए {mv}। आज सब बेचें तो {tax} टैक्स और {costs} शुल्क देने के बाद {after} बचेगा। {infl}% सालाना महंगाई जोड़ें तो असली मूल्य {real} है।",
        "ltcg": "12 महीने या ज़्यादा रखे शेयर, REIT और InvIT के लाभ पर {ltcg}% टैक्स लगता है (साल के ₹1.25 लाख के बाद)। 12 महीने से कम पर 20%। साथ में 4% सेस। आपका अनुमानित टैक्स {tax} है।",
        "reit": "REIT दफ़्तर और मॉल के मालिक होते हैं, InvIT सड़क और बिजली लाइन के। ये किराया या टोल आय देते हैं, जिस पर आपके स्लैब से टैक्स लगता है। आपको टैक्स के बाद सालाना करीब {income} मिलते हैं।",
        "twin": "आपका सबसे बड़ा निवेश {top} है, पोर्टफोलियो का {toppct}%, और शेयर {eq}% हैं। ट्विन कुछ हिस्सा REIT, InvIT और बॉन्ड में ले जाकर दोनों की असली तुलना दिखाता है।",
        "inflation": "महंगाई से वही रुपया कम खरीदता है। हम टैक्स के बाद का मूल्य हर लॉट की अवधि के लिए {infl}% सालाना से भाग देते हैं, इसलिए {after} का असली मूल्य {real} हुआ।",
        "slab": "सबसे अच्छा निवेश आपके टैक्स स्लैब पर निर्भर है। आपके {slab}% स्लैब पर 7.5% बॉन्ड का असली रिटर्न करीब {bond:.1f}% और निफ्टी 50 का करीब {eqr:.1f}% है।",
        "fallback": "मैं बता सकता हूँ कि असली मूल्य कम क्यों है, LTCG, REIT/InvIT, महंगाई, स्लैब और ट्विन क्या हैं। इनमें से कोई सवाल पूछें।",
    },
    "mr": {
        "why": "अ‍ॅप्स फक्त बाजारमूल्य दाखवतात, तुमच्यासाठी {mv}. आज सर्व विकल्यास {tax} कर आणि {costs} शुल्क जाऊन {after} उरेल. {infl}% वार्षिक महागाई धरल्यास खरे मूल्य {real} आहे.",
        "ltcg": "12 महिने किंवा जास्त ठेवलेल्या शेअर, REIT आणि InvIT च्या नफ्यावर {ltcg}% कर लागतो (वर्षाच्या ₹1.25 लाखांनंतर). 12 महिन्यांपेक्षा कमी असल्यास 20%. शिवाय 4% सेस. तुमचा अंदाजे कर {tax} आहे.",
        "reit": "REIT कार्यालये आणि मॉलचे मालक असतात, InvIT रस्ते आणि वीजवाहिन्यांचे. ते भाडे किंवा टोल उत्पन्न देतात, ज्यावर तुमच्या स्लॅबनुसार कर लागतो. करानंतर वार्षिक सुमारे {income} मिळतात.",
        "twin": "तुमची सर्वात मोठी गुंतवणूक {top} आहे, पोर्टफोलिओच्या {toppct}%, आणि शेअर्स {eq}% आहेत. ट्विन काही भाग REIT, InvIT आणि बॉण्डमध्ये नेऊन दोन्हींची खरी तुलना दाखवतो.",
        "inflation": "महागाईमुळे तोच रुपया कमी खरेदी करतो. आम्ही करानंतरचे मूल्य प्रत्येक लॉटच्या कालावधीसाठी {infl}% वार्षिकने भागतो, म्हणून {after} चे खरे मूल्य {real} आहे.",
        "slab": "सर्वोत्तम मालमत्ता तुमच्या कर स्लॅबवर अवलंबून असते. तुमच्या {slab}% स्लॅबवर 7.5% बॉण्डचा खरा परतावा सुमारे {bond:.1f}% आणि निफ्टी 50 चा सुमारे {eqr:.1f}% आहे.",
        "fallback": "खरे मूल्य कमी का, LTCG, REIT/InvIT, महागाई, स्लॅब आणि ट्विन याबद्दल मी सांगू शकतो. यापैकी एखादा प्रश्न विचारा.",
    },
}


def rules_answer(question: str, lang: str = "en", slab: float = 30, inflation: float = 5.0) -> dict:
    lang = lang if lang in TEXT else "en"
    q = " " + question.lower()
    intent = "fallback"
    for name, keys in INTENTS:
        if any(k in q for k in keys):
            intent = name
            break
    a = analyse(slab, inflation)
    t = a["totals"]
    inc_assets = sum(h["annual_income_net"] for h in a["holdings"] if h["type"] in ("REIT", "INVIT"))
    top = max(a["holdings"], key=lambda h: h["weight_pct"])
    text = TEXT[lang][intent].format(
        mv=inr(t["app_value"]), tax=inr(t["tax"]), costs=inr(t["costs"]), after=inr(t["after_tax"]),
        real=inr(t["real_value"]), infl=f"{inflation:g}", ltcg=f"{RULES['ltcg_rate'] * 100:g}",
        income=inr(inc_assets), top=top["name"], toppct=f"{top['weight_pct']:.0f}",
        eq=f"{a['stats']['equity_pct']:.0f}", slab=f"{slab:g}",
        bond=class_real_return("gsec", slab, 5, inflation)["real_return"] * 100,
        eqr=class_real_return("nifty50", slab, 5, inflation)["real_return"] * 100)
    return dict(intent=intent, lang=lang, answer=text,
                sources=[RULES["version"], "Your demo portfolio (sandbox AA fetch)"],
                disclaimer="Education only, not investment advice.")


def answer(question: str, lang: str = "en", slab: float = 30, inflation: float = 5.0, history=None) -> dict:
    """LLM answer via OpenRouter when a key is configured; otherwise (or on any failure) the rule-based answer."""
    base = rules_answer(question, lang, slab, inflation)
    base["engine"] = "rules"
    if not llm.enabled():
        return base
    try:
        text = llm.answer(question, base["lang"], slab, inflation, history)
        return dict(base, answer=text, engine="llm", model=llm.model())
    except Exception as e:  # network, quota, bad key, empty reply: never leave the user without an answer
        return dict(base, note=f"LLM unavailable ({type(e).__name__}); showing the built-in answer.")
