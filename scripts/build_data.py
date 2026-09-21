"""
build_data.py
Extracts curriculum structure, study plans, course details, and prerequisites from:
1. teaching/OBE2-CS69-3.docx
2. REG CMU (terms 1/2569 and 2/2569)
3. MIS CMU (year 2569 semester 2)
4. Merges with existing curated data in course_tree/data.js and mis_prereqs.js

Outputs:
d:/Documents/curriculum69/data/curriculum69.json
"""

import sys
import os
import json
import re
import urllib.request
import urllib.parse
import ssl
import docx

sys.stdout.reconfigure(encoding='utf-8')

# SSL Context for CMU servers
ssl_ctx = ssl.create_default_context()
ssl_ctx.check_hostname = False
ssl_ctx.verify_mode = ssl.CERT_NONE

HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}

def fetch_reg_courses(term):
    """Fetch all 204 courses offered in given term (e.g. '1/2569', '2/2569') from REG CMU."""
    print(f"Querying REG CMU for term {term}...")
    url = f'https://www1.reg.cmu.ac.th/registrationoffice/searchcourse.php?tterm={term}#showrecord'
    data = urllib.parse.urlencode({'fgroup': '204', 'button': 'Search'}).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers=HEADERS)
    offered = set()
    try:
        with urllib.request.urlopen(req, context=ssl_ctx, timeout=15) as resp:
            html = resp.read().decode('utf-8', errors='ignore')
            # Extract course codes from result table
            # Course codes appear as '204xxx - (' or in section rows
            matches = re.findall(r'(204\d{3})\s*-\s*\(', html)
            for m in matches:
                offered.add(m)
            # Also check bold course codes
            b_matches = re.findall(r'<b>\s*(204\d{3})\s*</b>', html)
            for m in b_matches:
                offered.add(m)
        print(f" -> Found {len(offered)} courses offered in {term}")
    except Exception as e:
        print(f" -> REG CMU query error for {term}: {e}")
    return offered

def fetch_mis_course(courseno):
    """Fetch official prerequisite and description from MIS CMU for year 2569 semester 2."""
    url = f'https://www.mis.cmu.ac.th/TQF/coursepublic.aspx?courseno={courseno}&semester=2&year=2569'
    req = urllib.request.Request(url, headers=HEADERS)
    info = {'mis_prereq': '', 'mis_desc_th': '', 'mis_desc_en': ''}
    try:
        with urllib.request.urlopen(req, context=ssl_ctx, timeout=8) as resp:
            html = resp.read().decode('utf-8', errors='ignore')
            spans = dict(re.findall(r'<span id="([^"]+)"[^>]*>(.*?)</span>', html, re.DOTALL))
            
            # Prerequisite
            if 'lblPreequisite' in spans:
                prereq_raw = re.sub(r'<[^>]+>', '', spans['lblPreequisite']).strip()
                if prereq_raw and prereq_raw != '-':
                    info['mis_prereq'] = prereq_raw
            
            # Desc Eng
            if 'lblCourseDescriptionEng' in spans:
                desc_en = re.sub(r'<[^>]+>', '', spans['lblCourseDescriptionEng']).strip()
                if desc_en:
                    info['mis_desc_en'] = desc_en
                    
            # Desc Tha
            if 'lblCourseDescriptionTha' in spans:
                # Often in Windows-874 / TIS-620
                try:
                    desc_th = re.sub(r'<[^>]+>', '', spans['lblCourseDescriptionTha']).strip()
                    if desc_th:
                        info['mis_desc_th'] = desc_th
                except:
                    pass
    except Exception:
        pass
    return info

def extract_docx_course_descriptions(docx_path):
    """Extract official course descriptions and prerequisites from Appendix of OBE2-CS69-3.docx."""
    print("Extracting course descriptions from OBE2 docx...")
    doc = docx.Document(docx_path)
    
    courses_docx = {}
    current_course = None
    
    for i, p in enumerate(doc.paragraphs):
        t = p.text.strip()
        if not t:
            continue
            
        # Match pattern like: ว.คพ. 111 (204111) : การเขียนโปรแกรมเบื้องต้น 3(2-2-5)
        # or CS 111 : Fundamentals of Programming
        m_head = re.match(r'(?:ว\.คพ\.|ว\.คณ\.|ว\.สถ\.|ว\.วท\.|ร\.ท\.|ม\.อ\.|ว\.ฟส\.|ว\.ชว\.|ว\.คม\.|วศ\.หป\.|บธ\.กง\.|ศศ\.|นว\.ด\.)\s*(\d{3})\s*\((\d{6})\)\s*[:：]\s*(.*?)(?:\s+(\d\([0-9\-]+\)|\d\s*หน่วยกิต))?$', t)
        if m_head:
            cid = m_head.group(2)
            name_th = m_head.group(3).strip()
            credits = m_head.group(4).strip() if m_head.group(4) else ""
            current_course = cid
            if current_course not in courses_docx:
                courses_docx[current_course] = {
                    'id': cid,
                    'name_TH': name_th,
                    'name_EN': '',
                    'credits': credits,
                    'prereq_TH': '',
                    'desc_TH': '',
                    'desc_EN': ''
                }
            continue
            
        if current_course:
            # Check English name line: CS 111 : Fundamentals of Programming
            m_en = re.match(r'^[A-Z]{2,5}\s*\d{3}\s*[:：]\s*(.+)$', t)
            if m_en and not courses_docx[current_course]['name_EN']:
                courses_docx[current_course]['name_EN'] = m_en.group(1).strip()
                continue
                
            # Check prerequisite line
            if 'เงื่อนไขที่ต้องผ่านก่อน' in t:
                parts = t.split(':', 1) if ':' in t else t.split('：', 1)
                if len(parts) > 1:
                    courses_docx[current_course]['prereq_TH'] = parts[1].strip()
                continue
                
            # Otherwise description lines
            # Check if Thai text
            if any('\u0e00' <= char <= '\u0e7f' for char in t):
                if not courses_docx[current_course]['desc_TH']:
                    courses_docx[current_course]['desc_TH'] = t
                else:
                    courses_docx[current_course]['desc_TH'] += " " + t
            else:
                # English description
                if not courses_docx[current_course]['desc_EN']:
                    courses_docx[current_course]['desc_EN'] = t
                else:
                    courses_docx[current_course]['desc_EN'] += " " + t

    print(f" -> Extracted {len(courses_docx)} courses from docx appendix")
    return courses_docx

def load_existing_course_data():
    """Load existing curated course data from course_tree/data.js and mis_prereqs.js."""
    courses_map = {}
    
    # 1. data.js
    data_js_path = 'd:/Documents/course_tree/data.js'
    if os.path.exists(data_js_path):
        with open(data_js_path, 'r', encoding='utf-8') as f:
            content = f.read()
        m = re.search(r'coursesDataAfter2569\s*=\s*(\[.*?\]);?\s*$', content, re.DOTALL)
        if m:
            c_list = json.loads(m.group(1))
            for c in c_list:
                cid = c.get('id')
                if cid:
                    courses_map[cid] = c
    
    # 2. mis_prereqs.js
    mis_path = 'd:/Documents/course_tree/mis_prereqs.js'
    mis_prereqs = {}
    if os.path.exists(mis_path):
        with open(mis_path, 'r', encoding='utf-8') as f:
            txt = f.read()
        for m in re.finditer(r'"(\d{6})":\s*"([^"]*)"', txt):
            mis_prereqs[m.group(1)] = m.group(2)
            
    return courses_map, mis_prereqs

def build_dataset():
    print("=== Building CMU CS Curriculum 2569 Dataset ===")
    
    # 1. Load existing rich data
    existing_courses, existing_mis_prereqs = load_existing_course_data()
    print(f"Loaded {len(existing_courses)} courses from course_tree/data.js")
    
    # 2. Extract from docx
    docx_path = 'd:/Documents/teaching/OBE2-CS69-3.docx'
    docx_courses = extract_docx_course_descriptions(docx_path)
    
    # 3. Fetch REG CMU offered courses for 2569 Sem 1 and Sem 2
    reg_sem1 = fetch_reg_courses('1/2569')
    reg_sem2 = fetch_reg_courses('2/2569')
    
    # 4. Fetch MIS CMU for all 204 courses
    print("Fetching prerequisite & description details from MIS CMU...")
    all_course_ids = sorted(list(set(list(existing_courses.keys()) + list(docx_courses.keys()))))
    mis_live_data = {}
    for cid in all_course_ids:
        if cid.startswith('204'):
            mis_info = fetch_mis_course(cid)
            if mis_info.get('mis_prereq') or mis_info.get('mis_desc_en'):
                mis_live_data[cid] = mis_info
    print(f" -> Fetched MIS details for {len(mis_live_data)} courses")
    
    # 5. Merge all course information
    final_courses = {}
    for cid in all_course_ids:
        curated = existing_courses.get(cid, {})
        docx_c = docx_courses.get(cid, {})
        mis_live = mis_live_data.get(cid, {})
        
        name_th = curated.get('name_TH') or docx_c.get('name_TH', '')
        name_en = curated.get('name_EN') or docx_c.get('name_EN', '')
        credits = curated.get('credits') or docx_c.get('credits', '3(3-0-6)')
        
        desc_th = curated.get('desc_TH') or docx_c.get('desc_TH', '')
        desc_en = curated.get('desc_EN') or docx_c.get('desc_EN', '') or mis_live.get('mis_desc_en', '')
        
        # Classification
        classification = curated.get('classification', 'elective')
        if not classification or classification == 'other':
            if cid in ['204111', '204115', '204255']:
                classification = 'core'
            elif cid.startswith('2042') or cid in ['204321', '204361', '204451', '204306', '204315', '204497', '204496']:
                classification = 'compulsory'
                
        is_project_based = (classification == 'project-elective')
        
        # Official MIS Prerequisite string
        official_prereq = mis_live.get('mis_prereq') or existing_mis_prereqs.get(cid) or docx_c.get('prereq_TH', '')
        if not official_prereq:
            official_prereq = "None"
            
        # Parse prerequisite IDs list
        prereqs_list = curated.get('prerequisites', [])
        if not prereqs_list:
            # Extract 6-digit course IDs from docx/mis prereq string
            extracted_ids = re.findall(r'\b(204\d{3}|206\d{3}|208\d{3}|001\d{3})\b', official_prereq)
            prereqs_list = sorted(list(set(extracted_ids)))
            
        # Term offerings from REG CMU
        offered_t1 = (cid in reg_sem1) or curated.get('terms', {}).get('t1', False)
        offered_t2 = (cid in reg_sem2) or curated.get('terms', {}).get('t2', False)
        
        # In case neither returned from reg (e.g. non-204 course), keep existing curated terms if present
        if not offered_t1 and not offered_t2:
            offered_t1 = curated.get('terms', {}).get('t1', False)
            offered_t2 = curated.get('terms', {}).get('t2', False)

        # Precise terms for GE and Core courses based on study plans and official scheduling
        known_terms = {
            '001101': {'t1': True, 't2': False},
            '001102': {'t1': False, 't2': True},
            '001225': {'t1': True, 't2': False},
            '001201': {'t1': True, 't2': True},
            '001233': {'t1': True, 't2': True},
            '001241': {'t1': True, 't2': True},
            '001242': {'t1': True, 't2': False},
            '001243': {'t1': False, 't2': True},
            '001249': {'t1': False, 't2': True},
            '140104': {'t1': True, 't2': False},
            '201111': {'t1': True, 't2': True},
            '201114': {'t1': True, 't2': False},
            '201116': {'t1': True, 't2': False},
            '201190': {'t1': True, 't2': True},
            '271111': {'t1': False, 't2': True},
            '702101': {'t1': True, 't2': True},
            '751100': {'t1': True, 't2': True},
            '888107': {'t1': False, 't2': True},
            '202101': {'t1': False, 't2': True},
            '206111': {'t1': True, 't2': True},
            '206183': {'t1': True, 't2': False},
            '207187': {'t1': False, 't2': True},
            '208269': {'t1': True, 't2': False},
            '206324': {'t1': False, 't2': True},
        }
        if cid in known_terms:
            offered_t1 = known_terms[cid]['t1']
            offered_t2 = known_terms[cid]['t2']
            
        final_courses[cid] = {
            'id': cid,
            'name_TH': name_th,
            'name_EN': name_en,
            'credits': credits,
            'desc_TH': desc_th,
            'desc_EN': desc_en,
            'classification': classification,
            'is_project_based': is_project_based,
            'prerequisites': prereqs_list,
            'official_prereq': official_prereq,
            'terms': {
                't1': bool(offered_t1),
                't2': bool(offered_t2)
            }
        }
        
    print(f"Total processed courses: {len(final_courses)}")
    
    # 6. Build curriculum overview metadata
    curriculum_meta = {
        "title_TH": "หลักสูตรวิทยาศาสตรบัณฑิต สาขาวิชาวิทยาการคอมพิวเตอร์ (หลักสูตรปรับปรุง พ.ศ. 2569)",
        "title_EN": "Bachelor of Science Program in Computer Science (Revised Curriculum 2026)",
        "degree_TH": "วิทยาศาสตรบัณฑิต (วิทยาการคอมพิวเตอร์) / วท.บ. (วิทยาการคอมพิวเตอร์)",
        "degree_EN": "Bachelor of Science (Computer Science) / B.S. (Computer Science)",
        "philosophy_TH": "มุ่งเน้นการผลิตบัณฑิตที่มีทักษะขั้นสูงด้านวิทยาการคอมพิวเตอร์ ปัญญาประดิษฐ์ วิศวกรรมซอฟต์แวร์ และเทคโนโลยีดิจิทัล สามารถออกแบบและพัฒนานวัตกรรมที่มีมูลค่าสูง ตอบโจทย์อุตสาหกรรมและสังคมยุคใหม่ พร้อมคุณธรรม จริยธรรมในวิชาชีพ",
        "philosophy_EN": "Dedicated to producing graduates with advanced computing capabilities in Computer Science, Artificial Intelligence, Software Engineering, and Digital Innovations, capable of designing and developing high-impact solutions for modern industry and society with professional ethics.",
        "plans": {
            "coop_minor": {
                "id": "coop_minor",
                "name_TH": "แผนสหกิจศึกษา (มีวิชาโท)",
                "name_EN": "Co-operative Education Plan (With Minor)",
                "total_credits": 123,
                "categories": [
                    {"id": "gened", "name_TH": "หมวดวิชาศึกษาทั่วไป", "name_EN": "General Education", "credits": 24, "note": "Language 9, Digital 3, Global 3, Innovation 3, Entrepreneur 3, GE Elective 3"},
                    {"id": "core", "name_TH": "วิชาแกน", "name_EN": "Core Courses", "credits": 25, "note": "Bio, Phys/Chem, Math 111, Math 183, Stat 269, CS 100, CS 111, CS 115, CS 255"},
                    {"id": "compulsory_shared", "name_TH": "วิชาเอกบังคับร่วม", "name_EN": "Shared Compulsory Courses", "credits": 29, "note": "11 required CS & Applied Math courses"},
                    {"id": "compulsory_plan", "name_TH": "วิชาเอกบังคับประจำแผน (สหกิจศึกษา)", "name_EN": "Plan Compulsory (Co-op 204496)", "credits": 6, "note": "204496 Cooperative Education"},
                    {"id": "major_electives", "name_TH": "วิชาเอกเลือก", "name_EN": "Major Electives (300-400)", "credits": 18, "note": "At least 9 credits at 400 level"},
                    {"id": "minor", "name_TH": "หมวดวิชาโท", "name_EN": "Academic Minor", "credits": 15, "note": "15 credits from any minor program in university"},
                    {"id": "free_electives", "name_TH": "หมวดวิชาเลือกเสรี", "name_EN": "Free Electives", "credits": 6, "note": "Any university courses"}
                ]
            },
            "coop_no_minor": {
                "id": "coop_no_minor",
                "name_TH": "แผนสหกิจศึกษา (ไม่มีวิชาโท - เน้นวิชาเอกเลือก ว.คพ.)",
                "name_EN": "Co-operative Education Plan (No Minor - CS Elective Focus)",
                "total_credits": 123,
                "categories": [
                    {"id": "gened", "name_TH": "หมวดวิชาศึกษาทั่วไป", "name_EN": "General Education", "credits": 24, "note": "Language 9, Digital 3, Global 3, Innovation 3, Entrepreneur 3, GE Elective 3"},
                    {"id": "core", "name_TH": "วิชาแกน", "name_EN": "Core Courses", "credits": 25, "note": "Bio, Phys/Chem, Math 111, Math 183, Stat 269, CS 100, CS 111, CS 115, CS 255"},
                    {"id": "compulsory_shared", "name_TH": "วิชาเอกบังคับร่วม", "name_EN": "Shared Compulsory Courses", "credits": 29, "note": "11 required CS & Applied Math courses"},
                    {"id": "compulsory_plan", "name_TH": "วิชาเอกบังคับประจำแผน (สหกิจศึกษา)", "name_EN": "Plan Compulsory (Co-op 204496)", "credits": 6, "note": "204496 Cooperative Education"},
                    {"id": "major_electives", "name_TH": "วิชาเอกเลือก (ปกติ + เสริมแทนวิชาโท)", "name_EN": "Major Electives (Base + CS Electives)", "credits": 33, "note": "18 credits regular + 15 credits CS electives at 300-400 level"},
                    {"id": "free_electives", "name_TH": "หมวดวิชาเลือกเสรี", "name_EN": "Free Electives", "credits": 6, "note": "Any university courses"}
                ]
            },
            "project_minor": {
                "id": "project_minor",
                "name_TH": "แผนมุ่งเน้นโครงงาน (มีวิชาโท)",
                "name_EN": "Project-oriented Plan (With Minor)",
                "total_credits": 126,
                "categories": [
                    {"id": "gened", "name_TH": "หมวดวิชาศึกษาทั่วไป", "name_EN": "General Education", "credits": 24, "note": "Language 9, Digital 3, Global 3, Innovation 3, Entrepreneur 3, GE Elective 3"},
                    {"id": "core", "name_TH": "วิชาแกน", "name_EN": "Core Courses", "credits": 25, "note": "Bio, Phys/Chem, Math 111, Math 183, Stat 269, CS 100, CS 111, CS 115, CS 255"},
                    {"id": "compulsory_shared", "name_TH": "วิชาเอกบังคับร่วม", "name_EN": "Shared Compulsory Courses", "credits": 29, "note": "11 required CS & Applied Math courses"},
                    {"id": "major_electives", "name_TH": "วิชาเอกเลือก", "name_EN": "Major Electives (300-400)", "credits": 27, "note": "At least 18 credits at 400 level & at least 15 credits project-based"},
                    {"id": "minor", "name_TH": "หมวดวิชาโท", "name_EN": "Academic Minor", "credits": 15, "note": "15 credits from any minor program in university"},
                    {"id": "free_electives", "name_TH": "หมวดวิชาเลือกเสรี", "name_EN": "Free Electives", "credits": 6, "note": "Any university courses"}
                ]
            },
            "project_no_minor": {
                "id": "project_no_minor",
                "name_TH": "แผนมุ่งเน้นโครงงาน (ไม่มีวิชาโท - เน้นวิชาเอกเลือก ว.คพ.)",
                "name_EN": "Project-oriented Plan (No Minor - CS Elective Focus)",
                "total_credits": 126,
                "categories": [
                    {"id": "gened", "name_TH": "หมวดวิชาศึกษาทั่วไป", "name_EN": "General Education", "credits": 24, "note": "Language 9, Digital 3, Global 3, Innovation 3, Entrepreneur 3, GE Elective 3"},
                    {"id": "core", "name_TH": "วิชาแกน", "name_EN": "Core Courses", "credits": 25, "note": "Bio, Phys/Chem, Math 111, Math 183, Stat 269, CS 100, CS 111, CS 115, CS 255"},
                    {"id": "compulsory_shared", "name_TH": "วิชาเอกบังคับร่วม", "name_EN": "Shared Compulsory Courses", "credits": 29, "note": "11 required CS & Applied Math courses"},
                    {"id": "major_electives", "name_TH": "วิชาเอกเลือก (ปกติ + เสริมแทนวิชาโท)", "name_EN": "Major Electives (Base + CS Electives)", "credits": 42, "note": "27 credits regular + 15 credits CS electives at 300-400 level"},
                    {"id": "free_electives", "name_TH": "หมวดวิชาเลือกเสรี", "name_EN": "Free Electives", "credits": 6, "note": "Any university courses"}
                ]
            }
        },
        "category_course_lists": {
            "gened_structure": {
                "language": {
                    "id": "language",
                    "title_TH": "กลุ่มวิชาด้านทักษะทางการสื่อสารและภาษา",
                    "title_EN": "Language Literacy",
                    "credits": 9,
                    "credits_text": "9 หน่วยกิต",
                    "options": {
                        "below_b1": {
                            "id": "below_b1",
                            "name_TH": "ระดับ e-Pro ไม่ถึง B1 หรือเทียบเท่า",
                            "name_EN": "e-Pro Score Below B1 or Equivalent",
                            "description_TH": "เรียนครบทั้ง 3 กระบวนวิชา (รวม 9 หน่วยกิต)",
                            "description_EN": "Complete all 3 prescribed courses (9 credits total)",
                            "courses": [
                                {"id": "001101", "name_TH": "ภาษาอังกฤษพื้นฐาน 1", "name_EN": "Fundamental English 1", "credits": "3(3-0-6)", "type": "required"},
                                {"id": "001102", "name_TH": "ภาษาอังกฤษพื้นฐาน 2", "name_EN": "Fundamental English 2", "credits": "3(3-0-6)", "type": "required"},
                                {"id": "001225", "name_TH": "ภาษาอังกฤษสำหรับวิทยาศาสตร์และเทคโนโลยี", "name_EN": "English for Science and Technology", "credits": "3(3-0-6)", "type": "required"}
                            ]
                        },
                        "b1_plus": {
                            "id": "b1_plus",
                            "name_TH": "ระดับ e-Pro ตั้งแต่ B1 ขึ้นไป หรือเทียบเท่า",
                            "name_EN": "e-Pro Score B1+ or Higher or Equivalent",
                            "description_TH": "วิชาบังคับ 3 หน่วยกิต + เลือกเรียน 6 หน่วยกิต (2 กระบวนวิชา) จากวิชาเลือกด้านล่าง",
                            "description_EN": "3 credits required + choose 6 credits (2 courses) from electives below",
                            "required_courses": [
                                {"id": "001225", "name_TH": "ภาษาอังกฤษสำหรับวิทยาศาสตร์และเทคโนโลยี", "name_EN": "English for Science and Technology", "credits": "3(3-0-6)", "type": "required"}
                            ],
                            "elective_directive_TH": "เลือกเรียน 6 หน่วยกิต จากกระบวนวิชาต่อไปนี้ (หรือเทียบผลการสอบมาตรฐานภาษาอังกฤษตามประกาศ มช.):",
                            "elective_directive_EN": "Choose 6 credits from the following courses (or equivalent standardized test score):",
                            "elective_courses": [
                                {"id": "001201", "name_TH": "การอ่านอย่างมีวิจารณญาณและการเขียนอย่างมีประสิทธิภาพ", "name_EN": "Critical Reading and Effective Writing", "credits": "3(3-0-6)"},
                                {"id": "001233", "name_TH": "ภาษาอังกฤษสำหรับการสอบมาตรฐาน", "name_EN": "English for Standardized Tests", "credits": "3(3-0-6)"},
                                {"id": "001241", "name_TH": "การพูดภาษาอังกฤษเพื่อการสื่อสาร", "name_EN": "Oral Communication in English", "credits": "3(3-0-6)"},
                                {"id": "001242", "name_TH": "เปิดโลกทักษะการอ่านและการเขียน", "name_EN": "Exploring Reading and Writing Skills", "credits": "3(3-0-6)"},
                                {"id": "001243", "name_TH": "พื้นฐานการเขียนเรียงความอย่างมีประสิทธิภาพ", "name_EN": "Basics of Effective Essay Writing", "credits": "3(3-0-6)"},
                                {"id": "001249", "name_TH": "ภาษาอังกฤษเพื่อการเดินทางท่องเที่ยว", "name_EN": "English for Travelling", "credits": "3(3-0-6)"}
                            ]
                        }
                    }
                },
                "digital": {
                    "id": "digital",
                    "title_TH": "กลุ่มวิชาด้านทักษะความเข้าใจและการใช้เทคโนโลยีดิจิทัล",
                    "title_EN": "Digital Literacy",
                    "credits": 3,
                    "credits_text": "3 หน่วยกิต",
                    "is_fixed": True,
                    "courses": [
                        {"id": "204100", "name_TH": "เรื่องน่ารู้ทางปัญญาประดิษฐ์และดิจิทัล", "name_EN": "Artificial Intelligence and Digital Essentials", "credits": "3(3-0-6)", "type": "required"}
                    ]
                },
                "global": {
                    "id": "global",
                    "title_TH": "กลุ่มวิชาด้านทักษะการเป็นพลเมืองโลก",
                    "title_EN": "Global Citizen",
                    "credits": 3,
                    "credits_text": "3 หน่วยกิต",
                    "is_fixed": True,
                    "courses": [
                        {"id": "140104", "name_TH": "การเป็นพลเมือง", "name_EN": "Citizenship", "credits": "3(3-0-6)", "type": "required"}
                    ]
                },
                "creativity": {
                    "id": "creativity",
                    "title_TH": "กลุ่มวิชาด้านทักษะการคิดสร้างสรรค์และนวัตกรรม",
                    "title_EN": "Creativity and Innovation",
                    "credits": 3,
                    "credits_text": "3 หน่วยกิต",
                    "directive_TH": "เลือกเรียน 3 หน่วยกิต (1 วิชา) จากกระบวนวิชาต่อไปนี้:",
                    "directive_EN": "Choose 3 credits (1 course) from the following courses:",
                    "courses": [
                        {"id": "201116", "name_TH": "วิทยาศาสตร์และภาวะโลกร้อน", "name_EN": "Science and Global Warming", "credits": "3(3-0-6)"},
                        {"id": "201190", "name_TH": "การคิดอย่างมีวิจารณญาณ การแก้ปัญหา และการสื่อสารทางวิทยาศาสตร์", "name_EN": "Critical Thinking, Problem Solving and Science Communication", "credits": "3(3-0-6)"},
                        {"id": "271111", "name_TH": "หุ่นยนต์วิจักษณ์", "name_EN": "Robotics Appreciation", "credits": "3(3-0-6)"}
                    ]
                },
                "entrepreneur": {
                    "id": "entrepreneur",
                    "title_TH": "กลุ่มวิชาด้านทักษะการเป็นผู้ประกอบการ",
                    "title_EN": "Entrepreneurial Skills",
                    "credits": 3,
                    "credits_text": "3 หน่วยกิต",
                    "directive_TH": "เลือกเรียน 3 หน่วยกิต (1 วิชา) จากกระบวนวิชาต่อไปนี้:",
                    "directive_EN": "Choose 3 credits (1 course) from the following courses:",
                    "courses": [
                        {"id": "702101", "name_TH": "การเงินในชีวิตประจำวัน", "name_EN": "Finance for Daily Life", "credits": "3(3-0-6)"},
                        {"id": "751100", "name_TH": "เศรษฐศาสตร์ในชีวิตประจำวัน", "name_EN": "Economics for Everyday Life", "credits": "3(3-0-6)"},
                        {"id": "888107", "name_TH": "การเริ่มต้นธุรกิจบนดิจิทัลแพลตฟอร์ม", "name_EN": "Business Startup on Digital Platform", "credits": "3(3-0-6)"}
                    ]
                },
                "digital_global_ai": {
                    "id": "digital_global_ai",
                    "title_TH": "กลุ่มวิชาด้านทักษะดิจิทัล หรือ พลเมืองโลก หรือ ปัญญาประดิษฐ์",
                    "title_EN": "Digital Literacy or Global Citizen or Artificial Intelligence",
                    "credits": 3,
                    "credits_text": "3 หน่วยกิต",
                    "directive_TH": "เลือกเรียน 3 หน่วยกิต (1 วิชา) จากกระบวนวิชาต่อไปนี้:",
                    "directive_EN": "Choose 3 credits (1 course) from the following courses:",
                    "courses": [
                        {"id": "201111", "name_TH": "โลกแห่งวิทยาศาสตร์", "name_EN": "The World of Science", "credits": "3(3-0-6)"},
                        {"id": "201114", "name_TH": "วิทยาศาสตร์สิ่งแวดล้อมในโลกปัจจุบัน", "name_EN": "Environmental Science in Today's World", "credits": "3(3-0-6)"},
                        {"id": "204123", "name_TH": "วิทยาการข้อมูลเบื้องต้น", "name_EN": "Introduction to Data Science", "credits": "3(2-2-5)"},
                        {"id": "204171", "name_TH": "ปัญญาประดิษฐ์ท่ามกลางพวกเรา", "name_EN": "Artificial Intelligence Among Us", "credits": "3(3-0-6)"}
                    ]
                }
            },
            "gened": [
                {"id": "001101", "name_TH": "ภาษาอังกฤษพื้นฐาน 1", "name_EN": "Fundamental English 1", "credits": "3(3-0-6)", "group": "Language Literacy (9 cr)"},
                {"id": "001102", "name_TH": "ภาษาอังกฤษพื้นฐาน 2", "name_EN": "Fundamental English 2", "credits": "3(3-0-6)", "group": "Language Literacy (9 cr)"},
                {"id": "001225", "name_TH": "ภาษาอังกฤษสำหรับวิทยาศาสตร์และเทคโนโลยี", "name_EN": "English for Science and Technology", "credits": "3(3-0-6)", "group": "Language Literacy (9 cr)"},
                {"id": "204100", "name_TH": "เรื่องน่ารู้ทางปัญญาประดิษฐ์และดิจิทัล", "name_EN": "Artificial Intelligence and Digital Essentials", "credits": "3(3-0-6)", "group": "Digital Literacy (3 cr)"},
                {"id": "140104", "name_TH": "การเป็นพลเมือง", "name_EN": "Citizenship", "credits": "3(3-0-6)", "group": "Global Citizen (3 cr)"},
                {"id": "GE_CREAT", "name_TH": "วิชาศึกษาทั่วไป กลุ่มทักษะการคิดสร้างสรรค์และนวัตกรรม", "name_EN": "GE Course in Creativity and Innovation", "credits": "3(3-0-6)", "group": "Creativity & Innovation (3 cr)"},
                {"id": "GE_ENTREP", "name_TH": "วิชาศึกษาทั่วไป กลุ่มทักษะการเป็นผู้ประกอบการ", "name_EN": "GE Course in Entrepreneurial Skills", "credits": "3(3-0-6)", "group": "Entrepreneurial Skills (3 cr)"},
                {"id": "GE_ELEC", "name_TH": "วิชาศึกษาทั่วไป กลุ่มดิจิทัล หรือ พลเมืองโลก หรือ AI", "name_EN": "GE Course in Digital / Global / AI", "credits": "3(3-0-6)", "group": "Digital / Global / AI (3 cr)"}
            ],
            "core": [
                {"id": "202101", "name_TH": "ชีววิทยาพื้นฐาน 1", "name_EN": "Basic Biology 1", "credits": "3(3-0-6)"},
                {"id": "204100", "name_TH": "เรื่องน่ารู้ทางปัญญาประดิษฐ์และดิจิทัล", "name_EN": "Artificial Intelligence and Digital Essentials", "credits": "3(3-0-6)"},
                {"id": "204111", "name_TH": "การเขียนโปรแกรมเบื้องต้น", "name_EN": "Fundamentals of Programming", "credits": "3(2-2-5)"},
                {"id": "204115", "name_TH": "หลักการเขียนโปรแกรมเชิงฟังก์ชัน", "name_EN": "Principles of Functional Programming", "credits": "3(2-2-5)"},
                {"id": "204255", "name_TH": "การเขียนโปรแกรมเชิงวัตถุและโครงสร้างข้อมูล", "name_EN": "Object-Oriented Programming and Data Structures", "credits": "4(3-2-7)"},
                {"id": "206111", "name_TH": "แคลคูลัส 1", "name_EN": "Calculus 1", "credits": "3(3-0-6)"},
                {"id": "206183", "name_TH": "โครงสร้างวิยุต", "name_EN": "Discrete Structure", "credits": "3(3-0-6)"},
                {"id": "207187", "name_TH": "ฟิสิกส์ 1 (หรือ 203103 เคมีทั่วไป 1)", "name_EN": "Physics 1 (or 203103 General Chemistry 1)", "credits": "3(3-0-6)"},
                {"id": "208269", "name_TH": "สถิติสำหรับวิทยาการคอมพิวเตอร์", "name_EN": "Statistics for Computer Science", "credits": "3(3-0-6)"}
            ],
            "compulsory": [
                {"id": "204212", "name_TH": "การพัฒนาเว็บแอปพลิเคชันแบบฟูลสแต๊ก", "name_EN": "Full-stack Web Application Development", "credits": "3(2-2-5)", "group": "Shared"},
                {"id": "204231", "name_TH": "การจัดระบบและสถาปัตยกรรมคอมพิวเตอร์", "name_EN": "Computer Organization and Architecture", "credits": "3(2-2-5)", "group": "Shared"},
                {"id": "204232", "name_TH": "เครือข่ายคอมพิวเตอร์และเกณฑ์วิธี", "name_EN": "Computer Networks and Protocols", "credits": "3(3-0-6)", "group": "Shared"},
                {"id": "204271", "name_TH": "ปัญญาประดิษฐ์เบื้องต้น", "name_EN": "Introduction to Artificial Intelligence", "credits": "3(2-2-5)", "group": "Shared"},
                {"id": "204306", "name_TH": "จริยธรรมสำหรับผู้ประกอบวิชาชีพคอมพิวเตอร์", "name_EN": "Ethics for Computer Professionals", "credits": "1(1-0-2)", "group": "Shared"},
                {"id": "204315", "name_TH": "การจัดระเบียบของภาษาโปรแกรม", "name_EN": "Organization of Programming Languages", "credits": "3(3-0-6)", "group": "Shared"},
                {"id": "204321", "name_TH": "ระบบฐานข้อมูล", "name_EN": "Database Systems", "credits": "3(2-2-5)", "group": "Shared"},
                {"id": "204361", "name_TH": "วิศวกรรมซอฟต์แวร์", "name_EN": "Software Engineering", "credits": "3(3-0-6)", "group": "Shared"},
                {"id": "204451", "name_TH": "การออกแบบและการวิเคราะห์อัลกอริทึม", "name_EN": "Algorithm Design and Analysis", "credits": "3(3-0-6)", "group": "Shared"},
                {"id": "204497", "name_TH": "สัมมนาทางวิทยาการคอมพิวเตอร์", "name_EN": "Seminar in Computer Science", "credits": "1(1-0-2)", "group": "Shared"},
                {"id": "206324", "name_TH": "พีชคณิตเชิงเส้นประยุกต์", "name_EN": "Applied Linear Algebra", "credits": "3(3-0-6)", "group": "Shared"},
                {"id": "204496", "name_TH": "สหกิจศึกษา (เฉพาะแผนสหกิจศึกษา)", "name_EN": "Cooperative Education (Co-op Plan Only)", "credits": "6 หน่วยกิต", "group": "Co-op Plan Only"}
            ]
        },
        "study_plans": {
            "coop": [
                {
                    "semester": "Y1S1", "year": 1, "term": 1, "total_credits": 18,
                    "courses": [
                        {"id": "140104", "name_TH": "การเป็นพลเมือง", "name_EN": "Citizenship", "credits": "3(3-0-6)", "type": "gened"},
                        {"id": "204111", "name_TH": "การเขียนโปรแกรมเบื้องต้น", "name_EN": "Fundamentals of Programming", "credits": "3(2-2-5)", "type": "core"},
                        {"id": "206111", "name_TH": "แคลคูลัส 1", "name_EN": "Calculus 1", "credits": "3(3-0-6)", "type": "core"},
                        {"id": "206183", "name_TH": "โครงสร้างวิยุต", "name_EN": "Discrete Structure", "credits": "3(3-0-6)", "type": "core"},
                        {"id": "001101", "name_TH": "ภาษาอังกฤษพื้นฐาน 1 (หรือ ENGL 225)", "name_EN": "Fundamental English 1 (or ENGL 225)", "credits": "3(3-0-6)", "type": "gened"},
                        {"id": "GE_CREAT", "name_TH": "วิชาศึกษาทั่วไป (ทักษะการคิดสร้างสรรค์และนวัตกรรม)", "name_EN": "GE Course in Creativity & Innovation", "credits": "3(3-0-6)", "type": "gened"}
                    ]
                },
                {
                    "semester": "Y1S2", "year": 1, "term": 2, "total_credits": 18,
                    "courses": [
                        {"id": "202101", "name_TH": "ชีววิทยาพื้นฐาน 1", "name_EN": "Basic Biology 1", "credits": "3(3-0-6)", "type": "core"},
                        {"id": "204100", "name_TH": "เรื่องน่ารู้ทางปัญญาประดิษฐ์และดิจิทัล", "name_EN": "AI and Digital Essentials", "credits": "3(3-0-6)", "type": "core"},
                        {"id": "204115", "name_TH": "หลักการเขียนโปรแกรมเชิงฟังก์ชัน", "name_EN": "Principles of Functional Programming", "credits": "3(2-2-5)", "type": "core"},
                        {"id": "207187", "name_TH": "ฟิสิกส์ 1", "name_EN": "Physics 1", "credits": "3(3-0-6)", "type": "core"},
                        {"id": "001102", "name_TH": "ภาษาอังกฤษพื้นฐาน 2 (หรือวิชาที่กำหนด)", "name_EN": "Fundamental English 2 (or designated)", "credits": "3(3-0-6)", "type": "gened"},
                        {"id": "GE_ENTREP", "name_TH": "วิชาศึกษาทั่วไป (ทักษะการเป็นผู้ประกอบการ)", "name_EN": "GE Course in Entrepreneurial Skills", "credits": "3(3-0-6)", "type": "gened"}
                    ]
                },
                {
                    "semester": "Y2S1", "year": 2, "term": 1, "total_credits": 19,
                    "courses": [
                        {"id": "001225", "name_TH": "ภาษาอังกฤษสำหรับวิทยาศาสตร์และเทคโนโลยี", "name_EN": "English for Science and Technology", "credits": "3(3-0-6)", "type": "gened"},
                        {"id": "204231", "name_TH": "การจัดระบบและสถาปัตยกรรมคอมพิวเตอร์", "name_EN": "Computer Organization & Architecture", "credits": "3(2-2-5)", "type": "compulsory"},
                        {"id": "204255", "name_TH": "การเขียนโปรแกรมเชิงวัตถุและโครงสร้างข้อมูล", "name_EN": "OOP and Data Structures", "credits": "4(3-2-7)", "type": "core"},
                        {"id": "208269", "name_TH": "สถิติสำหรับวิทยาการคอมพิวเตอร์", "name_EN": "Statistics for Computer Science", "credits": "3(3-0-6)", "type": "core"},
                        {"id": "GE_DIGI", "name_TH": "วิชาศึกษาทั่วไป (ดิจิทัล/พลเมืองโลก/AI)", "name_EN": "GE Course (Digital/Global/AI)", "credits": "3(3-0-6)", "type": "gened"},
                        {"id": "ELEC_OR_MINOR_1", "name_TH": "วิชาเอกเลือก หรือ วิชาโท (1)", "name_EN": "Major Elective or Minor (1)", "credits": "3(3-0-6)", "type": "elective"}
                    ]
                },
                {
                    "semester": "Y2S2", "year": 2, "term": 2, "total_credits": 18,
                    "courses": [
                        {"id": "204212", "name_TH": "การพัฒนาเว็บแอปพลิเคชันแบบฟูลสแต๊ก", "name_EN": "Full-stack Web App Development", "credits": "3(2-2-5)", "type": "compulsory"},
                        {"id": "204232", "name_TH": "เครือข่ายคอมพิวเตอร์และเกณฑ์วิธี", "name_EN": "Computer Networks and Protocols", "credits": "3(3-0-6)", "type": "compulsory"},
                        {"id": "204271", "name_TH": "ปัญญาประดิษฐ์เบื้องต้น", "name_EN": "Intro to Artificial Intelligence", "credits": "3(2-2-5)", "type": "compulsory"},
                        {"id": "206324", "name_TH": "พีชคณิตเชิงเส้นประยุกต์", "name_EN": "Applied Linear Algebra", "credits": "3(3-0-6)", "type": "compulsory"},
                        {"id": "CS_ELEC_300_1", "name_TH": "วิชาเอกเลือก ว.คพ. ระดับ 300 หรือ 400", "name_EN": "Major Elective Level 300/400", "credits": "3(3-0-6)", "type": "elective"},
                        {"id": "ELEC_OR_MINOR_2", "name_TH": "วิชาเอกเลือก หรือ วิชาโท (2)", "name_EN": "Major Elective or Minor (2)", "credits": "3(3-0-6)", "type": "elective"}
                    ]
                },
                {
                    "semester": "Y3S1", "year": 3, "term": 1, "total_credits": 15,
                    "courses": [
                        {"id": "204321", "name_TH": "ระบบฐานข้อมูล", "name_EN": "Database Systems", "credits": "3(2-2-5)", "type": "compulsory"},
                        {"id": "204361", "name_TH": "วิศวกรรมซอฟต์แวร์", "name_EN": "Software Engineering", "credits": "3(3-0-6)", "type": "compulsory"},
                        {"id": "204451", "name_TH": "การออกแบบและการวิเคราะห์อัลกอริทึม", "name_EN": "Algorithm Design and Analysis", "credits": "3(3-0-6)", "type": "compulsory"},
                        {"id": "FREE_ELEC_1", "name_TH": "วิชาเลือกเสรี (1)", "name_EN": "Free Elective (1)", "credits": "3(3-0-6)", "type": "free"},
                        {"id": "ELEC_OR_MINOR_3", "name_TH": "วิชาเอกเลือก หรือ วิชาโท (3)", "name_EN": "Major Elective or Minor (3)", "credits": "3(3-0-6)", "type": "elective"}
                    ]
                },
                {
                    "semester": "Y3S2", "year": 3, "term": 2, "total_credits": 16,
                    "courses": [
                        {"id": "204306", "name_TH": "จริยธรรมสำหรับผู้ประกอบวิชาชีพคอมพิวเตอร์", "name_EN": "Ethics for Computer Professionals", "credits": "1(1-0-2)", "type": "compulsory"},
                        {"id": "204315", "name_TH": "การจัดระเบียบของภาษาโปรแกรม", "name_EN": "Organization of Programming Languages", "credits": "3(3-0-6)", "type": "compulsory"},
                        {"id": "CS_ELEC_300_2", "name_TH": "วิชาเอกเลือก ว.คพ. ระดับ 300 หรือ 400 (ก)", "name_EN": "Major Elective Level 300/400 (A)", "credits": "3(3-0-6)", "type": "elective"},
                        {"id": "CS_ELEC_300_3", "name_TH": "วิชาเอกเลือก ว.คพ. ระดับ 300 หรือ 400 (ข)", "name_EN": "Major Elective Level 300/400 (B)", "credits": "3(3-0-6)", "type": "elective"},
                        {"id": "ELEC_OR_MINOR_4", "name_TH": "วิชาเอกเลือก หรือ วิชาโท (4)", "name_EN": "Major Elective or Minor (4)", "credits": "3(3-0-6)", "type": "elective"},
                        {"id": "FREE_ELEC_2", "name_TH": "วิชาเลือกเสรี (2)", "name_EN": "Free Elective (2)", "credits": "3(3-0-6)", "type": "free"}
                    ]
                },
                {
                    "semester": "Y4S1", "year": 4, "term": 1, "total_credits": 6,
                    "courses": [
                        {"id": "204496", "name_TH": "สหกิจศึกษา", "name_EN": "Cooperative Education", "credits": "6 หน่วยกิต", "type": "compulsory"}
                    ]
                },
                {
                    "semester": "Y4S2", "year": 4, "term": 2, "total_credits": 19,
                    "courses": [
                        {"id": "204497", "name_TH": "สัมมนาทางวิทยาการคอมพิวเตอร์", "name_EN": "Seminar in Computer Science", "credits": "1(1-0-2)", "type": "compulsory"},
                        {"id": "CS_ELEC_400_1", "name_TH": "วิชาเอกเลือกระดับ 400 (1)", "name_EN": "Major Elective Level 400 (1)", "credits": "3(3-0-6)", "type": "elective"},
                        {"id": "CS_ELEC_400_2", "name_TH": "วิชาเอกเลือกระดับ 400 (2)", "name_EN": "Major Elective Level 400 (2)", "credits": "3(3-0-6)", "type": "elective"},
                        {"id": "CS_ELEC_400_3", "name_TH": "วิชาเอกเลือกระดับ 400 (3)", "name_EN": "Major Elective Level 400 (3)", "credits": "3(3-0-6)", "type": "elective"},
                        {"id": "ELEC_OR_MINOR_5", "name_TH": "วิชาเอกเลือก หรือ วิชาโท (5)", "name_EN": "Major Elective or Minor (5)", "credits": "3(3-0-6)", "type": "elective"},
                        {"id": "CS_ELEC_EXTRA", "name_TH": "วิชาเอกเลือก ว.คพ. เพิ่มเติม", "name_EN": "Major Elective Course", "credits": "3(3-0-6)", "type": "elective", "note": "Adjusted to fulfill 129 credits"}
                    ]
                }
            ],
            "project": [
                {
                    "semester": "Y1S1", "year": 1, "term": 1, "total_credits": 18,
                    "courses": [
                        {"id": "140104", "name_TH": "การเป็นพลเมือง", "name_EN": "Citizenship", "credits": "3(3-0-6)", "type": "gened"},
                        {"id": "204111", "name_TH": "การเขียนโปรแกรมเบื้องต้น", "name_EN": "Fundamentals of Programming", "credits": "3(2-2-5)", "type": "core"},
                        {"id": "206111", "name_TH": "แคลคูลัส 1", "name_EN": "Calculus 1", "credits": "3(3-0-6)", "type": "core"},
                        {"id": "206183", "name_TH": "โครงสร้างวิยุต", "name_EN": "Discrete Structure", "credits": "3(3-0-6)", "type": "core"},
                        {"id": "001101", "name_TH": "ภาษาอังกฤษพื้นฐาน 1 (หรือ ENGL 225)", "name_EN": "Fundamental English 1 (or ENGL 225)", "credits": "3(3-0-6)", "type": "gened"},
                        {"id": "GE_CREAT", "name_TH": "วิชาศึกษาทั่วไป (ทักษะการคิดสร้างสรรค์และนวัตกรรม)", "name_EN": "GE Course in Creativity & Innovation", "credits": "3(3-0-6)", "type": "gened"}
                    ]
                },
                {
                    "semester": "Y1S2", "year": 1, "term": 2, "total_credits": 18,
                    "courses": [
                        {"id": "202101", "name_TH": "ชีววิทยาพื้นฐาน 1", "name_EN": "Basic Biology 1", "credits": "3(3-0-6)", "type": "core"},
                        {"id": "204100", "name_TH": "เรื่องน่ารู้ทางปัญญาประดิษฐ์และดิจิทัล", "name_EN": "AI and Digital Essentials", "credits": "3(3-0-6)", "type": "core"},
                        {"id": "204115", "name_TH": "หลักการเขียนโปรแกรมเชิงฟังก์ชัน", "name_EN": "Principles of Functional Programming", "credits": "3(2-2-5)", "type": "core"},
                        {"id": "207187", "name_TH": "ฟิสิกส์ 1", "name_EN": "Physics 1", "credits": "3(3-0-6)", "type": "core"},
                        {"id": "001102", "name_TH": "ภาษาอังกฤษพื้นฐาน 2 (หรือวิชาที่กำหนด)", "name_EN": "Fundamental English 2 (or designated)", "credits": "3(3-0-6)", "type": "gened"},
                        {"id": "GE_ENTREP", "name_TH": "วิชาศึกษาทั่วไป (ทักษะการเป็นผู้ประกอบการ)", "name_EN": "GE Course in Entrepreneurial Skills", "credits": "3(3-0-6)", "type": "gened"}
                    ]
                },
                {
                    "semester": "Y2S1", "year": 2, "term": 1, "total_credits": 19,
                    "courses": [
                        {"id": "001225", "name_TH": "ภาษาอังกฤษสำหรับวิทยาศาสตร์และเทคโนโลยี", "name_EN": "English for Science and Technology", "credits": "3(3-0-6)", "type": "gened"},
                        {"id": "204231", "name_TH": "การจัดระบบและสถาปัตยกรรมคอมพิวเตอร์", "name_EN": "Computer Organization & Architecture", "credits": "3(2-2-5)", "type": "compulsory"},
                        {"id": "204255", "name_TH": "การเขียนโปรแกรมเชิงวัตถุและโครงสร้างข้อมูล", "name_EN": "OOP and Data Structures", "credits": "4(3-2-7)", "type": "core"},
                        {"id": "208269", "name_TH": "สถิติสำหรับวิทยาการคอมพิวเตอร์", "name_EN": "Statistics for Computer Science", "credits": "3(3-0-6)", "type": "core"},
                        {"id": "GE_DIGI", "name_TH": "วิชาศึกษาทั่วไป (ดิจิทัล/พลเมืองโลก/AI)", "name_EN": "GE Course (Digital/Global/AI)", "credits": "3(3-0-6)", "type": "gened"},
                        {"id": "ELEC_OR_MINOR_1", "name_TH": "วิชาเอกเลือก หรือ วิชาโท (1)", "name_EN": "Major Elective or Minor (1)", "credits": "3(3-0-6)", "type": "elective"}
                    ]
                },
                {
                    "semester": "Y2S2", "year": 2, "term": 2, "total_credits": 18,
                    "courses": [
                        {"id": "204212", "name_TH": "การพัฒนาเว็บแอปพลิเคชันแบบฟูลสแต๊ก", "name_EN": "Full-stack Web App Development", "credits": "3(2-2-5)", "type": "compulsory"},
                        {"id": "204232", "name_TH": "เครือข่ายคอมพิวเตอร์และเกณฑ์วิธี", "name_EN": "Computer Networks and Protocols", "credits": "3(3-0-6)", "type": "compulsory"},
                        {"id": "204271", "name_TH": "ปัญญาประดิษฐ์เบื้องต้น", "name_EN": "Intro to Artificial Intelligence", "credits": "3(2-2-5)", "type": "compulsory"},
                        {"id": "206324", "name_TH": "พีชคณิตเชิงเส้นประยุกต์", "name_EN": "Applied Linear Algebra", "credits": "3(3-0-6)", "type": "compulsory"},
                        {"id": "CS_ELEC_300_1", "name_TH": "วิชาเอกเลือก ว.คพ. ระดับ 300 หรือ 400", "name_EN": "Major Elective Level 300/400", "credits": "3(3-0-6)", "type": "elective"},
                        {"id": "ELEC_OR_MINOR_2", "name_TH": "วิชาเอกเลือก หรือ วิชาโท (2)", "name_EN": "Major Elective or Minor (2)", "credits": "3(3-0-6)", "type": "elective"}
                    ]
                },
                {
                    "semester": "Y3S1", "year": 3, "term": 1, "total_credits": 15,
                    "courses": [
                        {"id": "204321", "name_TH": "ระบบฐานข้อมูล", "name_EN": "Database Systems", "credits": "3(2-2-5)", "type": "compulsory"},
                        {"id": "204361", "name_TH": "วิศวกรรมซอฟต์แวร์", "name_EN": "Software Engineering", "credits": "3(3-0-6)", "type": "compulsory"},
                        {"id": "204451", "name_TH": "การออกแบบและการวิเคราะห์อัลกอริทึม", "name_EN": "Algorithm Design and Analysis", "credits": "3(3-0-6)", "type": "compulsory"},
                        {"id": "FREE_ELEC_1", "name_TH": "วิชาเลือกเสรี (1)", "name_EN": "Free Elective (1)", "credits": "3(3-0-6)", "type": "free"},
                        {"id": "ELEC_OR_MINOR_3", "name_TH": "วิชาเอกเลือก หรือ วิชาโท (3)", "name_EN": "Major Elective or Minor (3)", "credits": "3(3-0-6)", "type": "elective"}
                    ]
                },
                {
                    "semester": "Y3S2", "year": 3, "term": 2, "total_credits": 16,
                    "courses": [
                        {"id": "204306", "name_TH": "จริยธรรมสำหรับผู้ประกอบวิชาชีพคอมพิวเตอร์", "name_EN": "Ethics for Computer Professionals", "credits": "1(1-0-2)", "type": "compulsory"},
                        {"id": "204315", "name_TH": "การจัดระเบียบของภาษาโปรแกรม", "name_EN": "Organization of Programming Languages", "credits": "3(3-0-6)", "type": "compulsory"},
                        {"id": "CS_ELEC_300_2", "name_TH": "วิชาเอกเลือกระดับ 300/400 (เน้นโครงงาน 1)", "name_EN": "Major Elective (Project-based 1)", "credits": "3(3-0-6)", "type": "project_elective"},
                        {"id": "CS_ELEC_300_3", "name_TH": "วิชาเอกเลือกระดับ 300/400 (เน้นโครงงาน 2)", "name_EN": "Major Elective (Project-based 2)", "credits": "3(3-0-6)", "type": "project_elective"},
                        {"id": "ELEC_OR_MINOR_4", "name_TH": "วิชาเอกเลือก หรือ วิชาโท (4)", "name_EN": "Major Elective or Minor (4)", "credits": "3(3-0-6)", "type": "elective"},
                        {"id": "FREE_ELEC_2", "name_TH": "วิชาเลือกเสรี (2)", "name_EN": "Free Elective (2)", "credits": "3(3-0-6)", "type": "free"}
                    ]
                },
                {
                    "semester": "Y4S1", "year": 4, "term": 1, "total_credits": 15,
                    "courses": [
                        {"id": "CS_ELEC_400_P1", "name_TH": "วิชาเอกเลือกระดับ 400 (เน้นโครงงาน 3)", "name_EN": "Major Elective 400 (Project-based 3)", "credits": "3(3-0-6)", "type": "project_elective"},
                        {"id": "CS_ELEC_400_P2", "name_TH": "วิชาเอกเลือกระดับ 400 (เน้นโครงงาน 4)", "name_EN": "Major Elective 400 (Project-based 4)", "credits": "3(3-0-6)", "type": "project_elective"},
                        {"id": "CS_ELEC_400_P3", "name_TH": "วิชาเอกเลือกระดับ 400 (เน้นโครงงาน 5)", "name_EN": "Major Elective 400 (Project-based 5)", "credits": "3(3-0-6)", "type": "project_elective"},
                        {"id": "CS_ELEC_400_1", "name_TH": "วิชาเอกเลือกระดับ 400 (ทั่วไป 1)", "name_EN": "Major Elective Level 400 (1)", "credits": "3(3-0-6)", "type": "elective"},
                        {"id": "CS_ELEC_EXTRA_P", "name_TH": "วิชาเอกเลือกระดับ 300/400", "name_EN": "Major Elective Level 300/400", "credits": "3(3-0-6)", "type": "elective", "note": "Adjusted to fulfill 132 credits"}
                    ]
                },
                {
                    "semester": "Y4S2", "year": 4, "term": 2, "total_credits": 13,
                    "courses": [
                        {"id": "204497", "name_TH": "สัมมนาทางวิทยาการคอมพิวเตอร์", "name_EN": "Seminar in Computer Science", "credits": "1(1-0-2)", "type": "compulsory"},
                        {"id": "CS_ELEC_400_2", "name_TH": "วิชาเอกเลือกระดับ 400 (ทั่วไป 2)", "name_EN": "Major Elective Level 400 (2)", "credits": "3(3-0-6)", "type": "elective"},
                        {"id": "CS_ELEC_400_3", "name_TH": "วิชาเอกเลือกระดับ 400 (ทั่วไป 3)", "name_EN": "Major Elective Level 400 (3)", "credits": "3(3-0-6)", "type": "elective"},
                        {"id": "ELEC_OR_MINOR_5", "name_TH": "วิชาเอกเลือก หรือ วิชาโท (5)", "name_EN": "Major Elective or Minor (5)", "credits": "3(3-0-6)", "type": "elective"},
                        {"id": "CS_ELEC_EXTRA_P2", "name_TH": "วิชาเอกเลือกระดับ 300/400", "name_EN": "Major Elective Level 300/400", "credits": "3(3-0-6)", "type": "elective", "note": "Adjusted to fulfill 132 credits"}
                    ]
                }
            ]
        }
    }
    
    # Save complete JSON & JS for direct file:// protocol loading
    out_data = {
        "curriculum": curriculum_meta,
        "courses": final_courses
    }
    
    out_file = 'd:/Documents/curriculum69/data/curriculum69.json'
    with open(out_file, 'w', encoding='utf-8') as f:
        json.dump(out_data, f, ensure_ascii=False, indent=2)

    out_js = 'd:/Documents/curriculum69/data/curriculum69_data.js'
    with open(out_js, 'w', encoding='utf-8') as f:
        f.write('window.CURRICULUM_DATA = ' + json.dumps(out_data, ensure_ascii=False, indent=2) + ';\n')
        
    print(f"\nSUCCESS: Generated {out_file} and {out_js} with {len(final_courses)} courses and all curriculum structures!")

if __name__ == '__main__':
    build_dataset()
