/**
 * ============================================================================
 * 도스 고전 너구리 게임 (Ponpoko Web Remake) - Game Engine
 * ============================================================================
 * 조작: 
 *   - 좌우 이동: ← / → (또는 A / D)
 *   - 사다리 타기: ↑ / ↓ (또는 W / S)
 *   - 점프: Spacebar (이동 중 점프 시 포물선 전방 점프, 점프 중 방향 전환 불가)
 * ============================================================================
 */

(function () {
  'use strict';

  // 1. 캔버스 및 렌더링 컨텍스트
  const canvas = document.getElementById('gameCanvas');
  const ctx = canvas.getContext('2d');

  // 2. HUD 및 UI 엘리먼트
  const scoreValEl = document.getElementById('score-val');
  const highScoreValEl = document.getElementById('high-score-val');
  const stageValEl = document.getElementById('stage-val');
  const livesContainerEl = document.getElementById('lives-container');
  const btnSound = document.getElementById('btn-sound');
  const btnRestart = document.getElementById('btn-restart');
  const btnStart = document.getElementById('btn-start');
  const gameOverlay = document.getElementById('game-overlay');
  const overlayTitle = document.getElementById('overlay-title');
  const overlayMsg = document.getElementById('overlay-msg');

  // 모바일 터치 버튼
  const touchUp = document.getElementById('touch-up');
  const touchDown = document.getElementById('touch-down');
  const touchLeft = document.getElementById('touch-left');
  const touchRight = document.getElementById('touch-right');
  const touchJump = document.getElementById('touch-jump');

  // 3. Web Audio API 사운드 시스템
  class RetroSoundEngine {
    constructor() {
      this.ctx = null;
      this.enabled = true;
    }

    init() {
      if (!this.ctx) {
        const AudioContext = window.AudioContext || window.webkitAudioContext;
        this.ctx = new AudioContext();
      }
      if (this.ctx.state === 'suspended') {
        this.ctx.resume();
      }
    }

    playTone(freq, type, duration, startVol = 0.15, endVol = 0.01) {
      if (!this.enabled || !this.ctx) return;
      try {
        const osc = this.ctx.createOscillator();
        const gain = this.ctx.createGain();
        osc.type = type;
        osc.frequency.setValueAtTime(freq, this.ctx.currentTime);
        gain.gain.setValueAtTime(startVol, this.ctx.currentTime);
        gain.gain.exponentialRampToValueAtTime(Math.max(endVol, 0.0001), this.ctx.currentTime + duration);
        osc.connect(gain);
        gain.connect(this.ctx.destination);
        osc.start();
        osc.stop(this.ctx.currentTime + duration);
      } catch (e) {
        // Audio error ignore
      }
    }

    playJump() {
      if (!this.enabled || !this.ctx) return;
      try {
        const osc = this.ctx.createOscillator();
        const gain = this.ctx.createGain();
        osc.type = 'square';
        osc.frequency.setValueAtTime(260, this.ctx.currentTime);
        osc.frequency.exponentialRampToValueAtTime(750, this.ctx.currentTime + 0.22);
        gain.gain.setValueAtTime(0.18, this.ctx.currentTime);
        gain.gain.exponentialRampToValueAtTime(0.01, this.ctx.currentTime + 0.22);
        osc.connect(gain);
        gain.connect(this.ctx.destination);
        osc.start();
        osc.stop(this.ctx.currentTime + 0.22);
      } catch (e) {}
    }

    playEat() {
      if (!this.enabled || !this.ctx) return;
      try {
        const now = this.ctx.currentTime;
        [880, 1174].forEach((freq, i) => {
          const osc = this.ctx.createOscillator();
          const gain = this.ctx.createGain();
          osc.type = 'triangle';
          osc.frequency.setValueAtTime(freq, now + i * 0.08);
          gain.gain.setValueAtTime(0.2, now + i * 0.08);
          gain.gain.exponentialRampToValueAtTime(0.01, now + i * 0.08 + 0.12);
          osc.connect(gain);
          gain.connect(this.ctx.destination);
          osc.start(now + i * 0.08);
          osc.stop(now + i * 0.08 + 0.12);
        });
      } catch (e) {}
    }

    playDie() {
      if (!this.enabled || !this.ctx) return;
      try {
        const osc = this.ctx.createOscillator();
        const gain = this.ctx.createGain();
        osc.type = 'sawtooth';
        osc.frequency.setValueAtTime(450, this.ctx.currentTime);
        osc.frequency.linearRampToValueAtTime(90, this.ctx.currentTime + 0.6);
        gain.gain.setValueAtTime(0.3, this.ctx.currentTime);
        gain.gain.linearRampToValueAtTime(0.01, this.ctx.currentTime + 0.6);
        osc.connect(gain);
        gain.connect(this.ctx.destination);
        osc.start();
        osc.stop(this.ctx.currentTime + 0.6);
      } catch (e) {}
    }

    playClear() {
      if (!this.enabled || !this.ctx) return;
      try {
        const notes = [523.25, 659.25, 783.99, 1046.50];
        const now = this.ctx.currentTime;
        notes.forEach((freq, idx) => {
          const osc = this.ctx.createOscillator();
          const gain = this.ctx.createGain();
          osc.type = 'square';
          osc.frequency.setValueAtTime(freq, now + idx * 0.12);
          gain.gain.setValueAtTime(0.18, now + idx * 0.12);
          gain.gain.exponentialRampToValueAtTime(0.01, now + idx * 0.12 + 0.18);
          osc.connect(gain);
          gain.connect(this.ctx.destination);
          osc.start(now + idx * 0.12);
          osc.stop(now + idx * 0.12 + 0.2);
        });
      } catch (e) {}
    }
  }

  const audio = new RetroSoundEngine();

  // 4. 입력 관리 시스템
  const keys = {
    left: false,
    right: false,
    up: false,
    down: false,
    space: false,
    spacePressedThisFrame: false
  };

  window.addEventListener('keydown', (e) => {
    audio.init();
    if (e.code === 'ArrowLeft' || e.code === 'KeyA') keys.left = true;
    if (e.code === 'ArrowRight' || e.code === 'KeyD') keys.right = true;
    if (e.code === 'ArrowUp' || e.code === 'KeyW') keys.up = true;
    if (e.code === 'ArrowDown' || e.code === 'KeyS') keys.down = true;
    if (e.code === 'Space') {
      if (!keys.space) keys.spacePressedThisFrame = true;
      keys.space = true;
      e.preventDefault();
    }
  });

  window.addEventListener('keyup', (e) => {
    if (e.code === 'ArrowLeft' || e.code === 'KeyA') keys.left = false;
    if (e.code === 'ArrowRight' || e.code === 'KeyD') keys.right = false;
    if (e.code === 'ArrowUp' || e.code === 'KeyW') keys.up = false;
    if (e.code === 'ArrowDown' || e.code === 'KeyS') keys.down = false;
    if (e.code === 'Space') keys.space = false;
  });

  // 터치 컨트롤 바인딩
  function bindTouch(element, action) {
    if (!element) return;
    const activate = (e) => {
      e.preventDefault();
      audio.init();
      if (action === 'space') {
        if (!keys.space) keys.spacePressedThisFrame = true;
        keys.space = true;
      } else {
        keys[action] = true;
      }
      element.classList.add('active');
    };
    const deactivate = (e) => {
      e.preventDefault();
      if (action === 'space') {
        keys.space = false;
      } else {
        keys[action] = false;
      }
      element.classList.remove('active');
    };

    element.addEventListener('touchstart', activate, { passive: false });
    element.addEventListener('touchend', deactivate, { passive: false });
    element.addEventListener('mousedown', activate);
    element.addEventListener('mouseup', deactivate);
    element.addEventListener('mouseleave', deactivate);
  }

  bindTouch(touchUp, 'up');
  bindTouch(touchDown, 'down');
  bindTouch(touchLeft, 'left');
  bindTouch(touchRight, 'right');
  bindTouch(touchJump, 'space');

  // 5. 스테이지 맵 데이터
  // 캔버스 크기: 800 x 600
  // 각 층 바닥 Y: 530 (1층 바닥), 430 (2층), 330 (3층), 230 (4층), 130 (5층 꼭대기)
  const STAGES = [
    // [Stage 1] 입문 코스
    {
      stageNum: 1,
      name: "초원 언덕",
      platforms: [
        { x: 30, y: 530, w: 740, h: 18 }, // 1층
        { x: 70, y: 430, w: 660, h: 18 }, // 2층
        { x: 70, y: 330, w: 660, h: 18 }, // 3층
        { x: 70, y: 230, w: 660, h: 18 }, // 4층
        { x: 160, y: 130, w: 480, h: 18 } // 5층 (정상)
      ],
      ladders: [
        { x: 620, y: 430, h: 100 }, // 1 -> 2층 우측
        { x: 150, y: 330, h: 100 }, // 2 -> 3층 좌측
        { x: 590, y: 230, h: 100 }, // 3 -> 4층 우측
        { x: 260, y: 130, h: 100 }  // 4 -> 5층 좌측
      ],
      spikes: [
        { x: 320, y: 514 },
        { x: 480, y: 514 },
        { x: 380, y: 414 },
        { x: 300, y: 314 },
        { x: 440, y: 214 }
      ],
      snakes: [
        { x: 220, y: 410, minX: 180, maxX: 460, speed: 1.2, dir: 1 },
        { x: 400, y: 310, minX: 280, maxX: 560, speed: 1.4, dir: -1 }
      ],
      foods: [
        { x: 120, y: 504, type: 'carrot', points: 100 },
        { x: 420, y: 504, type: 'apple', points: 100 },
        { x: 250, y: 404, type: 'mushroom', points: 150 },
        { x: 520, y: 404, type: 'grape', points: 150 },
        { x: 220, y: 304, type: 'carrot', points: 100 },
        { x: 480, y: 304, type: 'apple', points: 100 },
        { x: 200, y: 204, type: 'radish', points: 200 },
        { x: 500, y: 204, type: 'mushroom', points: 150 },
        { x: 340, y: 104, type: 'watermelon', points: 500 }
      ],
      spawn: { x: 70, y: 500 }
    },

    // [Stage 2] 중급 코스
    {
      stageNum: 2,
      name: "밤의 사원",
      platforms: [
        { x: 30, y: 530, w: 740, h: 18 },
        { x: 80, y: 430, w: 320, h: 18 },
        { x: 440, y: 430, w: 300, h: 18 },
        { x: 60, y: 330, w: 680, h: 18 },
        { x: 140, y: 230, w: 520, h: 18 },
        { x: 220, y: 130, w: 360, h: 18 }
      ],
      ladders: [
        { x: 180, y: 430, h: 100 },
        { x: 600, y: 430, h: 100 },
        { x: 300, y: 330, h: 100 },
        { x: 520, y: 330, h: 100 },
        { x: 220, y: 230, h: 100 },
        { x: 420, y: 130, h: 100 }
      ],
      spikes: [
        { x: 260, y: 514 },
        { x: 420, y: 514 },
        { x: 600, y: 514 },
        { x: 220, y: 414 },
        { x: 240, y: 314 },
        { x: 420, y: 314 },
        { x: 340, y: 214 },
        { x: 480, y: 214 }
      ],
      snakes: [
        { x: 350, y: 510, minX: 180, maxX: 560, speed: 1.6, dir: 1 },
        { x: 180, y: 310, minX: 100, maxX: 400, speed: 1.5, dir: -1 },
        { x: 360, y: 210, minX: 200, maxX: 560, speed: 1.8, dir: 1 }
      ],
      foods: [
        { x: 100, y: 504, type: 'apple', points: 100 },
        { x: 340, y: 504, type: 'grape', points: 150 },
        { x: 680, y: 504, type: 'carrot', points: 100 },
        { x: 260, y: 404, type: 'mushroom', points: 150 },
        { x: 660, y: 404, type: 'radish', points: 200 },
        { x: 160, y: 304, type: 'apple', points: 100 },
        { x: 500, y: 304, type: 'grape', points: 150 },
        { x: 280, y: 204, type: 'watermelon', points: 300 },
        { x: 440, y: 204, type: 'carrot', points: 100 },
        { x: 380, y: 104, type: 'watermelon', points: 500 }
      ],
      spawn: { x: 70, y: 500 }
    },

    // [Stage 3] 고수 코스
    {
      stageNum: 3,
      name: "오로라 첨탑",
      platforms: [
        { x: 30, y: 530, w: 740, h: 18 },
        { x: 90, y: 430, w: 620, h: 18 },
        { x: 60, y: 330, w: 680, h: 18 },
        { x: 100, y: 230, w: 600, h: 18 },
        { x: 240, y: 130, w: 320, h: 18 }
      ],
      ladders: [
        { x: 640, y: 430, h: 100 },
        { x: 160, y: 330, h: 100 },
        { x: 600, y: 230, h: 100 },
        { x: 380, y: 130, h: 100 }
      ],
      spikes: [
        { x: 240, y: 514 },
        { x: 380, y: 514 },
        { x: 520, y: 514 },
        { x: 280, y: 414 },
        { x: 440, y: 414 },
        { x: 220, y: 314 },
        { x: 380, y: 314 },
        { x: 500, y: 314 },
        { x: 260, y: 214 },
        { x: 460, y: 214 }
      ],
      snakes: [
        { x: 300, y: 510, minX: 100, maxX: 650, speed: 2.1, dir: 1 },
        { x: 360, y: 410, minX: 160, maxX: 580, speed: 2.0, dir: -1 },
        { x: 420, y: 310, minX: 120, maxX: 620, speed: 2.2, dir: 1 },
        { x: 320, y: 210, minX: 180, maxX: 540, speed: 2.2, dir: -1 }
      ],
      foods: [
        { x: 140, y: 504, type: 'watermelon', points: 200 },
        { x: 440, y: 504, type: 'apple', points: 100 },
        { x: 340, y: 404, type: 'grape', points: 150 },
        { x: 560, y: 404, type: 'radish', points: 200 },
        { x: 260, y: 304, type: 'mushroom', points: 150 },
        { x: 460, y: 304, type: 'carrot', points: 100 },
        { x: 300, y: 204, type: 'grape', points: 150 },
        { x: 540, y: 204, type: 'watermelon', points: 300 },
        { x: 380, y: 104, type: 'watermelon', points: 1000 }
      ],
      spawn: { x: 70, y: 500 }
    }
  ];

  // 6. 너구리 플레이어 클래스
  class RaccoonPlayer {
    constructor() {
      this.w = 26;
      this.h = 32;
      this.reset();
    }

    reset() {
      this.x = 70;
      this.y = 500;
      this.vx = 0;
      this.vy = 0;
      this.facing = 1; // 1: 오른쪽, -1: 왼쪽
      this.isGrounded = false;
      this.isJumping = false;
      this.isClimbing = false;
      this.isDead = false;
      this.deadTimer = 0;
      this.animTick = 0;
      this.walkFrame = 0;
    }

    respawn(spawnPos) {
      this.x = spawnPos.x;
      this.y = spawnPos.y;
      this.vx = 0;
      this.vy = 0;
      this.isGrounded = true;
      this.isJumping = false;
      this.isClimbing = false;
      this.isDead = false;
      this.deadTimer = 0;
    }

    update(stage) {
      // 사망 모션 처리 (위로 튀어올랐다가 낙하)
      if (this.isDead) {
        this.deadTimer++;
        this.y += this.vy;
        this.vy += 0.35;
        return;
      }

      this.animTick++;
      if (this.animTick % 6 === 0) {
        this.walkFrame = (this.walkFrame + 1) % 4;
      }

      // 사다리 감지
      const currentLadder = this.getNearbyLadder(stage.ladders);

      // 사다리 진입 판정
      if (currentLadder && !this.isJumping) {
        if (keys.up || keys.down) {
          this.isClimbing = true;
          this.isGrounded = false;
          // 사다리 중앙 정렬
          this.x = currentLadder.x + 12 - this.w / 2;
        }
      } else {
        this.isClimbing = false;
      }

      // --- 사다리 등반 로직 ---
      if (this.isClimbing && currentLadder) {
        this.vx = 0;
        this.vy = 0;

        if (keys.up) this.vy = -2.4;
        else if (keys.down) this.vy = 2.4;

        this.y += this.vy;

        // 사다리 상단 도달 (위층 발판에 안착)
        if (this.y + this.h <= currentLadder.y + 4) {
          this.y = currentLadder.y - this.h;
          this.isClimbing = false;
          this.isGrounded = true;
        }
        // 사다리 하단 도달 (아래층 발판에 안착)
        else if (this.y + this.h >= currentLadder.y + currentLadder.h) {
          this.y = currentLadder.y + currentLadder.h - this.h;
          this.isClimbing = false;
          this.isGrounded = true;
        }
        return;
      }

      // --- 일반 이동 및 점프 로직 ---
      // 점프 중에는 방향 전환 불가능 (너구리 게임 특유의 조작감)
      if (this.isGrounded) {
        this.vx = 0;
        if (keys.left) {
          this.vx = -3.2;
          this.facing = -1;
        } else if (keys.right) {
          this.vx = 3.2;
          this.facing = 1;
        }

        // 스페이스바 점프 개시
        if (keys.spacePressedThisFrame) {
          this.isJumping = true;
          this.isGrounded = false;
          this.vy = -8.2; // 수직 도약력
          // 걷는 도중이면 이동 방향으로 포물선 점프, 멈춰있으면 수직 점프
          this.jumpVx = this.vx !== 0 ? this.facing * 3.4 : 0;
          audio.playJump();
        }
      } else {
        // 공중 점프 진행 중: 발동 시점의 수평 속도 유지
        this.vx = this.jumpVx;
        // 중력 적용
        this.vy += 0.42;
      }

      // 위치 갱신
      this.x += this.vx;
      this.y += this.vy;

      // 캔버스 좌우 벽 충돌
      if (this.x < 10) this.x = 10;
      if (this.x + this.w > 790) this.x = 790 - this.w;

      // 플랫폼 착지 검사
      this.isGrounded = false;
      for (const plat of stage.platforms) {
        // 발이 플랫폼 상단 라인을 통과하려 할 때만 위에서 착지
        const prevFootY = this.y + this.h - this.vy;
        const currentFootY = this.y + this.h;

        if (this.x + this.w * 0.7 > plat.x && this.x + this.w * 0.3 < plat.x + plat.w) {
          if (prevFootY <= plat.y + 6 && currentFootY >= plat.y && this.vy >= 0) {
            this.y = plat.y - this.h;
            this.vy = 0;
            this.isGrounded = true;
            this.isJumping = false;
            this.jumpVx = 0;
            break;
          }
        }
      }

      // 화면 바닥 낙하 사망
      if (this.y > 620) {
        this.die();
      }
    }

    getNearbyLadder(ladders) {
      const centerX = this.x + this.w / 2;
      const footY = this.y + this.h;

      for (const lad of ladders) {
        if (centerX >= lad.x - 4 && centerX <= lad.x + 28) {
          if (footY >= lad.y && this.y <= lad.y + lad.h + 6) {
            return lad;
          }
        }
      }
      return null;
    }

    die() {
      if (this.isDead) return;
      this.isDead = true;
      this.vy = -7.5; // 위로 튀어오름
      audio.playDie();
    }

    // 픽셀 아트 렌더링 (도트 감성의 너구리)
    draw(ctx) {
      ctx.save();
      ctx.translate(Math.round(this.x), Math.round(this.y));

      // 방향에 따른 반전
      if (this.facing === -1) {
        ctx.scale(-1, 1);
        ctx.translate(-this.w, 0);
      }

      const w = this.w;
      const h = this.h;

      // 사망 연출
      if (this.isDead) {
        // 찌릿한 사망 스프라이트
        ctx.fillStyle = '#ff3366';
        ctx.fillRect(4, 8, w - 8, h - 12);
        // X자 눈
        ctx.fillStyle = '#ffffff';
        ctx.font = '10px monospace';
        ctx.fillText('X X', 6, 16);
        ctx.restore();
        return;
      }

      // 꼬리 (너구리의 상징: 줄무늬 꼬리)
      const tailOffset = (this.isGrounded && this.vx !== 0) ? (this.walkFrame % 2 === 0 ? 2 : -2) : 0;
      ctx.fillStyle = '#8B5A2B';
      ctx.fillRect(-6, 16 + tailOffset, 8, 12);
      ctx.fillStyle = '#3E2723';
      ctx.fillRect(-4, 18 + tailOffset, 4, 3);
      ctx.fillRect(-4, 23 + tailOffset, 4, 3);

      // 몸통 (갈색 털 & 밝은 배)
      ctx.fillStyle = '#9C6644';
      ctx.fillRect(4, 12, w - 8, 14);
      ctx.fillStyle = '#E6CCB2';
      ctx.fillRect(7, 15, w - 14, 10);

      // 머리
      ctx.fillStyle = '#7F4F24';
      ctx.fillRect(2, 2, w - 4, 12);

      // 귀 (쫑긋한 귀 2개)
      ctx.fillStyle = '#582F0E';
      ctx.fillRect(2, -2, 6, 5);
      ctx.fillRect(w - 8, -2, 6, 5);
      ctx.fillStyle = '#E6CCB2';
      ctx.fillRect(4, 0, 3, 3);
      ctx.fillRect(w - 7, 0, 3, 3);

      // 너구리 특유의 눈가 검은 마스크
      ctx.fillStyle = '#2B1704';
      ctx.fillRect(4, 5, 6, 4);
      ctx.fillRect(w - 10, 5, 6, 4);

      // 눈
      ctx.fillStyle = '#FFFFFF';
      ctx.fillRect(7, 6, 3, 3);
      ctx.fillRect(w - 7, 6, 3, 3);
      ctx.fillStyle = '#000000';
      ctx.fillRect(8, 7, 2, 2);
      ctx.fillRect(w - 6, 7, 2, 2);

      // 코
      ctx.fillStyle = '#000000';
      ctx.fillRect(w / 2 - 2, 9, 4, 3);

      // 다리 & 발 (걷기 애니메이션)
      ctx.fillStyle = '#4A2810';
      if (this.isClimbing) {
        // 사다리 오를 때 번갈아 손발 움직임
        const climbAlt = (this.animTick % 8 < 4);
        ctx.fillRect(4, h - 8, 5, climbAlt ? 6 : 9);
        ctx.fillRect(w - 9, h - 8, 5, climbAlt ? 9 : 6);
      } else if (this.isJumping) {
        // 점프 시 웅크린 다리
        ctx.fillRect(3, h - 6, 6, 5);
        ctx.fillRect(w - 9, h - 6, 6, 5);
      } else if (this.vx !== 0) {
        // 걷기 4프레임
        if (this.walkFrame === 0 || this.walkFrame === 2) {
          ctx.fillRect(4, h - 6, 5, 6);
          ctx.fillRect(w - 9, h - 6, 5, 6);
        } else if (this.walkFrame === 1) {
          ctx.fillRect(2, h - 7, 5, 7);
          ctx.fillRect(w - 8, h - 5, 5, 5);
        } else {
          ctx.fillRect(6, h - 5, 5, 5);
          ctx.fillRect(w - 11, h - 7, 5, 7);
        }
      } else {
        // 정지 상태
        ctx.fillRect(4, h - 6, 5, 6);
        ctx.fillRect(w - 9, h - 6, 5, 6);
      }

      ctx.restore();
    }
  }

  // 7. 메인 게임 엔진
  class PonpokoGame {
    constructor() {
      this.player = new RaccoonPlayer();
      this.currentStageIdx = 0;
      this.score = 0;
      this.highScore = 5000;
      this.lives = 3;
      this.state = 'TITLE'; // TITLE, PLAYING, RESPAWNING, STAGE_CLEAR, GAME_OVER
      this.stateTimer = 0;
      this.stage = null;
      this.loadStage(0);
    }

    loadStage(idx) {
      this.currentStageIdx = idx % STAGES.length;
      const raw = STAGES[this.currentStageIdx];
      // 딥 카피로 원본 보존
      this.stage = {
        stageNum: raw.stageNum,
        name: raw.name,
        platforms: raw.platforms.map(p => ({ ...p })),
        ladders: raw.ladders.map(l => ({ ...l })),
        spikes: raw.spikes.map(s => ({ ...s })),
        snakes: raw.snakes.map(sn => ({ ...sn })),
        foods: raw.foods.map(f => ({ ...f, collected: false })),
        spawn: { ...raw.spawn }
      };
      this.player.respawn(this.stage.spawn);
      stageValEl.textContent = this.stage.stageNum;
    }

    start() {
      this.score = 0;
      this.lives = 3;
      this.loadStage(0);
      this.state = 'PLAYING';
      this.updateHUD();
      gameOverlay.classList.remove('active');
    }

    restart() {
      this.start();
    }

    updateHUD() {
      scoreValEl.textContent = String(this.score).padStart(5, '0');
      if (this.score > this.highScore) {
        this.highScore = this.score;
      }
      highScoreValEl.textContent = String(this.highScore).padStart(5, '0');

      // 목숨 아이콘
      livesContainerEl.innerHTML = '';
      for (let i = 0; i < this.lives; i++) {
        const icon = document.createElement('span');
        icon.textContent = '🦝';
        livesContainerEl.appendChild(icon);
      }
    }

    update() {
      if (this.state === 'TITLE') return;

      // 뱀(Snakes) AI 순찰
      for (const snake of this.stage.snakes) {
        snake.x += snake.speed * snake.dir;
        if (snake.x <= snake.minX) {
          snake.x = snake.minX;
          snake.dir = 1;
        } else if (snake.x >= snake.maxX) {
          snake.x = snake.maxX;
          snake.dir = -1;
        }
      }

      // 플레이어 업데이트
      this.player.update(this.stage);

      // 사망 후 리스폰 대기 로직
      if (this.player.isDead) {
        if (this.player.deadTimer > 70) {
          this.lives--;
          this.updateHUD();

          if (this.lives <= 0) {
            this.state = 'GAME_OVER';
            overlayTitle.textContent = 'GAME OVER';
            overlayTitle.style.color = '#ff0055';
            overlayMsg.innerHTML = `최종 점수: <strong>${this.score}점</strong><br>다시 도전하여 최고 기록을 경신해 보세요!`;
            btnStart.textContent = 'PLAY AGAIN';
            gameOverlay.classList.add('active');
          } else {
            this.player.respawn(this.stage.spawn);
          }
        }
        return;
      }

      // 충돌 검사 1: 음식(Fruit) 섭취
      const pBox = {
        x: this.player.x + 3,
        y: this.player.y + 4,
        w: this.player.w - 6,
        h: this.player.h - 6
      };

      let uncollectedCount = 0;
      for (const food of this.stage.foods) {
        if (!food.collected) {
          uncollectedCount++;
          // 음식 크기 18x18
          if (
            pBox.x < food.x + 18 &&
            pBox.x + pBox.w > food.x &&
            pBox.y < food.y + 18 &&
            pBox.y + pBox.h > food.y
          ) {
            food.collected = true;
            this.score += food.points;
            this.updateHUD();
            audio.playEat();
          }
        }
      }

      // 모든 음식을 다 먹으면 스테이지 클리어!
      if (uncollectedCount === 0 && this.state === 'PLAYING') {
        this.state = 'STAGE_CLEAR';
        this.stateTimer = 0;
        audio.playClear();
      }

      if (this.state === 'STAGE_CLEAR') {
        this.stateTimer++;
        if (this.stateTimer > 90) {
          if (this.currentStageIdx + 1 < STAGES.length) {
            this.loadStage(this.currentStageIdx + 1);
            this.state = 'PLAYING';
          } else {
            // ALL STAGES CLEAR!
            this.state = 'ALL_CLEAR';
            overlayTitle.textContent = 'ALL CLEAR!';
            overlayTitle.style.color = '#ffe600';
            overlayMsg.innerHTML = `🎉 축하합니다! 모든 스테이지를 정복했습니다!<br>최종 점수: <strong>${this.score}점</strong>`;
            btnStart.textContent = 'CHALLENGE AGAIN';
            gameOverlay.classList.add('active');
          }
        }
        return;
      }

      // 충돌 검사 2: 압정(Spikes)
      for (const spike of this.stage.spikes) {
        // 압정 히트박스 (바닥 삼각형 형태)
        if (
          pBox.x < spike.x + 16 &&
          pBox.x + pBox.w > spike.x + 2 &&
          pBox.y + pBox.h > spike.y + 2 &&
          pBox.y < spike.y + 16
        ) {
          this.player.die();
          break;
        }
      }

      // 충돌 검사 3: 뱀(Snakes)
      for (const snake of this.stage.snakes) {
        const sBox = { x: snake.x, y: snake.y, w: 26, h: 18 };
        if (
          pBox.x < sBox.x + sBox.w &&
          pBox.x + pBox.w > sBox.x &&
          pBox.y < sBox.y + sBox.h &&
          pBox.y + pBox.h > sBox.y
        ) {
          this.player.die();
          break;
        }
      }

      // 프레임 플래그 리셋
      keys.spacePressedThisFrame = false;
    }

    draw() {
      // 캔버스 배경 (어두운 밤하늘)
      ctx.fillStyle = '#080a14';
      ctx.fillRect(0, 0, canvas.width, canvas.height);

      // 레트로 별빛 배경
      ctx.fillStyle = 'rgba(255, 255, 255, 0.4)';
      for (let i = 0; i < 35; i++) {
        const sx = (i * 97 + 13) % 800;
        const sy = (i * 71 + 29) % 550;
        ctx.fillRect(sx, sy, 2, 2);
      }

      // 1. 사다리 그리기 (원작 특유의 파란/하늘색 사다리)
      for (const lad of this.stage.ladders) {
        ctx.fillStyle = '#00e5ff';
        // 기둥 2개
        ctx.fillRect(lad.x, lad.y, 4, lad.h);
        ctx.fillRect(lad.x + 20, lad.y, 4, lad.h);
        // 발판 가로대들
        ctx.fillStyle = '#ffffff';
        for (let r = lad.y + 10; r < lad.y + lad.h; r += 14) {
          ctx.fillRect(lad.x + 4, r, 16, 3);
        }
      }

      // 2. 플랫폼 (벽돌 무늬) 그리기
      for (const plat of this.stage.platforms) {
        // 벽돌 메인
        ctx.fillStyle = '#b23b23';
        ctx.fillRect(plat.x, plat.y, plat.w, plat.h);
        // 벽돌 상단 하이라이트 잔디/라인
        ctx.fillStyle = '#2eb85c';
        ctx.fillRect(plat.x, plat.y, plat.w, 4);
        // 벽돌 줄눈 무늬
        ctx.fillStyle = '#541204';
        for (let bx = plat.x; bx < plat.x + plat.w; bx += 24) {
          ctx.fillRect(bx, plat.y + 4, 2, plat.h - 4);
        }
      }

      // 3. 압정 (Spikes) 그리기
      for (const spike of this.stage.spikes) {
        ctx.save();
        ctx.translate(spike.x, spike.y);
        // 뾰족한 은빛 침
        ctx.fillStyle = '#e2e8f0';
        ctx.beginPath();
        ctx.moveTo(9, 0);
        ctx.lineTo(17, 16);
        ctx.lineTo(1, 16);
        ctx.closePath();
        ctx.fill();
        // 빨간 밑받침
        ctx.fillStyle = '#ff0055';
        ctx.fillRect(0, 14, 18, 4);
        ctx.restore();
      }

      // 4. 뱀 (Snakes) 그리기
      const tick = Math.floor(Date.now() / 150);
      for (const snake of this.stage.snakes) {
        ctx.save();
        ctx.translate(Math.round(snake.x), Math.round(snake.y));
        if (snake.dir === -1) {
          ctx.scale(-1, 1);
          ctx.translate(-26, 0);
        }

        // 뱀 몸통 꿈틀거림 (2프레임 애니메이션)
        const wave = tick % 2 === 0 ? 2 : -2;
        ctx.fillStyle = '#00ff88';
        ctx.fillRect(4, 6 + wave, 18, 8);
        ctx.fillStyle = '#00bb55';
        ctx.fillRect(8, 8 + wave, 12, 4);

        // 뱀 머리
        ctx.fillStyle = '#00ff88';
        ctx.fillRect(20, 2, 8, 12);
        // 뱀 눈
        ctx.fillStyle = '#ffffff';
        ctx.fillRect(24, 4, 3, 3);
        ctx.fillStyle = '#000000';
        ctx.fillRect(25, 5, 2, 2);
        // 붉은 혓바닥
        if (tick % 2 === 0) {
          ctx.fillStyle = '#ff0033';
          ctx.fillRect(28, 9, 5, 2);
        }

        ctx.restore();
      }

      // 5. 음식 (Foods) 그리기
      for (const food of this.stage.foods) {
        if (food.collected) continue;
        ctx.save();
        ctx.translate(food.x, food.y);

        if (food.type === 'apple') {
          // 빨간 사과
          ctx.fillStyle = '#ff2a4b';
          ctx.beginPath();
          ctx.arc(9, 10, 8, 0, Math.PI * 2);
          ctx.fill();
          // 꼭지와 잎사귀
          ctx.fillStyle = '#2eb85c';
          ctx.fillRect(9, 1, 4, 3);
          ctx.fillStyle = '#5c3a21';
          ctx.fillRect(8, 1, 2, 4);
        } else if (food.type === 'carrot') {
          // 주황 당근
          ctx.fillStyle = '#ff7700';
          ctx.beginPath();
          ctx.moveTo(9, 18);
          ctx.lineTo(16, 4);
          ctx.lineTo(2, 4);
          ctx.closePath();
          ctx.fill();
          // 풀잎
          ctx.fillStyle = '#00ff66';
          ctx.fillRect(7, 0, 4, 4);
        } else if (food.type === 'mushroom') {
          // 버섯
          ctx.fillStyle = '#ff3366';
          ctx.beginPath();
          ctx.arc(9, 8, 8, Math.PI, 0);
          ctx.fill();
          ctx.fillStyle = '#ffffff';
          ctx.fillRect(7, 5, 3, 3);
          ctx.fillRect(12, 4, 2, 2);
          // 기둥
          ctx.fillStyle = '#f7fafc';
          ctx.fillRect(6, 8, 6, 8);
        } else if (food.type === 'grape') {
          // 포도송이
          ctx.fillStyle = '#a855f7';
          ctx.beginPath();
          ctx.arc(6, 7, 4, 0, Math.PI * 2);
          ctx.arc(12, 7, 4, 0, Math.PI * 2);
          ctx.arc(9, 12, 4, 0, Math.PI * 2);
          ctx.fill();
          ctx.fillStyle = '#2eb85c';
          ctx.fillRect(8, 1, 3, 3);
        } else {
          // 수박 / 기타 (초록 바탕 줄무늬)
          ctx.fillStyle = '#10b981';
          ctx.beginPath();
          ctx.arc(9, 9, 8, 0, Math.PI * 2);
          ctx.fill();
          ctx.fillStyle = '#064e3b';
          ctx.fillRect(6, 3, 2, 12);
          ctx.fillRect(11, 3, 2, 12);
        }

        ctx.restore();
      }

      // 6. 플레이어 너구리 그리기
      this.player.draw(ctx);

      // 7. 스테이지 클리어 연출
      if (this.state === 'STAGE_CLEAR') {
        ctx.fillStyle = 'rgba(0, 0, 0, 0.6)';
        ctx.fillRect(0, 240, 800, 110);
        ctx.fillStyle = '#ffe600';
        ctx.font = '24px "Press Start 2P", monospace';
        ctx.textAlign = 'center';
        ctx.fillText('STAGE CLEAR!', 400, 305);
      }
    }

    loop() {
      this.update();
      this.draw();
      requestAnimationFrame(() => this.loop());
    }
  }

  // 8. 게임 인스턴스 생성 및 이벤트 핸들러
  const game = new PonpokoGame();

  btnStart.addEventListener('click', () => {
    audio.init();
    game.start();
  });

  btnRestart.addEventListener('click', () => {
    audio.init();
    game.restart();
  });

  btnSound.addEventListener('click', () => {
    audio.init();
    audio.enabled = !audio.enabled;
    btnSound.textContent = audio.enabled ? '🔊 SOUND ON' : '🔈 SOUND OFF';
  });

  // 루프 시작
  game.loop();

})();
