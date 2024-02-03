from glob import iglob
from fname_utils import purify

for fname in iglob("../log_ly/*.log"):
    pname = purify(fname)
    print(pname)
    with open(f"../musicxml/{pname}.xml", "r", encoding="utf-8") as f:
        xml_content = f.read()
    if "<chord" in xml_content:
        print("    chord!")
    with open(fname, "r", encoding="utf-8") as f:
        for i, l in enumerate((ll.strip().lower() for ll in f), 1):
            if ("chyba" in l) or ("varov") in l:
                print(f"    {i}: {l}")