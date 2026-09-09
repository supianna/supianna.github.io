/**
 * ==========================================================================
 * Supia.log | Modern Tech Blog JavaScript Engine
 * 1. 4-Tab Navigation & Browser Hash Sync (SPA Style)
 * 2. Article Feed, Category Filtering & Live Search
 * 3. Article Reader Modal Popups
 * 4. Free Board & Guestbook with LocalStorage Persistence
 * 5. Interactive UI Helpers (Scroll-top, Mobile menu)
 * ==========================================================================
 */

document.addEventListener('DOMContentLoaded', () => {

  // ------------------------------------------------------------------------
  // 1. 블로그 아티클 데이터베이스 (Mock Data)
  // ------------------------------------------------------------------------
  const articles = [
    {
      id: 1,
      title: '바닐라 자바스크립트로 60fps 캔버스 파티클 시스템 최적화하기',
      category: 'frontend',
      categoryName: 'Frontend',
      date: '2026.03.05',
      readTime: '6분',
      views: 342,
      tags: ['JavaScript', 'Canvas', 'Performance', 'Animation'],
      excerpt: '브라우저의 requestAnimationFrame 루프를 활용하여 수백 개의 별빛 및 오로라 파티클을 버벅임 없이 렌더링한 성능 튜닝 여정을 공유합니다.',
      content: `
        <h3>1. 문제 인식: 파티클 수 증가에 따른 프레임 드랍</h3>
        <p>포트폴리오와 블로그 배경에 밤하늘의 은하수와 오로라 느낌을 내기 위해 수백 개의 반짝이는 파티클을 렌더링해야 했습니다. 그러나 초기 구현에서는 매 프레임마다 객체를 재생성하고 불필요한 DOM 조회가 겹치면서 저사양 기기에서 FPS가 30 이하로 급락하는 현상이 발생했습니다.</p>
        
        <blockquote>
          "성능 최적화의 첫걸음은 메모리 할당(Garbage Collection)을 최소화하고 화면 갱신 주기(Refresh Rate)에 정확히 동기화하는 것입니다."
        </blockquote>

        <h3>2. 최적화 전략</h3>
        <p>다음과 같은 3가지 핵심 기법을 적용했습니다:</p>
        <ul>
          <li><strong>객체 풀링(Object Pooling)</strong>: 매 프레임 파티클 객체를 생성/파괴하지 않고, 고정된 크기의 배열을 재활용하여 GC 유발 방지</li>
          <li><strong>오프스크린 캔버스 캐싱</strong>: 복잡한 방사형 그라데이션 글로우 효과를 미리 캐시 캔버스에 그려두고 <code>drawImage</code>로 고속 복사</li>
          <li><strong>화면 밖 객체 연산 생략</strong>: 뷰포트를 벗어난 파티클의 삼각함수 연산을 조기에 건너뜁니다.</li>
        </ul>

        <h3>3. 핵심 코드</h3>
        <pre><code>// 방사형 그라데이션 스프라이트 사전 캐싱
function createGlowSprite(color, radius) {
  const offCanvas = document.createElement('canvas');
  offCanvas.width = radius * 2;
  offCanvas.height = radius * 2;
  const ctx = offCanvas.getContext('2d');
  
  const grad = ctx.createRadialGradient(radius, radius, 0, radius, radius, radius);
  grad.addColorStop(0, color);
  grad.addColorStop(1, 'transparent');
  ctx.fillStyle = grad;
  ctx.beginPath();
  ctx.arc(radius, radius, radius, 0, Math.PI * 2);
  ctx.fill();
  return offCanvas;
}</code></pre>

        <h3>4. 결과 및 배운 점</h3>
        <p>파티클 400개 기준 모바일 브라우저에서도 안정적인 60fps를 유지할 수 있었습니다. 브라우저의 그래픽 파이프라인을 이해하고 코드를 작성하는 것의 중요성을 다시 한번 실감했습니다.</p>
      `
    },
    {
      id: 2,
      title: '단일 책임 원칙(SRP)으로 풀어낸 유지보수 가능한 UI 컴포넌트 설계',
      category: 'architecture',
      categoryName: 'Architecture',
      date: '2026.02.24',
      readTime: '8분',
      views: 520,
      tags: ['CleanCode', 'Architecture', 'SRP', 'Refactoring'],
      excerpt: '복잡해지는 웹 페이지에서 각 함수와 모듈이 단 하나의 역할만 맡도록 분리하여 변경에 유연하고 테스트하기 쉬운 코드를 만드는 방법론.',
      content: `
        <h3>1. 한 함수가 너무 많은 일을 할 때 생기는 비극</h3>
        <p>기능을 빠르게 구현하다 보면 데이터 가공, DOM 렌더링, 이벤트 리스너 등록, 에러 처리를 하나의 함수에 몰아넣는 실수를 범하기 쉽습니다. 이러한 '신(God) 함수'는 작은 요구사항 변경에도 전체가 깨지는 취약점을 갖습니다.</p>

        <h3>2. 단일 책임 원칙(SRP) 적용 실습</h3>
        <p>하나의 컴포넌트를 다음과 같이 책임별로 쪼갭니다:</p>
        <ol>
          <li><strong>Data Provider</strong>: 데이터를 가져오거나 가공하는 책임</li>
          <li><strong>HTML Template Builder</strong>: 순수하게 데이터를 받아 HTML 문자열이나 요소를 조립하는 책임</li>
          <li><strong>DOM Updater</strong>: 실제 문서 트리에 안전하게 반영하는 책임</li>
          <li><strong>Event Binder</strong>: 사용자 인터랙션을 청취하고 비즈니스 함수를 트리거하는 책임</li>
        </ol>

        <blockquote>
          "코드는 작성되는 시간보다 읽히고 수정되는 시간이 훨씬 깁니다. 미래의 나와 동료를 위해 책임을 쪼개세요."
        </blockquote>
      `
    },
    {
      id: 3,
      title: 'Atomic Commits: Git 히스토리를 정갈한 개발 이야기로 만드는 법',
      category: 'architecture',
      categoryName: 'Architecture',
      date: '2026.02.10',
      readTime: '5분',
      views: 412,
      tags: ['GitWorkflow', 'CleanCode', 'Collaboration'],
      excerpt: '무분별하게 모든 변경사항을 하나의 커밋으로 뭉개지 않고, 논리적 단위별로 깔끔하게 스테이징하고 직관적인 한국어로 커밋하는 실전 가이드.',
      content: `
        <h3>1. 원자적 커밋(Atomic Commit)이란?</h3>
        <p>커밋 하나가 단 하나의 의미 있는 논리적 변경(One logical change per commit)만을 담고 있어야 한다는 원칙입니다. 버그가 발생했을 때 <code>git bisect</code>나 <code>git revert</code>를 안전하게 수행할 수 있는 기반이 됩니다.</p>

        <h3>2. 실전 분리 기준</h3>
        <ul>
          <li><strong>환경 및 설정</strong>: <code>.gitignore</code>, 패키지 의존성 파일 등</li>
          <li><strong>기능 구현</strong>: 신규 기능 마크업 및 자바스크립트 로직</li>
          <li><strong>문서 및 리팩토링</strong>: README 수정 및 오탈자 교정</li>
        </ul>
      `
    },
    {
      id: 4,
      title: '외부 서버 없이 LocalStorage로 실시간 방명록 & 게시판 만들기',
      category: 'frontend',
      categoryName: 'Frontend',
      date: '2026.01.28',
      readTime: '7분',
      views: 630,
      tags: ['JavaScript', 'LocalStorage', 'WebStandards', 'Security'],
      excerpt: '백엔드 데이터베이스 없이도 브라우저 스토리지 API와 직렬화 기술을 활용해 지속성 있는 인터랙티브 게시판을 안전하게 구축하는 실전 팁.',
      content: `
        <h3>1. 브라우저 스토리지의 매력</h3>
        <p>정적 호스팅 환경(GitHub Pages)에서도 사용자에게 개인화된 상호작용 경험을 제공할 수 있습니다. 로컬 스토리지를 이용하면 브라우저를 닫거나 새로고침해도 작성한 데이터가 온전히 보존됩니다.</p>

        <h3>2. 필수 보안: XSS 방지 텍스트 인코딩</h3>
        <pre><code>function escapeHtml(str) {
  return str
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}</code></pre>
      `
    },
    {
      id: 5,
      title: '개발자로서의 1년을 돌아보며: 배움과 성장의 기록',
      category: 'retrospect',
      categoryName: '회고 & 일상',
      date: '2026.01.05',
      readTime: '6분',
      views: 890,
      tags: ['Retrospective', 'Career', 'Life'],
      excerpt: '새로운 기술을 탐구하고 개인 프로젝트들을 완성해 나가며 마주했던 고민들과, 앞으로 지향하고자 하는 개발자 상에 대한 솔직한 고백.',
      content: `
        <h3>기록이 성장을 이끈다</h3>
        <p>어제 풀지 못했던 난제가 오늘 해결되었을 때, 그 순간의 사고 과정을 메모해두는 습관이 지난 1년간 저를 가장 크게 성장시켰습니다.</p>
        <p>앞으로도 화려함에 휘둘리기보다는 기본기를 탄탄히 다지고, 사용자에게 진정한 가치를 전달할 수 있는 단단한 개발자로 살아가고자 합니다.</p>
      `
    },
    {
      id: 6,
      title: '웹 브라우저의 렌더링 파이프라인과 CSS 하드웨어 가속 원리',
      category: 'devlog',
      categoryName: 'DevLog',
      date: '2025.12.18',
      readTime: '9분',
      views: 750,
      tags: ['BrowserEngine', 'CSS-Architecture', 'Performance'],
      excerpt: 'DOM Tree 생성부터 Reflow, Repaint, Composite 단계까지 브라우저의 화면 렌더링 과정을 이해하고 CSS transform/opacity를 활용한 GPU 가속 최적화.',
      content: `
        <h3>1. 렌더링 파이프라인 단계</h3>
        <p>브라우저는 HTML 파싱 → DOM 트리 구성 → CSSOM 결합 → Render Tree 생성 → Layout(Reflow) → Paint(Repaint) → Composite 단계를 거쳐 픽셀을 화면에 찍어냅니다.</p>

        <h3>2. GPU 합성(Composite) 계층의 활용</h3>
        <p><code>transform</code>과 <code>opacity</code> 속성은 Layout과 Paint 단계를 건너뛰고 오직 합성 단계만 거치므로, 부드러운 60fps 애니메이션을 구현하는 최선의 선택입니다.</p>
      `
    }
  ];

  // ------------------------------------------------------------------------
  // 2. 4대 메인 탭 전환 & 브라우저 URL 해시 동기화 로직
  // ------------------------------------------------------------------------
  const tabButtons = document.querySelectorAll('.tab-btn');
  const tabPanels = document.querySelectorAll('.tab-panel');

  function activateTab(tabId) {
    const validTabs = ['home', 'who-am-i', 'projects', 'free-board'];
    if (!validTabs.includes(tabId)) {
      tabId = 'home';
    }

    document.body.dataset.activeTab = tabId;

    // 네비게이션 버튼 활성화 토글
    tabButtons.forEach(btn => {
      if (btn.dataset.tab === tabId) {
        btn.classList.add('active');
      } else {
        btn.classList.remove('active');
      }
    });

    // 탭 패널 표시 전환
    tabPanels.forEach(panel => {
      if (panel.id === tabId) {
        panel.classList.add('active');
      } else {
        panel.classList.remove('active');
      }
    });

    // 화면 최상단으로 부드럽게 스크롤
    window.scrollTo({ top: 0, behavior: 'smooth' });

    // Who am I ? 탭 활성화 시 해달 조개 던지기 시네마틱 자동 재생
    if (tabId === 'who-am-i') {
      setTimeout(() => {
        triggerOtterShellToss();
      }, 150);
    }
  }

  // ------------------------------------------------------------------------
  // 2-1. Who am I ? 탭: 귀여운 해달의 조개 던지기 시네마틱 애니메이션 엔진
  // ------------------------------------------------------------------------
  const otterCharacter = document.getElementById('otter-character');
  const flyingShell = document.getElementById('otter-flying-shell');
  const landingBurst = document.getElementById('shell-landing-burst');
  const profileContainer = document.getElementById('profile-reveal-container');
  let isOtterAnimating = false;

  function triggerOtterShellToss() {
    if (!otterCharacter || !flyingShell || !profileContainer) return;
    if (isOtterAnimating) return;
    isOtterAnimating = true;

    // 1. 기존 클래스 초기화
    otterCharacter.classList.remove('is-throwing');
    flyingShell.classList.remove('is-flying');
    if (landingBurst) landingBurst.classList.remove('burst-active');
    profileContainer.classList.remove('is-revealed');

    // 리플로우 강제 (애니메이션 재시작을 위함)
    void flyingShell.offsetWidth;

    // 2. 해달 앞발 들고 조개 투척 시작!
    otterCharacter.classList.add('is-throwing');
    flyingShell.classList.add('is-flying');

    // 3. 조개가 화면 중앙에 도달하는 타이밍 (약 750ms 시점)
    setTimeout(() => {
      if (landingBurst) landingBurst.classList.add('burst-active');
      profileContainer.classList.add('is-revealed');
    }, 750);

    // 4. 애니메이션 완료 후 정리
    setTimeout(() => {
      otterCharacter.classList.remove('is-throwing');
      flyingShell.classList.remove('is-flying');
      isOtterAnimating = false;
    }, 1200);
  }

  // 해달 클릭 시 조개 던지기 리플레이 이벤트
  if (otterCharacter) {
    otterCharacter.addEventListener('click', (e) => {
      e.stopPropagation();
      triggerOtterShellToss();
    });

    otterCharacter.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault();
        triggerOtterShellToss();
      }
    });
  }

  // 상단 탭 버튼 클릭 이벤트
  tabButtons.forEach(btn => {
    btn.addEventListener('click', () => {
      const target = btn.dataset.tab;
      activateTab(target);
      history.pushState(null, '', `#${target}`);
    });
  });

  // data-target-tab을 가진 모든 범용 링크/버튼 이벤트 연결 (모바일 조개 터치 인터랙션 지원)
  const isTouchDevice = () => window.matchMedia('(pointer: coarse)').matches;

  document.addEventListener('click', (e) => {
    const jumpBtn = e.target.closest('[data-target-tab]');
    if (!jumpBtn) return;

    // 모바일 터치 환경에서 조개 카드를 탭한 경우: 첫 탭에선 열어주고, 열린 후 탭 시 이동
    const shellCard = jumpBtn.closest('.shell-card');
    if (shellCard && isTouchDevice()) {
      const isActionClick = e.target.closest('.card-footer-action, .action-text');
      if (!shellCard.classList.contains('is-open') && !isActionClick) {
        e.preventDefault();
        document.querySelectorAll('.shell-card.is-open').forEach(el => el.classList.remove('is-open'));
        shellCard.classList.add('is-open');
        return;
      }
    }

    e.preventDefault();
    const targetTab = jumpBtn.getAttribute('data-target-tab');
    if (targetTab) {
      document.querySelectorAll('.shell-card.is-open').forEach(el => el.classList.remove('is-open'));
      activateTab(targetTab);
      history.pushState(null, '', `#${targetTab}`);
    }
  });

  // 화면 빈 곳 클릭 시 모바일에서 열린 조개 닫기
  document.addEventListener('click', (e) => {
    if (!e.target.closest('.shell-card')) {
      document.querySelectorAll('.shell-card.is-open').forEach(el => el.classList.remove('is-open'));
    }
  });

  // 브라우저 뒤로가기/앞으로가기 및 직접 URL 해시 진입 지원
  function handleHashChange() {
    const hash = window.location.hash.replace('#', '');
    if (hash) {
      activateTab(hash);
    } else {
      activateTab('home');
    }
  }

  window.addEventListener('hashchange', handleHashChange);
  handleHashChange(); // 초기 로드시 실행

  // ------------------------------------------------------------------------
  // 3. HOME 아티클 목록 렌더링, 필터링 및 라이브 검색
  // ------------------------------------------------------------------------
  const articlesListEl = document.getElementById('articles-list');
  const categoryBtns = document.querySelectorAll('.category-btn');
  const searchInput = document.getElementById('article-search');

  let currentCategory = 'all';
  let currentSearchQuery = '';

  function renderArticles() {
    if (!articlesListEl) return;

    // 필터링 적용
    const filtered = articles.filter(item => {
      const matchCategory = (currentCategory === 'all') || (item.category === currentCategory);
      const query = currentSearchQuery.toLowerCase().trim();
      const matchSearch = !query || 
        item.title.toLowerCase().includes(query) ||
        item.excerpt.toLowerCase().includes(query) ||
        item.tags.some(t => t.toLowerCase().includes(query));

      return matchCategory && matchSearch;
    });

    if (filtered.length === 0) {
      articlesListEl.innerHTML = `
        <div style="text-align: center; padding: 3.5rem 1rem; color: var(--text-muted);">
          <p style="font-size: 1.05rem; font-weight: 600; color: var(--text-main);">일치하는 아티클이 없습니다.</p>
          <p style="font-size: 0.88rem; margin-top: 0.25rem;">다른 검색어나 카테고리를 선택해 보세요.</p>
        </div>
      `;
      return;
    }

    articlesListEl.innerHTML = filtered.map(item => `
      <article class="article-row" data-article-id="${item.id}">
        <div class="article-row-meta">
          <span class="category-tag-badge">${item.categoryName}</span>
          <span>${item.date}</span>
          <span>· ${item.readTime}</span>
        </div>
        <h2 class="article-row-title">${item.title}</h2>
        <p class="article-row-excerpt">${item.excerpt}</p>
        <div class="article-row-tags">
          ${item.tags.map(t => `<span class="row-tag">#${t}</span>`).join('')}
        </div>
      </article>
    `).join('');
  }

  // 카테고리 필터 클릭
  categoryBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      categoryBtns.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      currentCategory = btn.dataset.category;
      renderArticles();
    });
  });

  // 검색 인풋 입력
  if (searchInput) {
    searchInput.addEventListener('input', (e) => {
      currentSearchQuery = e.target.value;
      renderArticles();
    });
  }

  // ------------------------------------------------------------------------
  // 4. 아티클 상세 읽기 모달 팝업
  // ------------------------------------------------------------------------
  const modalEl = document.getElementById('article-modal');
  const modalContentEl = document.getElementById('modal-content');
  const modalCloseBtn = document.getElementById('modal-close-btn');

  function openArticleModal(articleId) {
    const article = articles.find(a => a.id === parseInt(articleId, 10));
    if (!article || !modalEl || !modalContentEl) return;

    modalContentEl.innerHTML = `
      <div class="modal-header-section">
        <div class="modal-article-meta">
          <span class="category-tag-badge">${article.categoryName}</span>
          <span>${article.date}</span>
          <span>· ${article.readTime} 읽기</span>
        </div>
        <h1 class="modal-article-title">${article.title}</h1>
        <div class="article-row-tags">
          ${article.tags.map(t => `<span class="row-tag">#${t}</span>`).join('')}
        </div>
      </div>
      <div class="modal-article-body">
        ${article.content}
      </div>
    `;

    modalEl.classList.add('show');
    modalEl.setAttribute('aria-hidden', 'false');
    document.body.style.overflow = 'hidden';
  }

  function closeArticleModal() {
    if (!modalEl) return;
    modalEl.classList.remove('show');
    modalEl.setAttribute('aria-hidden', 'true');
    document.body.style.overflow = '';
  }

  // 아티클 행 클릭 시 모달 열기
  document.addEventListener('click', (e) => {
    const articleTarget = e.target.closest('[data-article-id]');
    if (articleTarget) {
      const id = articleTarget.getAttribute('data-article-id');
      openArticleModal(id);
    }
  });

  if (modalCloseBtn) {
    modalCloseBtn.addEventListener('click', closeArticleModal);
  }

  if (modalEl) {
    modalEl.addEventListener('click', (e) => {
      if (e.target === modalEl) {
        closeArticleModal();
      }
    });
  }

  window.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && modalEl && modalEl.classList.contains('show')) {
      closeArticleModal();
    }
  });

  // ------------------------------------------------------------------------
  // 5. Free Board (자유 게시판 & 실시간 로컬스토리지 방명록)
  // ------------------------------------------------------------------------
  const STORAGE_KEY = 'supia_gitblog_board_posts_v1';
  const boardForm = document.getElementById('board-form');
  const boardCardsGrid = document.getElementById('board-cards-grid');
  const totalBoardCountEl = document.getElementById('total-board-count');
  const charCountEl = document.getElementById('char-count');
  const messageInput = document.getElementById('board-message');

  function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }

  // 초기 샘플 데이터
  const initialBoardPosts = [
    {
      id: 'post_init_1',
      nickname: '우주탐험가',
      category: '응원',
      message: '새로운 블로그 디자인 정말 깔끔하고 읽기 편하네요! 자주 방문할게요 :)',
      createdAt: '2026.03.07 15:20',
      likes: 4
    },
    {
      id: 'post_init_2',
      nickname: '클린코더',
      category: '질문',
      message: '단일 책임 원칙(SRP) 관련 아티클 정독했습니다. 본질을 짚어주는 글이 마음에 와닿습니다.',
      createdAt: '2026.03.06 18:45',
      likes: 3
    }
  ];

  function getBoardPosts() {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      if (!raw) {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(initialBoardPosts));
        return initialBoardPosts;
      }
      return JSON.parse(raw);
    } catch (e) {
      console.warn('LocalStorage access failed:', e);
      return initialBoardPosts;
    }
  }

  function saveBoardPosts(posts) {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(posts));
    } catch (e) {
      console.error('Failed to save to localStorage:', e);
    }
  }

  function renderBoardFeed() {
    if (!boardCardsGrid) return;
    const posts = getBoardPosts();

    if (totalBoardCountEl) {
      totalBoardCountEl.textContent = posts.length;
    }

    if (posts.length === 0) {
      boardCardsGrid.innerHTML = `
        <div style="text-align: center; padding: 2.5rem; color: var(--text-muted);">
          남겨진 메시지가 없습니다. 첫 번째 메시지를 남겨보세요!
        </div>
      `;
      return;
    }

    boardCardsGrid.innerHTML = posts.map(post => `
      <div class="board-item" data-post-id="${post.id}">
        <div class="board-item-top">
          <span class="board-user">
            <span>${escapeHtml(post.nickname)}</span>
            <span class="board-category-chip">${escapeHtml(post.category)}</span>
          </span>
          <span class="board-time">${post.createdAt}</span>
        </div>
        <div class="board-text">${escapeHtml(post.message)}</div>
        <div class="board-actions">
          <button class="btn-board-action" data-action="like" title="공감">❤️ ${post.likes || 0}</button>
          <button class="btn-board-action" data-action="delete" title="삭제">삭제</button>
        </div>
      </div>
    `).join('');
  }

  // 글자 수 실시간 표시
  if (messageInput && charCountEl) {
    messageInput.addEventListener('input', () => {
      charCountEl.textContent = messageInput.value.length;
    });
  }

  // 방명록 폼 제출
  if (boardForm) {
    boardForm.addEventListener('submit', (e) => {
      e.preventDefault();

      const nickname = document.getElementById('board-nickname').value.trim();
      const category = document.getElementById('board-category').value;
      const message = messageInput.value.trim();

      if (!nickname || !message) {
        alert('닉네임과 메시지를 모두 입력해 주세요!');
        return;
      }

      const now = new Date();
      const formattedDate = `${now.getFullYear()}.${String(now.getMonth() + 1).padStart(2, '0')}.${String(now.getDate()).padStart(2, '0')} ${String(now.getHours()).padStart(2, '0')}:${String(now.getMinutes()).padStart(2, '0')}`;

      const newPost = {
        id: 'post_' + Date.now(),
        nickname,
        category,
        message,
        createdAt: formattedDate,
        likes: 0
      };

      const posts = getBoardPosts();
      posts.unshift(newPost);
      saveBoardPosts(posts);
      renderBoardFeed();

      // 폼 리셋
      boardForm.reset();
      if (charCountEl) charCountEl.textContent = '0';
    });
  }

  // 게시글 좋아요 & 삭제 이벤트 위임
  if (boardCardsGrid) {
    boardCardsGrid.addEventListener('click', (e) => {
      const actionBtn = e.target.closest('[data-action]');
      if (!actionBtn) return;

      const card = actionBtn.closest('.board-item');
      const postId = card.getAttribute('data-post-id');
      const action = actionBtn.getAttribute('data-action');
      const posts = getBoardPosts();

      if (action === 'like') {
        const target = posts.find(p => p.id === postId);
        if (target) {
          target.likes = (target.likes || 0) + 1;
          saveBoardPosts(posts);
          actionBtn.textContent = `❤️ ${target.likes}`;
        }
      } else if (action === 'delete') {
        if (confirm('이 메시지를 삭제하시겠습니까?')) {
          const updated = posts.filter(p => p.id !== postId);
          saveBoardPosts(updated);
          renderBoardFeed();
        }
      }
    });
  }

  // ------------------------------------------------------------------------
  // 초기 실행
  // ------------------------------------------------------------------------
  renderArticles();
  renderBoardFeed();

});



