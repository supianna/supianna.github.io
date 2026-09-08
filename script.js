/**
 * Supianna's Portfolio Tab Switching Logic
 * Pure JavaScript for seamless navigation and URL hash sync
 */

document.addEventListener('DOMContentLoaded', () => {
  const tabButtons = document.querySelectorAll('.nav-tab-btn');
  const tabPanels = document.querySelectorAll('.tab-panel');

  // 특정 탭 활성화 함수
  function activateTab(tabId) {
    // 탭 버튼 active 클래스 제어
    tabButtons.forEach(btn => {
      if (btn.dataset.tab === tabId) {
        btn.classList.add('active');
      } else {
        btn.classList.remove('active');
      }
    });

    // 탭 패널 active 제어
    tabPanels.forEach(panel => {
      if (panel.id === tabId) {
        panel.classList.add('active');
      } else {
        panel.classList.remove('active');
      }
    });

    // 화면 상단으로 부드럽게 스크롤
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  // 상단 네비게이션 탭 클릭 이벤트
  tabButtons.forEach(btn => {
    btn.addEventListener('click', (e) => {
      const targetTab = btn.dataset.tab;
      activateTab(targetTab);
      history.pushState(null, '', `#${targetTab}`);
    });
  });

  // 로고/브랜드 클릭 시 홈으로 이동
  const brandLink = document.querySelector('.nav-brand');
  if (brandLink) {
    brandLink.addEventListener('click', (e) => {
      e.preventDefault();
      activateTab('home');
      history.pushState(null, '', '#home');
    });
  }

  // 본문 내 탭 이동 버튼 (data-target-tab 속성 지원)
  const jumpButtons = document.querySelectorAll('[data-target-tab]');
  jumpButtons.forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.preventDefault();
      const targetTab = btn.getAttribute('data-target-tab');
      if (targetTab) {
        activateTab(targetTab);
        history.pushState(null, '', `#${targetTab}`);
      }
    });
  });

  // 브라우저 해시(URL)에 따른 초기 탭 설정 및 뒤로가기/앞으로가기 처리
  function handleHashChange() {
    const hash = window.location.hash.replace('#', '');
    const validTabs = ['home', 'resume', 'projects', 'blank'];
    if (validTabs.includes(hash)) {
      activateTab(hash);
    } else {
      activateTab('home');
    }
  }

  window.addEventListener('hashchange', handleHashChange);
  handleHashChange();
});
