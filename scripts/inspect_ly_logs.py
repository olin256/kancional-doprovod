from glob import iglob
from fname_utils import purify

voice_names = ["soprano", "alto", "tenor", "bass"]

for fname in iglob("../log_ly/*.log"):
    pname = purify(fname)
    print(pname)
    with open(f"../musicxml/{pname}.xml", "r", encoding="utf-8") as f:
        xml_content = f.read()
    with open(f"../ly/{pname}_0.ly", "r", encoding="utf-8") as f:
        ly_content = [l.strip() for l in f]
    if "<chord" in xml_content:
        print("    chord!")
    shown_errors = set()
    with open(fname, "r", encoding="utf-8") as f:
        for i, l in enumerate((ll.strip().lower() for ll in f), 1):
            if (("chyba" in l) or ("varov" in l)) and (l not in shown_errors):
                error_line_no = int(l.split(":", 2)[1])
                source_portion = ly_content[:error_line_no]
                source_portion_str = "\n".join(source_portion)
                for v in voice_names:
                    source_parts = source_portion_str.split(v + " = ", 1)
                    if len(source_parts) == 1:
                        break
                    source_portion_str = source_parts[1]
                    voice = v
                measure_no = source_portion_str.count("|")
                print(f"    {i}: {voice} {measure_no} {l}")
                print(" "*8 + source_portion[-1])
                shown_errors.add(l)