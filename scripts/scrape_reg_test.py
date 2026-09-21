import urllib.request, urllib.parse, ssl, re, json

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

def get_reg_courses(term):
    # term is '1/2569' or '2/2569'
    url = f'https://www1.reg.cmu.ac.th/registrationoffice/searchcourse.php?tterm={term}#showrecord'
    # Try searching 2041xx, 2042xx, 2043xx, 2044xx or fgroup=204
    # Note: searching fgroup='204' with button='Search'
    data = urllib.parse.urlencode({'fgroup': '204', 'button': 'Search'}).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=15) as resp:
            html = resp.read().decode('utf-8', errors='ignore')
            # Extract course codes
            # Course codes appear as "204xxx - (" or in links
            courses = set(re.findall(r'<b>\s*(204\d{3})\s*</b>|(204\d{3})\s*-\s*\(', html))
            found = set()
            for a, b in courses:
                if a: found.add(a)
                if b: found.add(b)
            return found
    except Exception as e:
        print(f"Error for term {term}: {e}")
        return set()

t1_courses = get_reg_courses('1/2569')
print(f"1/2569 courses count: {len(t1_courses)}")
print("Sample 1/2569:", sorted(list(t1_courses))[:10])

t2_courses = get_reg_courses('2/2569')
print(f"2/2569 courses count: {len(t2_courses)}")
print("Sample 2/2569:", sorted(list(t2_courses))[:10])
