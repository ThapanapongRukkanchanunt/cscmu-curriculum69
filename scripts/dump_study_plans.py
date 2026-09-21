import sys, docx
sys.stdout.reconfigure(encoding='utf-8')

doc = docx.Document('d:/Documents/teaching/OBE2-CS69-3.docx')

lines = []
for i in range(444, 750):
    t = doc.paragraphs[i].text.strip()
    if t:
        lines.append(f'{i}: {t}')

with open('d:/Documents/curriculum69/scripts/study_plans_raw.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(lines))

print(f'Wrote {len(lines)} lines to study_plans_raw.txt')
