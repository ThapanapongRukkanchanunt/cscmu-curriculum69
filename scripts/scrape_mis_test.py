import urllib.request, ssl, re

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

def test_mis_course(courseno):
    url = f'https://www.mis.cmu.ac.th/TQF/coursepublic.aspx?courseno={courseno}&semester=2&year=2569'
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=10) as resp:
            html = resp.read().decode('utf-8', errors='ignore')
            # Look for Prerequisite label or span
            # Let's find spans
            spans = dict(re.findall(r'<span id="([^"]+)"[^>]*>(.*?)</span>', html, re.DOTALL))
            print(f"--- {courseno} ---")
            for k, v in spans.items():
                v_clean = re.sub(r'<[^>]+>', '', v).strip()
                if 'prereq' in k.lower() or 'cond' in k.lower() or 'desc' in k.lower() or 'pre' in k.lower() or 'detail' in k.lower():
                    print(f"  {k}: {v_clean[:120]}")
            # Also search for เงื่อนไข or Prerequisite in the raw html
            m = re.search(r'(เงื่อนไขที่ต้องผ่านก่อน|Prerequisite|PREREQ)[^<]*</td>\s*<td[^>]*>(.*?)</td>', html, re.DOTALL | re.IGNORECASE)
            if m:
                print("  Matched TD Prereq:", re.sub(r'<[^>]+>', '', m.group(2)).strip())
    except Exception as e:
        print(f"Error {courseno}: {e}")

test_mis_course('204212')
test_mis_course('204321')
test_mis_course('204451')
