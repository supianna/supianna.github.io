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
