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

  // 기본 샘플 메모 데이터
  const defaultNotes = [
    {
      id: 1,
      author: '수피아나 (Supianna)',
      tag: '✨ 영감',
      content: '방문해주셔서 진심으로 감사합니다! 🌊\n햇살을 받아 반짝이는 바다 윤슬처럼, 이곳에서 따뜻하고 편안한 영감을 얻어가시길 바랍니다.',
      date: '2026.09.08 13:30'
    },
    {
      id: 2,
      author: '익명의 여행자',
      tag: '🌊 윤슬',
      content: '바다 파티클 효과와 시원한 블루 & 골드 톤 디자인이 너무 매력적이에요! 원스크린 홈 화면도 한눈에 들어와서 정말 편리합니다.',
      date: '2026.09.08 13:35'
    },
    {
      id: 3,
      author: '동료 개발자',
      tag: '🚀 응원',
      content: '단단한 코드 구조와 감성적인 UI의 조화가 멋집니다. 앞으로 펼쳐질 다양한 프로젝트들도 진심으로 응원합니다!',
      date: '2026.09.08 13:38'
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
        <div style="grid-column: 1 / -1; text-align: center; padding: 3rem 1rem; color: var(--text-muted); background: var(--glass-card-bg); border-radius: var(--radius-xl); border: 1px dashed rgba(142, 186, 242, 0.4);">
          <div style="font-size: 2.2rem; margin-bottom: 0.5rem;">💌</div>
          <p style="font-size: 1rem; font-weight: 600; color: var(--pastel-blue-deep);">아직 남겨진 메모가 없습니다.</p>
          <p style="font-size: 0.875rem; margin-top: 0.25rem;">위 폼에서 첫 번째 따뜻한 이야기를 남겨보세요!</p>
        </div>
      `;
      return;
    }

    boardListEl.innerHTML = notes.map(note => {
      // XSS 방지를 위한 HTML 이스케이프
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
        author = '익명의 여행자';
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
      notes.unshift(newNote); // 최신글이 맨 위로
      saveNotes(notes);

      // 폼 리셋
      boardContentInput.value = '';
      if (charCounter) charCounter.textContent = '0';
      renderNotes();

      // 등록 성공 피드백
      alert('메모가 따뜻하게 등록되었습니다 ✨');
    });
  }

  // 샘플 메모 복원 버튼
  if (btnResetSample) {
    btnResetSample.addEventListener('click', () => {
      if (confirm('기본 샘플 메모로 다시 채우시겠습니까? (기존 메모는 덮어씌워집니다)')) {
        saveNotes(defaultNotes);
        renderNotes();
      }
    });
  }

  // 게시판 초기 렌더링
  renderNotes();

  // ------------------------------------------------------------------------
  // 2. 바다 윤슬 은은한 반짝임 애니메이션 (Ambient Yoonseul Sparkles)
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

  // 반짝임 파티클 생성
  const sparkles = [];
  const SPARKLE_COUNT = 45; // 화면 전체에 은은하게 퍼지는 파티클 수

  class Sparkle {
    constructor() {
      this.reset();
      this.alpha = Math.random() * 0.7; // 초기 투명도 랜덤 분산
    }

    reset() {
      this.x = Math.random() * width;
      this.y = Math.random() * height;
      this.size = Math.random() * 2.8 + 1.2; // 부드럽고 작은 크기
      this.alpha = 0;
      this.speed = Math.random() * 0.015 + 0.008; // 천천히 숨쉬듯 깜빡임
      this.isGrowing = true;
      this.colorType = Math.random() > 0.4 ? 'gold' : 'blue'; // 따뜻한 햇살빛 또는 맑은 하늘빛
    }

    update() {
      if (this.isGrowing) {
        this.alpha += this.speed;
        if (this.alpha >= 0.75) {
          this.isGrowing = false;
        }
      } else {
        this.alpha -= this.speed;
        if (this.alpha <= 0) {
          this.reset();
        }
      }

      // 물결처럼 아주 미세하게 부유하는 움직임
      this.y += Math.sin(Date.now() * 0.001 + this.x) * 0.15;
    }

    draw() {
      ctx.save();
      ctx.beginPath();
      ctx.arc(this.x, this.y, this.size, 0, Math.PI * 2);

      let gradient = ctx.createRadialGradient(this.x, this.y, 0, this.x, this.y, this.size * 2.2);
      if (this.colorType === 'gold') {
        // 따스한 윤슬 골든 옐로우 틴트
        gradient.addColorStop(0, `rgba(255, 255, 255, ${this.alpha})`);
        gradient.addColorStop(0.5, `rgba(253, 230, 138, ${this.alpha * 0.7})`);
        gradient.addColorStop(1, `rgba(251, 191, 36, 0)`);
      } else {
        // 투명한 에메랄드 스카이블루 틴트
        gradient.addColorStop(0, `rgba(255, 255, 255, ${this.alpha})`);
        gradient.addColorStop(0.5, `rgba(186, 230, 253, ${this.alpha * 0.6})`);
        gradient.addColorStop(1, `rgba(147, 197, 253, 0)`);
      }

      ctx.fillStyle = gradient;
      ctx.shadowBlur = 8;
      ctx.shadowColor = this.colorType === 'gold' ? 'rgba(253, 230, 138, 0.6)' : 'rgba(186, 230, 253, 0.6)';
      ctx.fill();
      ctx.restore();
    }
  }

  for (let i = 0; i < SPARKLE_COUNT; i++) {
    sparkles.push(new Sparkle());
  }

  function animate() {
    ctx.clearRect(0, 0, width, height);
    sparkles.forEach(s => {
      s.update();
      s.draw();
    });
    requestAnimationFrame(animate);
  }

  animate();
});
