/**
 * tree.js - Logic for Page 3: CS Electives Course Tree (Clean List View with Filter Controls)
 */

let selectedLevelFilter = 'all'; // 'all', '300', '400'
let selectedTermFilter = 'all'; // 'all', 't1', 't2'
let searchQuery = '';

document.addEventListener('DOMContentLoaded', async () => {
  const data = await fetchCurriculumData();
  if (!data) return;

  setupTreeControls(data);
  renderTree(data);

  onLanguageChange(() => {
    renderTree(data);
  });
});

function setupTreeControls(data) {
  // Search input
  const searchInput = document.getElementById('tree-search-input');
  if (searchInput) {
    searchInput.addEventListener('input', e => {
      searchQuery = e.target.value.toLowerCase().trim();
      renderTree(data);
    });
  }

  // Level filter chips
  document.querySelectorAll('.filter-level-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.filter-level-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      selectedLevelFilter = btn.dataset.level;
      renderTree(data);
    });
  });

  // Term filter chips
  document.querySelectorAll('.filter-term-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.filter-term-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      selectedTermFilter = btn.dataset.term;
      renderTree(data);
    });
  });
}

// Check if course matches active filters
function matchesFilter(course) {
  if (selectedLevelFilter === '300' && !course.id.startsWith('2043')) return false;
  if (selectedLevelFilter === '400' && !course.id.startsWith('2044')) return false;

  if (selectedTermFilter === 't1' && !course.terms?.t1) return false;
  if (selectedTermFilter === 't2' && !course.terms?.t2) return false;

  if (searchQuery) {
    const codeMatch = course.id.toLowerCase().includes(searchQuery);
    const thMatch = (course.name_TH || '').toLowerCase().includes(searchQuery);
    const enMatch = (course.name_EN || '').toLowerCase().includes(searchQuery);
    const descMatch = ((course.desc_TH || '') + ' ' + (course.desc_EN || '')).toLowerCase().includes(searchQuery);
    if (!codeMatch && !thMatch && !enMatch && !descMatch) return false;
  }
  return true;
}

function renderTree(data) {
  renderListView(data);
}

/**
 * Render Electives List View
 */
function renderListView(data) {
  const projListEl = document.getElementById('list-project-courses');
  const nonProjListEl = document.getElementById('list-nonproject-courses');
  const projCountEl = document.getElementById('proj-count-badge');
  const nonProjCountEl = document.getElementById('nonproj-count-badge');

  if (!projListEl || !nonProjListEl) return;

  projListEl.innerHTML = '';
  nonProjListEl.innerHTML = '';

  let pCount = 0;
  let npCount = 0;

  // Filter 300 and 400 level CS electives
  const coursesList = Object.values(data.courses).filter(c => 
    c.id.startsWith('204') && 
    (c.id.startsWith('2043') || c.id.startsWith('2044')) &&
    c.classification !== 'compulsory' &&
    c.classification !== 'core'
  );

  // Sort by course code ascending
  coursesList.sort((a, b) => a.id.localeCompare(b.id));

  coursesList.forEach(c => {
    if (!matchesFilter(c)) return;

    const isProj = c.is_project_based || c.classification === 'project-elective';
    const card = document.createElement('div');
    card.className = 'list-course-card';

    const title = currentLang === 'th' ? c.name_TH : c.name_EN;
    const t1 = c.terms?.t1;
    const t2 = c.terms?.t2;

    let termPillsHtml = '';
    if (t1) termPillsHtml += '<span class="term-pill t1-pill">T1</span>';
    if (t2) termPillsHtml += '<span class="term-pill t2-pill">T2</span>';
    if (!t1 && !t2) {
      termPillsHtml = `<span style="font-size:0.68rem; color:var(--text-muted);">${currentLang === 'th' ? 'ไม่เปิดสอนปี 69' : 'Not offered 2026'}</span>`;
    }

    card.innerHTML = `
      <div style="display:flex; justify-content:space-between; align-items:center;">
        <span style="font-family:monospace; font-weight:800; color:var(--cmu-purple); font-size:1.05rem;">${c.id}</span>
        <span style="font-size:0.75rem; font-weight:700; color:var(--text-muted);">${c.credits || '3 cr'}</span>
      </div>
      <div style="font-size:0.92rem; font-weight:700; color:var(--text-primary); line-height:1.3;">
        ${title}
      </div>
      <div style="font-size:0.8rem; color:var(--text-secondary); background:var(--bg-surface-elevated); padding:0.4rem 0.6rem; border-radius:6px;">
        <span style="font-weight:700; color:var(--text-muted);">${currentLang === 'th' ? 'เงื่อนไข:' : 'Prereq:'}</span> ${c.official_prereq || (currentLang === 'th' ? 'ไม่มี' : 'None')}
      </div>
      <div style="display:flex; justify-content:space-between; align-items:center; margin-top:4px;">
        <span style="font-size:0.75rem; font-weight:700; color: ${isProj ? 'var(--cat-proj-elective)' : 'var(--cat-nonproj-elective)'};">
          ${isProj ? (currentLang === 'th' ? '✓ มุ่งเน้นโครงงาน' : '✓ Project-based') : (currentLang === 'th' ? '• ไม่เน้นโครงงาน' : '• Non-project')}
        </span>
        <div style="display:flex; gap:4px; align-items:center;">
          ${termPillsHtml}
        </div>
      </div>
    `;

    card.addEventListener('click', () => openCourseDrawer(c.id));

    if (isProj) {
      projListEl.appendChild(card);
      pCount++;
    } else {
      nonProjListEl.appendChild(card);
      npCount++;
    }
  });

  if (projCountEl) projCountEl.textContent = `${pCount} ${currentLang === 'th' ? 'วิชา' : 'courses'}`;
  if (nonProjCountEl) nonProjCountEl.textContent = `${npCount} ${currentLang === 'th' ? 'วิชา' : 'courses'}`;
}
