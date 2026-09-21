/**
 * overview.js - Logic for Page 1: Degree Requirements (Summary & Category Breakdown Tables)
 * Follows UIUC degree requirements catalog design
 */

let selectedPlan = 'coop'; // 'coop' or 'project'
let selectedMinor = 'minor'; // 'minor' or 'no_minor'

document.addEventListener('DOMContentLoaded', async () => {
  const data = await fetchCurriculumData();
  if (!data) return;

  setupTrackControls();
  renderOverview(data);

  onLanguageChange(() => {
    renderOverview(data);
  });
});

function setupTrackControls() {
  const planBtns = document.querySelectorAll('.plan-toggle-btn');
  const minorBtns = document.querySelectorAll('.minor-toggle-btn');

  planBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      planBtns.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      selectedPlan = btn.dataset.plan;
      if (curriculumData) renderOverview(curriculumData);
    });
  });

  minorBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      minorBtns.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      selectedMinor = btn.dataset.minor;
      if (curriculumData) renderOverview(curriculumData);
    });
  });
}

function renderOverview(data) {
  const planKey = `${selectedPlan}_${selectedMinor}`;
  const planMeta = data.curriculum.plans[planKey];
  if (!planMeta) return;

  // Render Plan Title
  const planTitleEl = document.getElementById('selected-plan-title');
  if (planTitleEl) {
    planTitleEl.textContent = currentLang === 'th' ? planMeta.name_TH : planMeta.name_EN;
  }

  // Render Stat Cards
  const totalCrEl = document.getElementById('stat-total-credits');
  if (totalCrEl) totalCrEl.textContent = planMeta.total_credits;

  const geCrEl = document.getElementById('stat-ge-credits');
  if (geCrEl) geCrEl.textContent = 24;

  const coreCrEl = document.getElementById('stat-core-credits');
  if (coreCrEl) coreCrEl.textContent = 25;

  // 1. Overall Summary Table
  const tableBody = document.getElementById('categories-table-body');
  if (tableBody) {
    tableBody.innerHTML = '';
    planMeta.categories.forEach(cat => {
      const tr = document.createElement('tr');
      const catName = currentLang === 'th' ? cat.name_TH : cat.name_EN;
      const note = cat.note ? `<div style="font-size:0.75rem; color:var(--text-muted); margin-top:2px;">• ${cat.note}</div>` : '';
      tr.innerHTML = `
        <td style="font-weight:600;">
          <a href="#section-${cat.id || ''}" style="color:inherit; text-decoration:underline; text-decoration-color:var(--border-medium);">${catName}</a>
          ${note}
        </td>
        <td style="text-align:right; font-weight:700; font-family:monospace; font-size:1.05rem; color:var(--cmu-purple);">${cat.credits}</td>
      `;
      tableBody.appendChild(tr);
    });

    // Summary Total Row
    const totalTr = document.createElement('tr');
    totalTr.style.background = 'var(--bg-surface-elevated)';
    totalTr.innerHTML = `
      <td style="font-weight:800; font-size:1rem; color:var(--cmu-purple);">
        ${currentLang === 'th' ? 'จำนวนหน่วยกิตรวมตลอดหลักสูตร (Total Required Credits)' : 'Total Required Credits'}
      </td>
      <td style="text-align:right; font-weight:800; font-family:monospace; font-size:1.2rem; color:var(--cmu-purple);">
        ${planMeta.total_credits}
      </td>
    `;
    tableBody.appendChild(totalTr);
  }

  // 2. Individual Category Course Tables
  renderCategoryTables(data);
}

// Global state for GE Language placement score
window.selectedGeLangScore = window.selectedGeLangScore || 'below_b1';

window.setGeLangScore = function(score) {
  window.selectedGeLangScore = score;
  if (window.CURRICULUM_DATA) {
    renderCategoryTables(window.CURRICULUM_DATA);
  }
};

function getTermBadgesHtml(realCourse) {
  if (!realCourse || !realCourse.terms) {
    return '<span style="color:var(--text-muted); font-size:0.75rem;">—</span>';
  }
  const t1 = realCourse.terms.t1;
  const t2 = realCourse.terms.t2;
  if (!t1 && !t2) {
    return '<span style="color:var(--text-muted); font-size:0.75rem;">—</span>';
  }
  let pills = '';
  if (t1) pills += '<span class="term-pill t1-pill">T1</span>';
  if (t2) pills += '<span class="term-pill t2-pill">T2</span>';
  return `<div class="card-terms-row" style="justify-content:center; margin:0;">${pills}</div>`;
}

function renderCourseRow(courseId, customData = {}, showTerms = true, allCourses = {}) {
  const isReal = !!allCourses[courseId];
  const realObj = allCourses[courseId] || {};
  const name = currentLang === 'th' ? (realObj.name_TH || customData.name_TH || courseId) : (realObj.name_EN || customData.name_EN || courseId);
  const credits = realObj.credits || customData.credits || '3(3-0-6)';
  const badgeHtml = customData.badge ? `<span class="meta-pill" style="font-size:0.7rem; margin-left:6px; background:var(--cmu-purple-subtle); color:var(--cmu-purple); border:1px solid var(--border-medium);">${customData.badge}</span>` : '';

  return `
    <tr>
      <td style="font-family:monospace; font-weight:800; width:130px;">
        ${isReal 
          ? `<a href="javascript:void(0)" onclick="openCourseDrawer('${courseId}')" style="color:var(--cmu-purple); text-decoration:underline;">${courseId}</a>` 
          : `<span style="color:var(--text-muted);">${courseId}</span>`}
      </td>
      <td>
        <span style="font-weight:600;">${name}</span>
        ${badgeHtml}
      </td>
      <td style="text-align:right; font-family:monospace; font-weight:600; white-space:nowrap; width:110px;">
        ${credits}
      </td>
      ${showTerms ? `<td style="text-align:center; width:90px;">${getTermBadgesHtml(realObj)}</td>` : ''}
    </tr>
  `;
}

function renderGenedSectionHtml(data) {
  const allCourses = data.courses || {};
  const genedStruct = data.curriculum?.category_course_lists?.gened_structure;
  if (!genedStruct) return '';

  const isB1Plus = (window.selectedGeLangScore === 'b1_plus');
  const langTrack = genedStruct.language.options[window.selectedGeLangScore || 'below_b1'];

  // 1. Language Literacy Table
  let langRowsHtml = '';
  if (!isB1Plus) {
    // Below B1: 3 prescribed courses (001101, 001102, 001225)
    (langTrack.courses || []).forEach(c => {
      langRowsHtml += renderCourseRow(c.id, {
        badge: currentLang === 'th' ? 'วิชาบังคับ' : 'Required',
        name_TH: c.name_TH,
        name_EN: c.name_EN
      }, true, allCourses);
    });
  } else {
    // B1+: 1 Required course (001225)
    (langTrack.required_courses || []).forEach(c => {
      langRowsHtml += renderCourseRow(c.id, {
        badge: currentLang === 'th' ? 'วิชาบังคับ (3 นก.)' : 'Required (3 cr)',
        name_TH: c.name_TH,
        name_EN: c.name_EN
      }, true, allCourses);
    });
  }

  // B1+ Elective Courses Expandable
  let b1ElectivesHtml = '';
  if (isB1Plus && langTrack.elective_courses) {
    let electivesRows = '';
    langTrack.elective_courses.forEach(c => {
      electivesRows += renderCourseRow(c.id, { name_TH: c.name_TH, name_EN: c.name_EN }, true, allCourses);
    });

    b1ElectivesHtml = `
      <details class="ge-expandable-card" open style="margin-top:0.65rem;">
        <summary class="ge-expand-summary">
          <div class="ge-expand-left">
            <span class="ge-expand-badge" style="background:#059669; color:#FFF; border:none;">
              ${currentLang === 'th' ? 'วิชาเลือก: เลือก 6 หน่วยกิต' : 'Elective: Choose 6 credits'}
            </span>
            <span class="ge-expand-title">
              ${currentLang === 'th' ? 'รายชื่อวิชาเลือกภาษาอังกฤษสำหรับกลุ่ม B1+ (คลิกเพื่อย่อ/ขยาย)' : 'English Electives for B1+ Group (Click to expand/collapse)'}
            </span>
          </div>
          <span class="ge-expand-icon">▾</span>
        </summary>
        <div class="ge-expand-body">
          <div class="ge-directive-text" style="color:var(--text-primary);">
            ⚠️ <strong>${currentLang === 'th' ? 'เกณฑ์การเลือก:' : 'Selection Rule:'}</strong> 
            ${currentLang === 'th' 
              ? 'ให้นักศึกษาเลือกเรียน 6 หน่วยกิต (2 กระบวนวิชา) จากกระบวนวิชาต่อไปนี้ หรือเทียบผลการสอบมาตรฐานภาษาอังกฤษตามประกาศของมหาวิทยาลัย' 
              : 'Choose 6 credits (2 courses) from the following list, or submit an equivalent standardized English proficiency test score:'}
          </div>
          <div style="overflow-x:auto;">
            <table class="custom-table">
              <thead>
                <tr>
                  <th style="width:130px;">${currentLang === 'th' ? 'รหัสวิชา' : 'Course Code'}</th>
                  <th>${currentLang === 'th' ? 'ชื่อกระบวนวิชา (Course Title)' : 'Course Title'}</th>
                  <th style="text-align:right; width:110px;">${currentLang === 'th' ? 'หน่วยกิต' : 'Credits'}</th>
                  <th style="text-align:center; width:90px;">${currentLang === 'th' ? 'เทอมเปิดสอน' : 'Terms'}</th>
                </tr>
              </thead>
              <tbody>
                ${electivesRows}
              </tbody>
            </table>
          </div>
        </div>
      </details>
    `;
  }

  // 2. Fixed GE Requirements (Digital & Global)
  let fixedRowsHtml = '';
  (genedStruct.digital.courses || []).forEach(c => {
    fixedRowsHtml += renderCourseRow(c.id, {
      badge: currentLang === 'th' ? 'ทักษะดิจิทัล (บังคับ)' : 'Digital Literacy (Req)',
      name_TH: c.name_TH,
      name_EN: c.name_EN
    }, true, allCourses);
  });
  (genedStruct.global.courses || []).forEach(c => {
    fixedRowsHtml += renderCourseRow(c.id, {
      badge: currentLang === 'th' ? 'พลเมืองโลก (บังคับ)' : 'Global Citizen (Req)',
      name_TH: c.name_TH,
      name_EN: c.name_EN
    }, true, allCourses);
  });

  // 3. Expandable GE Elective Groups Helper
  function renderGeExpandableGroup(groupObj, badgeTextTH, badgeTextEN) {
    let rows = '';
    (groupObj.courses || []).forEach(c => {
      rows += renderCourseRow(c.id, { name_TH: c.name_TH, name_EN: c.name_EN }, true, allCourses);
    });

    const count = (groupObj.courses || []).length;
    const title = currentLang === 'th' ? groupObj.title_TH : groupObj.title_EN;
    const directive = currentLang === 'th' ? groupObj.directive_TH : groupObj.directive_EN;

    return `
      <details class="ge-expandable-card">
        <summary class="ge-expand-summary">
          <div class="ge-expand-left">
            <span class="ge-expand-badge">
              ${currentLang === 'th' ? badgeTextTH : badgeTextEN}
            </span>
            <span class="ge-expand-title">${title} (${count} ${currentLang === 'th' ? 'วิชาที่เปิดให้เลือก' : 'available courses'})</span>
          </div>
          <span class="ge-expand-icon">▾</span>
        </summary>
        <div class="ge-expand-body">
          <div class="ge-directive-text">
            📋 <strong>${directive}</strong>
          </div>
          <div style="overflow-x:auto;">
            <table class="custom-table">
              <thead>
                <tr>
                  <th style="width:130px;">${currentLang === 'th' ? 'รหัสวิชา' : 'Course Code'}</th>
                  <th>${currentLang === 'th' ? 'ชื่อกระบวนวิชา (Course Title)' : 'Course Title'}</th>
                  <th style="text-align:right; width:110px;">${currentLang === 'th' ? 'หน่วยกิต' : 'Credits'}</th>
                  <th style="text-align:center; width:90px;">${currentLang === 'th' ? 'เทอมเปิดสอน' : 'Terms'}</th>
                </tr>
              </thead>
              <tbody>
                ${rows}
              </tbody>
            </table>
          </div>
        </div>
      </details>
    `;
  }

  const creativityHtml = renderGeExpandableGroup(
    genedStruct.creativity,
    'เลือก 3 หน่วยกิต',
    'Choose 3 credits'
  );

  const entrepreneurHtml = renderGeExpandableGroup(
    genedStruct.entrepreneur,
    'เลือก 3 หน่วยกิต',
    'Choose 3 credits'
  );

  const digitalGlobalAiHtml = renderGeExpandableGroup(
    genedStruct.digital_global_ai,
    'เลือก 3 หน่วยกิต',
    'Choose 3 credits'
  );

  return `
    <section class="section-block" id="section-gened">
      <div class="section-title-wrap">
        <div>
          <h2 class="section-title">${currentLang === 'th' ? 'หมวดวิชาศึกษาทั่วไป (General Education)' : 'General Education Courses'}</h2>
          <div style="font-size:0.88rem; color:var(--text-secondary); margin-top:3px;">
            ${currentLang === 'th'
              ? 'รวม 24 หน่วยกิต เพื่อพัฒนาทักษะการเรียนรู้ตลอดชีวิต ภาษา การสื่อสาร การคิดสร้างสรรค์ เทคโนโลยีดิจิทัล และความเป็นพลเมือง'
              : 'Total 24 credits covering Language, Digital Literacy, Global Citizenship, Creativity & Innovation, and Entrepreneurial Skills.'}
          </div>
        </div>
        <div class="sem-credits-badge" style="font-size:0.85rem; padding:0.4rem 0.85rem; white-space:nowrap;">
          24 ${currentLang === 'th' ? 'หน่วยกิต' : 'Credits'}
        </div>
      </div>

      <!-- 1. Language Literacy Subgroup -->
      <div class="ge-subgroup-title">
        <span>🗣️</span>
        <span>${currentLang === 'th' ? '1. กลุ่มวิชาด้านทักษะทางการสื่อสารและภาษา (Language Literacy) - 9 หน่วยกิต' : '1. Language Literacy - 9 Credits'}</span>
      </div>

      <!-- Placement Score Selector Toolbar -->
      <div class="ge-lang-toolbar">
        <div class="ge-lang-label">
          <span>🎯 ${currentLang === 'th' ? 'เลือกแผนตามผลสอบวัดระดับภาษาอังกฤษ (e-Pro / CEFR Placement):' : 'Select track by English proficiency placement (e-Pro):'}</span>
        </div>
        <div class="ge-lang-btns">
          <button class="ge-lang-btn ${!isB1Plus ? 'active' : ''}" onclick="setGeLangScore('below_b1')">
            <span>&lt; B1</span> (${currentLang === 'th' ? 'ไม่ถึง B1' : 'Below B1'})
          </button>
          <button class="ge-lang-btn ${isB1Plus ? 'active' : ''}" onclick="setGeLangScore('b1_plus')">
            <span>&ge; B1 (B1+)</span> (${currentLang === 'th' ? 'ตั้งแต่ B1 ขึ้นไป' : 'B1 or Higher'})
          </button>
        </div>
      </div>

      <div style="font-size:0.84rem; color:var(--text-secondary); margin-bottom:0.65rem; font-style:italic;">
        ${currentLang === 'th' ? langTrack.description_TH : langTrack.description_EN}
      </div>

      <div style="overflow-x:auto;">
        <table class="custom-table">
          <thead>
            <tr>
              <th style="width:130px;">${currentLang === 'th' ? 'รหัสวิชา' : 'Course Code'}</th>
              <th>${currentLang === 'th' ? 'ชื่อกระบวนวิชา (Course Title)' : 'Course Title'}</th>
              <th style="text-align:right; width:110px;">${currentLang === 'th' ? 'หน่วยกิต' : 'Credits'}</th>
              <th style="text-align:center; width:90px;">${currentLang === 'th' ? 'เทอมเปิดสอน' : 'Terms'}</th>
            </tr>
          </thead>
          <tbody>
            ${langRowsHtml}
          </tbody>
        </table>
      </div>

      ${b1ElectivesHtml}

      <!-- 2. Compulsory Digital & Global Literacy Subgroup -->
      <div class="ge-subgroup-title">
        <span>🌐</span>
        <span>${currentLang === 'th' ? '2. รายวิชาศึกษาทั่วไปบังคับ (Digital Literacy & Global Citizen) - 6 หน่วยกิต' : '2. Required Digital & Global Literacy - 6 Credits'}</span>
      </div>
      <div style="overflow-x:auto;">
        <table class="custom-table">
          <thead>
            <tr>
              <th style="width:130px;">${currentLang === 'th' ? 'รหัสวิชา' : 'Course Code'}</th>
              <th>${currentLang === 'th' ? 'ชื่อกระบวนวิชา (Course Title)' : 'Course Title'}</th>
              <th style="text-align:right; width:110px;">${currentLang === 'th' ? 'หน่วยกิต' : 'Credits'}</th>
              <th style="text-align:center; width:90px;">${currentLang === 'th' ? 'เทอมเปิดสอน' : 'Terms'}</th>
            </tr>
          </thead>
          <tbody>
            ${fixedRowsHtml}
          </tbody>
        </table>
      </div>

      <!-- 3. Expandable GE Elective Subgroups -->
      <div class="ge-subgroup-title">
        <span>💡</span>
        <span>${currentLang === 'th' ? '3. กลุ่มวิชาศึกษาทั่วไปเลือกตามทักษะ (GE Skill Electives) - 9 หน่วยกิต (3 กลุ่มวิชา)' : '3. GE Skill Electives - 9 Credits (3 Groups)'}</span>
      </div>
      <div style="font-size:0.84rem; color:var(--text-muted); margin-bottom:0.5rem;">
        ${currentLang === 'th' ? 'คลิกที่แต่ละกลุ่มวิชาเพื่อดูรายชื่อกระบวนวิชาที่เปิดให้เลือกเรียน (Expandable):' : 'Click each category below to expand available course options:'}
      </div>

      ${creativityHtml}
      ${entrepreneurHtml}
      ${digitalGlobalAiHtml}
    </section>
  `;
}

function renderCategoryTables(data) {
  const container = document.getElementById('category-tables-container');
  if (!container) return;

  const categoryLists = data.curriculum.category_course_lists || {};
  const allCourses = data.courses || {};

  // Elective categorization - strictly 300 and 400 level courses only
  const projElectives = [];
  const nonProjElectives = [];

  Object.values(allCourses).forEach(c => {
    if (!c.id.startsWith('204') && !c.id.startsWith('206')) return;
    
    // STRICT RULE: Major electives must only be 300 and 400 level courses (>= 300)
    const numPart = parseInt(c.id.slice(3), 10);
    if (isNaN(numPart) || numPart < 300) return;

    // Exclude compulsory courses
    const isComp = ['204306', '204315', '204321', '204361', '204451', '204497', '204496', '206324'].includes(c.id);
    if (isComp) return;

    if (c.is_project_based || c.classification === 'project-elective') {
      projElectives.push(c);
    } else {
      nonProjElectives.push(c);
    }
  });

  // Sort electives by id
  projElectives.sort((a, b) => a.id.localeCompare(b.id));
  nonProjElectives.sort((a, b) => a.id.localeCompare(b.id));

  // Determine Compulsory courses for selected plan
  const compCourses = (categoryLists.compulsory || []).filter(c => {
    if (c.id === '204496' && selectedPlan !== 'coop') return false;
    return true;
  });

  const compCredits = selectedPlan === 'coop' ? 35 : 29;

  // Render General Education section with dedicated interactive layout
  let finalHtml = renderGenedSectionHtml(data);

  // Remaining Section Configurations
  const remainingSections = [
    {
      id: 'core',
      title_TH: 'วิชาแกน (Core Courses)',
      title_EN: 'Core Courses',
      credits: '25 หน่วยกิต',
      description_TH: 'กระบวนวิชาพื้นฐานทางคณิตศาสตร์ สถิติ วิทยาศาสตร์ และรากฐานการเขียนโปรแกรมที่นักศึกษาทุกคนต้องเรียนร่วมกัน',
      description_EN: 'Foundational courses in mathematics, statistics, natural sciences, and core computing required of all students.',
      courses: categoryLists.core || [],
      showTerms: true
    },
    {
      id: 'compulsory_shared',
      title_TH: `วิชาเอกบังคับ (Major Compulsory Courses) - ${selectedPlan === 'coop' ? 'แผนสหกิจศึกษา' : 'แผนมุ่งเน้นโครงงาน'}`,
      title_EN: `Major Compulsory Courses - ${selectedPlan === 'coop' ? 'Co-op Plan' : 'Project-oriented Plan'}`,
      credits: `${compCredits} หน่วยกิต`,
      description_TH: selectedPlan === 'coop' 
        ? 'วิชาเอกบังคับร่วม 29 หน่วยกิต และวิชาเอกบังคับประจำแผนสหกิจศึกษา (204496 สหกิจศึกษา) 6 หน่วยกิต รวม 35 หน่วยกิต'
        : 'วิชาเอกบังคับร่วม 29 หน่วยกิต (แผนมุ่งเน้นโครงงานไม่มีวิชาบังคับประจำแผน แต่เพิ่มหน่วยกิตในวิชาเอกเลือก)',
      description_EN: selectedPlan === 'coop'
        ? '29 credits of shared compulsory courses plus 6 credits of Cooperative Education (204496), totaling 35 credits.'
        : '29 credits of shared compulsory courses (Project plan replaces co-op with 9 additional major elective credits).',
      courses: compCourses,
      showTerms: true
    },
    {
      id: 'major_electives_proj',
      title_TH: 'วิชาเอกเลือก - กลุ่มกระบวนวิชาที่มุ่งเน้นโครงงาน (Project-oriented Electives - Level 300 & 400)',
      title_EN: 'Major Electives - Project-oriented Courses (Level 300 & 400)',
      credits: selectedPlan === 'project' ? 'ต้องเรียนอย่างน้อย 15 หน่วยกิต' : 'เลือกเรียนตามแผน',
      description_TH: 'กระบวนวิชาระดับ 300 และ 400 ที่มุ่งเน้นการลงมือพัฒนาโครงงานจริง (แผนมุ่งเน้นโครงงานต้องลงกลุ่มนี้อย่างน้อย 15 หน่วยกิต)',
      description_EN: 'Courses emphasizing hands-on project implementations. Students in the Project-oriented plan must take at least 15 credits from this group.',
      courses: projElectives,
      showTerms: true
    },
    {
      id: 'major_electives_nonproj',
      title_TH: 'วิชาเอกเลือก - กลุ่มกระบวนวิชาที่ไม่มุ่งเน้นโครงงาน (Non-project Electives - Level 300 & 400)',
      title_EN: 'Major Electives - Non-project Courses (Level 300 & 400)',
      credits: 'เลือกเรียนตามแผน',
      description_TH: 'กระบวนวิชาเอกเลือกระดับ 300 และ 400 ที่เน้นทฤษฎี ระบบ อัลกอริทึม และองค์ความรู้เฉพาะทางของวิทยาการคอมพิวเตอร์',
      description_EN: 'Courses covering specialized theories, systems, algorithmic principles, and advanced computer science foundations.',
      courses: nonProjElectives,
      showTerms: true
    },
    {
      id: 'minor',
      title_TH: selectedMinor === 'minor' ? 'หมวดวิชาโท (Academic Minor)' : 'กลุ่มวิชาเอกเลือก ว.คพ. เพิ่มเติม (แทนวิชาโท)',
      title_EN: selectedMinor === 'minor' ? 'Academic Minor' : 'Additional CS Electives (In lieu of Minor)',
      credits: '15 หน่วยกิต',
      description_TH: selectedMinor === 'minor'
        ? 'นักศึกษาที่ต้องการเรียนวิชาโท สามารถเลือกเรียนวิชาโทสาขาใดๆ ในมหาวิทยาลัยเชียงใหม่ โดยความเห็นชอบของอาจารย์ที่ปรึกษา ไม่น้อยกว่า 15 หน่วยกิต'
        : 'นักศึกษาที่ไม่ต้องการเรียนวิชาโท ให้เลือกเรียนกระบวนวิชาวิทยาการคอมพิวเตอร์ระดับ 300 หรือ 400 เพิ่มเติมอีกไม่น้อยกว่า 15 หน่วยกิต',
      description_EN: selectedMinor === 'minor'
        ? 'Students pursuing an academic minor choose at least 15 credits from any minor program offered by any department with advisor approval.'
        : 'Students opting out of a minor must complete 15 additional credits of CS courses at the 300 or 400 level.',
      courses: [],
      note: selectedMinor === 'minor' ? '15 Credits in Minor field' : '15 Credits in 300-400 CS Electives'
    },
    {
      id: 'free_electives',
      title_TH: 'หมวดวิชาเลือกเสรี (Free Electives)',
      title_EN: 'Free Electives',
      credits: '6 หน่วยกิต',
      description_TH: 'นักศึกษาสามารถเลือกเรียนกระบวนวิชาใดๆ ที่เปิดสอนในมหาวิทยาลัยเชียงใหม่ตามความสนใจ โดยความเห็นชอบของอาจารย์ที่ปรึกษา ไม่น้อยกว่า 6 หน่วยกิต',
      description_EN: 'At least 6 credits of free elective courses offered by any department across the university.',
      courses: [],
      note: '6 Credits Free Electives'
    }
  ];

  remainingSections.forEach(sec => {
    const title = currentLang === 'th' ? sec.title_TH : sec.title_EN;
    const desc = currentLang === 'th' ? sec.description_TH : sec.description_EN;

    let rowsHtml = '';
    if (sec.courses.length > 0) {
      sec.courses.forEach(c => {
        rowsHtml += renderCourseRow(c.id, {
          name_TH: c.name_TH,
          name_EN: c.name_EN,
          credits: c.credits,
          badge: c.group ? c.group : ''
        }, sec.showTerms, allCourses);
      });
    } else {
      rowsHtml = `
        <tr>
          <td colspan="4" style="text-align:center; padding:1.5rem; color:var(--text-secondary); font-style:italic;">
            ${sec.note || (currentLang === 'th' ? 'เลือกเรียนตามเกณฑ์ที่กำหนด' : 'Select courses based on curriculum guidelines')}
          </td>
        </tr>
      `;
    }

    finalHtml += `
      <section class="section-block" id="section-${sec.id}">
        <div class="section-title-wrap">
          <div>
            <h2 class="section-title">${title}</h2>
            <div style="font-size:0.88rem; color:var(--text-secondary); margin-top:3px;">${desc}</div>
          </div>
          <div class="sem-credits-badge" style="font-size:0.85rem; padding:0.4rem 0.85rem; white-space:nowrap;">
            ${sec.credits}
          </div>
        </div>
        <div style="overflow-x:auto;">
          <table class="custom-table">
            <thead>
              <tr>
                <th style="width:130px;">${currentLang === 'th' ? 'รหัสวิชา' : 'Course Code'}</th>
                <th>${currentLang === 'th' ? 'ชื่อกระบวนวิชา (Course Title)' : 'Course Title'}</th>
                <th style="text-align:right; width:110px;">${currentLang === 'th' ? 'หน่วยกิต' : 'Credits'}</th>
                ${sec.showTerms ? `<th style="text-align:center; width:90px;">${currentLang === 'th' ? 'เทอมเปิดสอน' : 'Terms'}</th>` : ''}
              </tr>
            </thead>
            <tbody>
              ${rowsHtml}
            </tbody>
          </table>
        </div>
      </section>
    `;
  });

  container.innerHTML = finalHtml;
}
