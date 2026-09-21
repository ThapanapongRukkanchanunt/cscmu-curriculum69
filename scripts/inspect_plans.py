import sys, docx
sys.stdout.reconfigure(encoding='utf-8')

doc = docx.Document('d:/Documents/teaching/OBE2-CS69-3.docx')

recording = False
plan_name = ""
plan_lines = []

for i, p in enumerate(doc.paragraphs):
    txt = p.text.strip()
    if '2.4 แผนการศึกษา' in txt or 'แผนการศึกษา' in txt:
        print(f'Line {i}: {txt}')
    if 'แผนสหกิจศึกษา' in txt or 'แผนมุ่งเน้นโครงงาน' in txt:
        print(f'Line {i} [PLAN]: {txt}')

print("\n--- TABLES WITH STUDY PLANS ---")
for i, table in enumerate(doc.tables):
    txt = ' '.join(c.text.strip() for row in table.rows for c in row.cells)
    if 'ชั้นปีที่ 1' in txt or 'ภาคการศึกษาที่ 1' in txt:
        print(f'Table {i}: rows={len(table.rows)}, cols={len(table.columns)}')
        for r in table.rows[:3]:
            print('  |  '.join(c.text.strip().replace('\n', ' ') for c in r.cells))
