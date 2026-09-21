/**
 * map.js - Logic for Page 2: Curriculum Map (8-Column Grid with Interactive Hover Dependency Highlighting)
 */

let selectedMapPlan = 'coop'; // 'coop' or 'project'
let selectedEnglishScore = 'below_b1'; // 'below_b1' or 'b1_plus'
let activeMobileSem = 'Y1S1';

document.addEventListener('DOMContentLoaded', async () => {
  const data = await fetchCurriculumData();
  if (!data) return;

  setupMapControls();
  renderCurriculumMap(data);

  onLanguageChange(() => {
    renderCurriculumMap(data);
  });
});

function setupMapControls() {
  // Plan switchers (Co-op vs Project)
  const planBtns = document.querySelectorAll('.map-plan-btn');
  planBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      planBtns.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      selectedMapPlan = btn.dataset.plan;
      if (curriculumData) renderCurriculumMap(curriculumData);
    });
  });

  // English Placement Score switchers (< B1 vs >= B1)
  const scoreBtns = document.querySelectorAll('.map-lang-score-btn');
  scoreBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      scoreBtns.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      selectedEnglishScore = btn.dataset.score;
      if (curriculumData) renderCurriculumMap(curriculumData);
    });
  });

  // Mobile semester tab buttons
  const semTabs = document.querySelectorAll('.sem-tab-btn');
  semTabs.forEach(tab => {
    tab.addEventListener('click', () => {
      semTabs.forEach(t => t.classList.remove('active'));
      tab.classList.add('active');
      activeMobileSem = tab.dataset.sem;
      updateMobileVisibleColumn();
    });
  });
}

function updateMobileVisibleColumn() {
  document.querySelectorAll('.map-column').forEach(col => {
    if (col.dataset.sem === activeMobileSem) {
      col.classList.add('active-mobile-col');
    } else {
      col.classList.remove('active-mobile-col');
    }
  });
}

function getAllPrerequisites(courseId, courses, visited = new Set()) {
  const result = new Set();
  const direct = courses[courseId]?.prerequisites || [];
  direct.forEach(pid => {
    if (!visited.has(pid)) {
      visited.add(pid);
      result.add(pid);
      const sub = getAllPrerequisites(pid, courses, visited);
      sub.forEach(sp => result.add(sp));
    }
  });
  return result;
}

function getAllPostRequisites(courseId, postMap, visited = new Set()) {
  const result = new Set();
  const direct = postMap[courseId] || [];
  direct.forEach(pid => {
    if (!visited.has(pid)) {
      visited.add(pid);
      result.add(pid);
      const sub = getAllPostRequisites(pid, postMap, visited);
      sub.forEach(sp => result.add(sp));
    }
  });
  return result;
}

function renderCurriculumMap(data) {
  const mapContainer = document.getElementById('curriculum-map-grid');
  if (!mapContainer) return;

  const studyPlan = data.curriculum.study_plans[selectedMapPlan];
  const postReqMap = getPostRequisitesMap(data.courses);

  mapContainer.innerHTML = '';

  studyPlan.forEach(sem => {
    const col = document.createElement('div');
    col.className = 'map-column';
    col.dataset.sem = sem.semester;
    if (sem.semester === activeMobileSem) {
      col.classList.add('active-mobile-col');
    }

    const semTitleTH = `ปี ${sem.year} เทอม ${sem.term}`;
    const semTitleEN = `Y${sem.year} Sem ${sem.term}`;
    const crText = `${sem.total_credits} ${currentLang === 'th' ? 'หน่วยกิต' : 'Credits'}`;

    let headerHtml = `
      <div class="map-col-header">
        <div class="map-col-title">${currentLang === 'th' ? semTitleTH : semTitleEN}</div>
        <div class="map-col-sub">${crText}</div>
      </div>
    `;

    // Process courses based on English placement score (< B1 vs B1+)
    let semCourses = sem.courses.map(c => ({ ...c }));
    if (selectedEnglishScore === 'b1_plus') {
      if (sem.semester === 'Y1S1') {
        const idx = semCourses.findIndex(c => c.id === '001101');
        if (idx !== -1) {
          semCourses[idx] = { id: '001225', type: 'gened' };
        }
      } else if (sem.semester === 'Y1S2') {
        const idx = semCourses.findIndex(c => c.id === '001102');
        if (idx !== -1) {
          semCourses[idx] = {
            id: 'GE_ENGL_1',
            name_TH: 'วิชาเลือกภาษาอังกฤษ',
            name_EN: 'English Elective',
            credits: '3(3-0-6)',
            type: 'gened'
          };
        }
      } else if (sem.semester === 'Y2S1') {
        const idx = semCourses.findIndex(c => c.id === '001225');
        if (idx !== -1) {
          semCourses[idx] = {
            id: 'GE_ENGL_2',
            name_TH: 'วิชาเลือกภาษาอังกฤษ',
            name_EN: 'English Elective',
            credits: '3(3-0-6)',
            type: 'gened'
          };
        }
      }
    }

    let cardsHtml = '';
    semCourses.forEach(c => {
      const realCourse = data.courses[c.id];
      const isReal = !!realCourse;
      const title = isReal ? (currentLang === 'th' ? realCourse.name_TH : realCourse.name_EN) : (currentLang === 'th' ? c.name_TH : c.name_EN);
      const type = isReal ? (realCourse.classification || c.type) : (c.type || 'gened');
      const credits = isReal ? realCourse.credits : (c.credits || '3 cr');

      const t1 = realCourse?.terms?.t1;
      const t2 = realCourse?.terms?.t2;

      let termsHtml = '';
      if (isReal && (t1 || t2)) {
        let pills = '';
        if (t1) pills += '<span class="term-pill t1-pill">T1</span>';
        if (t2) pills += '<span class="term-pill t2-pill">T2</span>';
        termsHtml = `<div class="card-terms-row">${pills}</div>`;
      }

      cardsHtml += `
        <div class="map-course-card" data-cid="${c.id}" data-type="${type}" tabindex="0">
          <div class="card-top">
            <span class="card-code">${c.id.includes('_') ? '•' : c.id}</span>
            <span class="card-credits">${credits}</span>
          </div>
          <div class="card-title">${title}</div>
          ${termsHtml}
        </div>
      `;
    });

    col.innerHTML = headerHtml + cardsHtml;
    mapContainer.appendChild(col);
  });

  // Attach hover & click listeners to course cards
  const allCards = mapContainer.querySelectorAll('.map-course-card');

  allCards.forEach(card => {
    const cid = card.dataset.cid;

    // Hover Highlight Handler (background/border color only, no resizing)
    card.addEventListener('mouseenter', () => {
      if (!data.courses[cid]) return;

      const prereqs = getAllPrerequisites(cid, data.courses);
      const postreqs = getAllPostRequisites(cid, postReqMap);

      allCards.forEach(otherCard => {
        const otherId = otherCard.dataset.cid;
        if (otherId === cid) {
          otherCard.classList.add('is-active');
        } else if (prereqs.has(otherId)) {
          otherCard.classList.add('is-prereq');
        } else if (postreqs.has(otherId)) {
          otherCard.classList.add('is-postreq');
        } else {
          otherCard.classList.add('is-dimmed');
        }
      });
    });

    card.addEventListener('mouseleave', () => {
      allCards.forEach(otherCard => {
        otherCard.classList.remove('is-active', 'is-prereq', 'is-postreq', 'is-dimmed');
      });
    });

    // Click handler to open inspector drawer
    card.addEventListener('click', () => {
      if (data.courses[cid]) {
        openCourseDrawer(cid);
      }
    });

    // Keyboard accessibility
    card.addEventListener('keydown', e => {
      if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault();
        if (data.courses[cid]) openCourseDrawer(cid);
      }
    });
  });

  updateMobileVisibleColumn();
}
