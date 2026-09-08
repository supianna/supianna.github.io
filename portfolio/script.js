/**
 * Supianna's Portfolio JavaScript
 * 1. Seamless Tab Switching & URL Hash Sync
 * 2. Emotional Yoonseul (Sea Glitters) Ambient Particle Canvas
 */

document.addEventListener('DOMContentLoaded', () => {
  // ------------------------------------------------------------------------
  // 1. 탭 전환 및 브라우저 해시 동기화 로직
  // ------------------------------------------------------------------------
  const tabButtons = document.querySelectorAll('.nav-tab-btn');
  const tabPanels = document.querySelectorAll('.tab-panel');

  function activateTab(tabId) {
    // 이전 해시 매핑 호환성 지원
    if (tabId === 'resume') tabId = 'who-am-i';
    if (tabId === 'blank') tabId = 'free-board';

    document.body.dataset.activeTab = tabId;

    tabButtons.forEach(btn => {
      if (btn.dataset.tab === tabId) {
        btn.classList.add('active');
      } else {
        btn.classList.remove('active');
      }
    });

    tabPanels.forEach(panel => {
      if (panel.id === tabId) {
        panel.classList.add('active');
      } else {
        panel.classList.remove('active');
      }
    });

    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  tabButtons.forEach(btn => {
    btn.addEventListener('click', () => {
      const targetTab = btn.dataset.tab;
      activateTab(targetTab);
      history.pushState(null, '', `#${targetTab}`);
    });
  });

  const brandLink = document.querySelector('.nav-brand');
  if (brandLink) {
    brandLink.addEventListener('click', (e) => {
      e.preventDefault();
      activateTab('home');
      history.pushState(null, '', '#home');
    });
  }

  // data-target-tab을 가진 모든 버튼 및 링크 이벤트 연동
  document.addEventListener('click', (e) => {
    const jumpBtn = e.target.closest('[data-target-tab]');
    if (jumpBtn) {
      e.preventDefault();
      const targetTab = jumpBtn.getAttribute('data-target-tab');
      if (targetTab) {
        activateTab(targetTab);
        history.pushState(null, '', `#${targetTab}`);
      }
    }
  });

  function handleHashChange() {
    let hash = window.location.hash.replace('#', '');
    if (hash === 'resume') hash = 'who-am-i';
    if (hash === 'blank') hash = 'free-board';

    const validTabs = ['home', 'who-am-i', 'projects', 'free-board'];
    if (validTabs.includes(hash)) {
      activateTab(hash);
    } else {
      activateTab('home');
    }
  }

  window.addEventListener('hashchange', handleHashChange);
  handleHashChange();

  // ------------------------------------------------------------------------
  // 2. Projects 탭 카테고리 필터링 로직
  // ------------------------------------------------------------------------
  const filterButtons = document.querySelectorAll('.filter-btn');
  const projectCards = document.querySelectorAll('.project-card');

  filterButtons.forEach(btn => {
    btn.addEventListener('click', () => {
      filterButtons.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');

      const filter = btn.dataset.filter;
      projectCards.forEach(card => {
        const category = card.dataset.category;
        if (filter === 'all' || category === filter) {
          card.style.display = 'flex';
          card.style.animation = 'noteAppear 0.35s ease forwards';
        } else {
          card.style.display = 'none';
        }
      });
    });
  });

  // ------------------------------------------------------------------------
  // 3. Free Board (자유 게시판 & 방명록) LocalStorage 관리 로직
  // ------------------------------------------------------------------------
  const STORAGE_KEY = 'supianna_free_board_notes';
  const boardForm = document.getElementById('board-form');
  const boardAuthorInput = document.getElementById('board-author');
  const boardContentInput = document.getElementById('board-content');
  const charCounter = document.getElementById('char-count');
  const boardListEl = document.getElementById('board-notes-list');
  const boardTotalCountEl = document.getElementById('board-total-count');
  const emojiTagButtons = document.querySelectorAll('.emoji-tag-btn');
  const btnResetSample = document.getElementById('btn-reset-sample');

  let currentSelectedTag = '✨ 영감';

  // 기본 샘플 메모 데이터 (Mystic Deep Aurora 테마)
  const defaultNotes = [
    {
      id: 1,
      author: '수피아나 (Supianna)',
      tag: '✨ 영감',
      content: '오로라 테크 아카이브에 오신 것을 환영합니다! 🌌\n끝없는 밤하늘을 수놓는 오로라처럼, 이곳에서 새로운 영감과 아이디어를 발견하시길 바랍니다.',
      date: '2026.09.08 13:45'
    },
    {
      id: 2,
      author: '익명의 탐험가',
      tag: '🌌 오로라',
      content: '딥 스페이스 밤하늘과 네온 오로라 글래스모피즘이 정말 몽환적이고 세련되었네요! 원스크린 홈 대시보드 몰입감이 최고입니다.',
      date: '2026.09.08 13:48'
    },
    {
      id: 3,
      author: '동료 개발자',
      tag: '🚀 응원',
      content: '미래지향적인 비주얼과 탄탄한 아키텍처의 조화가 멋집니다. 앞으로 펼쳐질 다양한 프로젝트들도 진심으로 응원합니다!',
      date: '2026.09.08 13:50'
    }
  ];

  // 로컬스토리지에서 메모 불러오기
  function loadNotes() {
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      if (!stored) {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(defaultNotes));
        return defaultNotes;
      }
      return JSON.parse(stored);
    } catch (e) {
      console.error('메모 불러오기 에러:', e);
      return defaultNotes;
    }
  }

  // 로컬스토리지에 메모 저장하기
  function saveNotes(notes) {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(notes));
    } catch (e) {
      console.error('메모 저장 에러:', e);
    }
  }

  // 메모 목록 렌더링
  function renderNotes() {
    if (!boardListEl) return;
    const notes = loadNotes();

    if (boardTotalCountEl) {
      boardTotalCountEl.textContent = notes.length;
    }

    if (notes.length === 0) {
      boardListEl.innerHTML = `
        <div style="grid-column: 1 / -1; text-align: center; padding: 3.5rem 1rem; color: var(--text-muted); background: var(--glass-bg); border-radius: var(--radius-xl); border: 1px dashed rgba(255, 255, 255, 0.15);">
          <div style="font-size: 2.5rem; margin-bottom: 0.6rem; filter: drop-shadow(0 0 10px rgba(192, 132, 252, 0.5));">🌌</div>
          <p style="font-size: 1.05rem; font-weight: 700; color: var(--text-primary);">아직 남겨진 우주의 메시지가 없습니다.</p>
          <p style="font-size: 0.885rem; margin-top: 0.35rem; color: var(--text-secondary);">위 폼에서 첫 번째 반짝이는 메모를 남겨보세요!</p>
        </div>
      `;
      return;
    }

    boardListEl.innerHTML = notes.map(note => {
      const safeAuthor = escapeHtml(note.author || '익명의 여행자');
      const safeContent = escapeHtml(note.content || '');
      const safeTag = escapeHtml(note.tag || '✨ 영감');
      const safeDate = escapeHtml(note.date || '');

      return `
        <article class="board-note-card" data-note-id="${note.id}">
          <div class="note-pin" aria-hidden="true"></div>
          <div class="note-card-header">
            <span class="note-tag">${safeTag}</span>
            <button type="button" class="btn-delete-note" title="메모 삭제" data-id="${note.id}" aria-label="메모 삭제">×</button>
          </div>
          <div class="note-card-body">
            <p class="note-message">${safeContent}</p>
          </div>
          <div class="note-card-footer">
            <span class="note-author">@ ${safeAuthor}</span>
            <span class="note-date">${safeDate}</span>
          </div>
        </article>
      `;
    }).join('');

    // 개별 삭제 버튼 이벤트 바인딩
    const deleteButtons = boardListEl.querySelectorAll('.btn-delete-note');
    deleteButtons.forEach(btn => {
      btn.addEventListener('click', (e) => {
        e.stopPropagation();
        const noteId = Number(btn.dataset.id);
        deleteNote(noteId);
      });
    });
  }

  function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }

  // 메모 삭제
  function deleteNote(id) {
    if (confirm('이 메모를 삭제하시겠습니까?')) {
      let notes = loadNotes();
      notes = notes.filter(n => n.id !== id);
      saveNotes(notes);
      renderNotes();
    }
  }

  // 이모지 태그 선택 이벤트
  emojiTagButtons.forEach(btn => {
    btn.addEventListener('click', () => {
      emojiTagButtons.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      currentSelectedTag = btn.dataset.tag || '✨ 영감';
    });
  });

  // 글자 수 카운터 연동
  if (boardContentInput && charCounter) {
    boardContentInput.addEventListener('input', () => {
      charCounter.textContent = boardContentInput.value.length;
    });
  }

  // 폼 제출 이벤트
  if (boardForm) {
    boardForm.addEventListener('submit', (e) => {
      e.preventDefault();

      const rawContent = boardContentInput.value.trim();
      if (!rawContent) {
        alert('메시지 내용을 입력해주세요!');
        boardContentInput.focus();
        return;
      }

      let author = boardAuthorInput.value.trim();
      if (!author) {
        author = '익명의 탐험가';
      }

      const now = new Date();
      const formattedDate = `${now.getFullYear()}.${String(now.getMonth() + 1).padStart(2, '0')}.${String(now.getDate()).padStart(2, '0')} ${String(now.getHours()).padStart(2, '0')}:${String(now.getMinutes()).padStart(2, '0')}`;

      const newNote = {
        id: Date.now(),
        author: author,
        tag: currentSelectedTag,
        content: rawContent,
        date: formattedDate
      };

      const notes = loadNotes();
      notes.unshift(newNote);
      saveNotes(notes);

      // 폼 리셋
      boardContentInput.value = '';
      if (charCounter) charCounter.textContent = '0';
      renderNotes();

      alert('오로라 보드에 메모가 등록되었습니다 ✨');
    });
  }

  // 샘플 메모 복원 버튼
  if (btnResetSample) {
    btnResetSample.addEventListener('click', () => {
      if (confirm('오로라 기본 샘플 메모로 다시 채우시겠습니까? (기존 메모는 덮어씌워집니다)')) {
        saveNotes(defaultNotes);
        renderNotes();
      }
    });
  }

  // 게시판 초기 렌더링
  renderNotes();

  // ------------------------------------------------------------------------
  // 4. 은하수 별빛 & 오로라 파티클 캔버스 (Cosmic Starlight & Twinkling Dust)
  // ------------------------------------------------------------------------
  const canvas = document.getElementById('sparkle-canvas');
  if (!canvas) return;

  const ctx = canvas.getContext('2d');
  let width = (canvas.width = window.innerWidth);
  let height = (canvas.height = window.innerHeight);

  window.addEventListener('resize', () => {
    width = canvas.width = window.innerWidth;
    height = canvas.height = window.innerHeight;
  });

  const stars = [];
  const STAR_COUNT = 65;

  class CosmicStar {
    constructor() {
      this.reset();
      this.alpha = Math.random() * 0.8;
    }

    reset() {
      this.x = Math.random() * width;
      this.y = Math.random() * height;
      this.size = Math.random() * 2.2 + 0.8;
      this.alpha = 0;
      this.speed = Math.random() * 0.015 + 0.005;
      this.isGrowing = true;
      const typeChoice = Math.random();
      if (typeChoice < 0.4) {
        this.color = 'cyan'; // #38bdf8
      } else if (typeChoice < 0.75) {
        this.color = 'violet'; // #c084fc
      } else {
        this.color = 'white'; // #ffffff
      }
    }

    update() {
      if (this.isGrowing) {
        this.alpha += this.speed;
        if (this.alpha >= 0.85) {
          this.isGrowing = false;
        }
      } else {
        this.alpha -= this.speed;
        if (this.alpha <= 0) {
          this.reset();
        }
      }
      this.y -= 0.12; // 은하수처럼 아주 천천히 위로 부유
      if (this.y < 0) this.y = height;
    }

    draw() {
      ctx.save();
      ctx.beginPath();
      ctx.arc(this.x, this.y, this.size, 0, Math.PI * 2);

      let colorRgba = `rgba(255, 255, 255, ${this.alpha})`;
      let glowRgba = `rgba(255, 255, 255, 0.4)`;
      if (this.color === 'cyan') {
        colorRgba = `rgba(56, 189, 248, ${this.alpha})`;
        glowRgba = `rgba(6, 182, 212, 0.6)`;
      } else if (this.color === 'violet') {
        colorRgba = `rgba(192, 132, 252, ${this.alpha})`;
        glowRgba = `rgba(139, 92, 246, 0.6)`;
      }

      ctx.fillStyle = colorRgba;
      ctx.shadowBlur = 10;
      ctx.shadowColor = glowRgba;
      ctx.fill();
      ctx.restore();
    }
  }

  for (let i = 0; i < STAR_COUNT; i++) {
    stars.push(new CosmicStar());
  }

  // 때때로 밤하늘을 가로지르는 은은한 유성(Shooting Star)
  let shootingStar = null;

  class ShootingStar {
    constructor() {
      this.reset();
    }
    reset() {
      this.x = Math.random() * (width * 0.7);
      this.y = Math.random() * (height * 0.4);
      this.len = Math.random() * 80 + 50;
      this.speed = Math.random() * 8 + 6;
      this.size = Math.random() * 1.5 + 1;
      this.alpha = 1;
      this.active = true;
    }
    update() {
      this.x += this.speed;
      this.y += this.speed * 0.55;
      this.alpha -= 0.025;
      if (this.alpha <= 0) {
        this.active = false;
      }
    }
    draw() {
      if (!this.active) return;
      ctx.save();
      ctx.strokeStyle = `rgba(192, 132, 252, ${this.alpha})`;
      ctx.lineWidth = this.size;
      ctx.beginPath();
      ctx.moveTo(this.x, this.y);
      ctx.lineTo(this.x - this.len, this.y - this.len * 0.55);
      ctx.stroke();
      ctx.restore();
    }
  }

  function maybeSpawnShootingStar() {
    if (!shootingStar && Math.random() < 0.008) {
      shootingStar = new ShootingStar();
    }
  }

  function animate() {
    ctx.clearRect(0, 0, width, height);

    stars.forEach(s => {
      s.update();
      s.draw();
    });

    maybeSpawnShootingStar();
    if (shootingStar) {
      shootingStar.update();
      shootingStar.draw();
      if (!shootingStar.active) {
        shootingStar = null;
      }
    }

    requestAnimationFrame(animate);
  }

  animate();
});
