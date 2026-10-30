import re

with open("vega/SoftPowerPlay.reg", "r", encoding="utf-8") as f:
    content = f.read()

match = re.search(r'"PP_PhmSoftPowerPlayTable"=hex:(.+)', content, re.DOTALL)
if match:
    raw_hex = match.group(1)
    clean_hex = raw_hex.replace("\\", "").replace("\n", "").replace("\r", "").replace(" ", "").replace(",", "")
    clean_hex = re.match(r"^([0-9a-fA-F]+)", clean_hex).group(1)
    print("Extracted bytes count:", len(clean_hex) // 2)
    with open("vega/user_test.pp_table", "wb") as out:
        out.write(bytes.fromhex(clean_hex))
else:
    print("No match found!")
