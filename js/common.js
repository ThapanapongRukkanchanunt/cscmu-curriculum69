/**
 * common.js - Shared utilities, State Management, Navigation, and Course Inspector Drawer
 */

let curriculumData = null;
let currentLang = localStorage.getItem('cmu_cs_lang') || 'th';
let currentTheme = localStorage.getItem('cmu_cs_theme') || 'light';

// Listeners for lang changes
const langChangeCallbacks = [];

function onLanguageChange(fn) {
  langChangeCallbacks.push(fn);
}

// Fetch curriculum JSON or fallback to preloaded window.CURRICULUM_DATA for file:// protocol
async function fetchCurriculumData() {
  if (curriculumData) return curriculumData;
  if (typeof window !== 'undefined' && window.CURRICULUM_DATA) {
    curriculumData = window.CURRICULUM_DATA;
    return curriculumData;
  }
  try {
    const res = await fetch('data/curriculum69.json');
    if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);
    curriculumData = await res.json();
    return curriculumData;
  } catch (err) {
    console.error('Failed to load curriculum data:', err);
    return null;
  }
}

// Theme Management
function initTheme() {
  document.documentElement.setAttribute('data-theme', currentTheme);
  const themeBtn = document.getElementById('theme-toggle-btn');
  if (themeBtn) {
    themeBtn.innerHTML = currentTheme === 'dark' ? '☀️' : '🌙';
    themeBtn.setAttribute('title', currentTheme === 'dark' ? 'Switch to Light Mode' : 'Switch to Dark Mode');
  }
}

function toggleTheme() {
  currentTheme = currentTheme === 'dark' ? 'light' : 'dark';
  localStorage.setItem('cmu_cs_theme', currentTheme);
  initTheme();
}

// Language Management
function initLanguage() {
  document.documentElement.setAttribute('lang', currentLang);
  const langBtn = document.getElementById('lang-toggle-btn');
  if (langBtn) {
    langBtn.textContent = currentLang === 'th' ? 'EN' : 'TH';
    langBtn.setAttribute('title', currentLang === 'th' ? 'Switch to English' : 'เปลี่ยนเป็นภาษาไทย');
  }
  updateDOMText();
}

function toggleLanguage() {
  currentLang = currentLang === 'th' ? 'en' : 'th';
  localStorage.setItem('cmu_cs_lang', currentLang);
  initLanguage();
  if (currentDrawerCourseId) {
    openCourseDrawer(currentDrawerCourseId);
  }
  langChangeCallbacks.forEach(fn => fn(currentLang));
}

function updateDOMText() {
  document.querySelectorAll('[data-th][data-en]').forEach(el => {
    el.textContent = currentLang === 'th' ? el.getAttribute('data-th') : el.getAttribute('data-en');
  });
  document.querySelectorAll('[data-placeholder-th][data-placeholder-en]').forEach(el => {
    el.placeholder = currentLang === 'th' ? el.getAttribute('data-placeholder-th') : el.getAttribute('data-placeholder-en');
  });
}

// Build post-requisites map
function getPostRequisitesMap(courses) {
  const postReqs = {};
  Object.keys(courses).forEach(cid => {
    postReqs[cid] = [];
  });
  Object.entries(courses).forEach(([cid, c]) => {
    const prereqs = c.prerequisites || [];
    prereqs.forEach(preId => {
      if (!postReqs[preId]) postReqs[preId] = [];
      postReqs[preId].push(cid);
    });
  });
  return postReqs;
}

// Setup Shared Header & Navigation
function setupSharedHeader() {
  // Theme toggle
  const themeBtn = document.getElementById('theme-toggle-btn');
  if (themeBtn) themeBtn.addEventListener('click', toggleTheme);

  // Lang toggle
  const langBtn = document.getElementById('lang-toggle-btn');
  if (langBtn) langBtn.addEventListener('click', toggleLanguage);

  // Active page link
  const currentPath = window.location.pathname;
  document.querySelectorAll('.nav-link').forEach(link => {
    const href = link.getAttribute('href');
    if (currentPath.endsWith(href) || (currentPath.endsWith('/') && href === 'index.html')) {
      link.classList.add('active');
    }
  });

  // Drawer Backdrop and close button
  const backdrop = document.getElementById('drawer-backdrop');
  const closeBtn = document.getElementById('drawer-close-btn');
  if (backdrop) backdrop.addEventListener('click', closeCourseDrawer);
  if (closeBtn) closeBtn.addEventListener('click', closeCourseDrawer);

  window.addEventListener('keydown', e => {
    if (e.key === 'Escape') closeCourseDrawer();
  });
}

let currentDrawerCourseId = null;

// Inspector Drawer Logic
function openCourseDrawer(courseId) {
  if (!curriculumData || !curriculumData.courses) return;
  const course = curriculumData.courses[courseId];
  if (!course) return;

  currentDrawerCourseId = courseId;

  const drawer = document.getElementById('course-drawer');
  const backdrop = document.getElementById('drawer-backdrop');
  if (!drawer || !backdrop) return;

  const postReqMap = getPostRequisitesMap(curriculumData.courses);
  const postReqs = postReqMap[courseId] || [];

  // Update Drawer Fields
  document.getElementById('drawer-course-id').textContent = course.id;
  document.getElementById('drawer-course-th').textContent = course.name_TH;
  document.getElementById('drawer-course-en').textContent = course.name_EN;

  // Category pill
  const catEl = document.getElementById('drawer-category-pill');
  if (catEl) {
    let catNameTH = 'วิชาเลือกทั่วไป';
    let catNameEN = 'Elective';
    if (course.classification === 'core') {
      catNameTH = 'วิชาแกน';
      catNameEN = 'Core Course';
    } else if (course.classification === 'compulsory') {
      catNameTH = 'วิชาเอกบังคับ';
      catNameEN = 'Compulsory Course';
    } else if (course.classification === 'project-elective') {
      catNameTH = 'วิชาเอกเลือกมุ่งเน้นโครงงาน';
      catNameEN = 'Project-oriented Elective';
    } else if (course.classification === 'non-project-elective') {
      catNameTH = 'วิชาเอกเลือกไม่มุ่งเน้นโครงงาน';
      catNameEN = 'Non-project Elective';
    } else if (course.classification === 'gened') {
      catNameTH = 'วิชาศึกษาทั่วไป';
      catNameEN = 'General Education';
    }
    catEl.textContent = currentLang === 'th' ? catNameTH : catNameEN;
  }

  // Credits pill
  const crEl = document.getElementById('drawer-credits-pill');
  if (crEl) {
    crEl.textContent = course.credits || '3 credits';
  }

  // Terms offered pill
  const termsEl = document.getElementById('drawer-terms-pill');
  if (termsEl) {
    const t1 = course.terms?.t1;
    const t2 = course.terms?.t2;
    if (t1 && t2) {
      termsEl.textContent = currentLang === 'th' ? 'เปิดสอน: ภาคการศึกษา 1 และ 2 (ปี 2569)' : 'Offered: Term 1 & Term 2 (2026)';
      termsEl.className = 'meta-pill offered-both';
    } else if (t1) {
      termsEl.textContent = currentLang === 'th' ? 'เปิดสอน: ภาคการศึกษา 1 เท่านั้น (ปี 2569)' : 'Offered: Term 1 Only (2026)';
      termsEl.className = 'meta-pill';
    } else if (t2) {
      termsEl.textContent = currentLang === 'th' ? 'เปิดสอน: ภาคการศึกษา 2 เท่านั้น (ปี 2569)' : 'Offered: Term 2 Only (2026)';
      termsEl.className = 'meta-pill';
    } else {
      termsEl.textContent = currentLang === 'th' ? 'ไม่พบเปิดสอนในปี 2569' : 'Not Offered in 2026';
      termsEl.className = 'meta-pill';
    }
  }

  // Official Prerequisites string from MIS CMU
  const prereqStrEl = document.getElementById('drawer-prereq-str');
  if (prereqStrEl) {
    prereqStrEl.textContent = course.official_prereq || (currentLang === 'th' ? 'ไม่มี' : 'None');
  }

  // Prerequisites tags
  const prereqsTagsEl = document.getElementById('drawer-prereqs-tags');
  if (prereqsTagsEl) {
    prereqsTagsEl.innerHTML = '';
    const pList = course.prerequisites || [];
    if (pList.length === 0) {
      prereqsTagsEl.innerHTML = `<span style="font-size: 0.85rem; color: var(--text-muted);">${currentLang === 'th' ? 'ไม่มีวิชากำหนดก่อน' : 'No prerequisite courses'}</span>`;
    } else {
      pList.forEach(pId => {
        const pBtn = document.createElement('button');
        pBtn.className = 'link-course-tag';
        const pObj = curriculumData.courses[pId];
        const pName = pObj ? (currentLang === 'th' ? pObj.name_TH : pObj.name_EN) : '';
        pBtn.textContent = `${pId} ${pName ? '· ' + pName.slice(0, 20) + '...' : ''}`;
        pBtn.addEventListener('click', () => openCourseDrawer(pId));
        prereqsTagsEl.appendChild(pBtn);
      });
    }
  }

  // Post-requisites tags
  const postreqsTagsEl = document.getElementById('drawer-postreqs-tags');
  if (postreqsTagsEl) {
    postreqsTagsEl.innerHTML = '';
    if (postReqs.length === 0) {
      postreqsTagsEl.innerHTML = `<span style="font-size: 0.85rem; color: var(--text-muted);">${currentLang === 'th' ? 'ไม่มีวิชาที่ต้องเรียนวิชานี้ก่อน' : 'No dependent courses'}</span>`;
    } else {
      postReqs.forEach(postPid => {
        const postBtn = document.createElement('button');
        postBtn.className = 'link-course-tag';
        const postObj = curriculumData.courses[postPid];
        const postName = postObj ? (currentLang === 'th' ? postObj.name_TH : postObj.name_EN) : '';
        postBtn.textContent = `${postPid} ${postName ? '· ' + postName.slice(0, 20) + '...' : ''}`;
        postBtn.addEventListener('click', () => openCourseDrawer(postPid));
        postreqsTagsEl.appendChild(postBtn);
      });
    }
  }

  // Course Descriptions
  const descThEl = document.getElementById('drawer-desc-th');
  if (descThEl) {
    descThEl.textContent = course.desc_TH || 'ไม่มีคำอธิบายลักษณะกระบวนวิชาภาษาไทย';
  }
  const descEnEl = document.getElementById('drawer-desc-en');
  if (descEnEl) {
    descEnEl.textContent = course.desc_EN || 'No English course description available.';
  }

  // Open classes
  drawer.classList.add('open');
  backdrop.classList.add('open');
  document.body.style.overflow = 'hidden';
}

function closeCourseDrawer() {
  currentDrawerCourseId = null;
  const drawer = document.getElementById('course-drawer');
  const backdrop = document.getElementById('drawer-backdrop');
  if (drawer) drawer.classList.remove('open');
  if (backdrop) backdrop.classList.remove('open');
  document.body.style.overflow = '';
}

// Initialize on DOMContentLoaded
document.addEventListener('DOMContentLoaded', () => {
  initTheme();
  initLanguage();
  setupSharedHeader();
});
