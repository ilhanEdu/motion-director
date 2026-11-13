#!/usr/bin/env python3
"""English vs Roman-Hindi word share of a script's teleprompter (the `>` lines).
Usage: python3 langmix.py SCRIPT.md [terms.txt]   (or pipe text in; terms.txt = your own product names, not counted)
ponytail: wordlist heuristic, not a language model; good to about +-5%. Add words to HI as they show up."""
import re, sys

# Words that are also common English (is, do, the, to, us, hi, ha, na) are left out on purpose.
HI = set("""
toh pe par ab aap aapko aapka aapke aapki main mein maine mera meri mere hum hamari hamara hamare humne
ye yeh wo woh vo iss uss inka unka koi kuch sab
hai hain tha thi ho hoga hogi hoge hua hui hue raha rahi rahe hoon hu
nahi nahin mat haan ji bhai yaar arre
aur ya lekin magar kyunki isliye matlab jaise waise bas sirf bhi phir fir pehle baad abhi
ka ke ki ko se tak liye wala wale wali
kya kyu kyun kaise kab kahan kitna kitne kitni kaun
lagega lagta lage laga bolte bole bola bolo bolna kehte kehna kahe kaha keh kahunga
kar karo kariye kijiye karna karta karte karti kiya kiye ki dekhiye dekho poochiye poochna poocho
sakte sakta sakti milenge milega mila mili milta chalega chalta chal chala dikh dikhti dikhta jaati jaata jaate
daaliye daalo banaya banaye
khud asli sawaal baat baatein cheez cheezein ek teen chhoti bada badi zyada kam
hafte hafta din saal raay baaki agli agla baar
""".split())

# Names and crypto terms stay English in any script, so they are not counted either way.
TERMS = set("""
usdt million volume tickets ticket wallet leaderboard pool prize mega super preset
margin bot code docs formula fee zero solely trading activity battle return top epoch draw
""".split())

def mix(text):
    words = [w for w in re.findall(r"[A-Za-z']+", text) if w.lower() not in TERMS and not w.isupper()]
    hi = [w for w in words if w.lower() in HI]
    n = len(words)
    return n, len(hi), n - len(hi)

if __name__ == "__main__":
    if len(sys.argv) > 2: TERMS |= set(open(sys.argv[2]).read().lower().split())
    src = open(sys.argv[1]).read() if len(sys.argv) > 1 else sys.stdin.read()
    lines = [l[1:] for l in src.splitlines() if l.startswith(">")]
    text = "\n".join(lines) if lines else src
    text = re.sub(r"\*\*\d+\.\*\*", "", text)
    n, hi, en = mix(text)
    assert mix("Ab aapko lagega more volume")[1:] == (3, 1), "self-check failed"
    print(f"everyday words {n} (names and crypto terms not counted) | English {en} ({en*100//max(n,1)}%) | Hindi {hi} ({hi*100//max(n,1)}%)")
