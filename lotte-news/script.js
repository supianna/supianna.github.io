/**
 * 롯데자이언츠 뉴스 수집기 & AI 일일 보고서 웹 인터랙티브 데모 (script.js)
 * 
 * 기능:
 *  1. 마크다운 (.md) 파서 및 실시간 뷰어 렌더러
 *  2. 네이버 뉴스 API 수집 파이프라인 시뮬레이션 인터랙션
 *  3. OpenAI GPT-5.6-Luna 기반 날짜별/주간 종합 보고서 조회 및 생성
 *  4. 보고서 클립보드 복사, .md 파일 다운로드, 원본/뷰어 모드 토글
 *  5. 실제 수집 기사 데이터셋(218건) 실시간 검색 및 날짜 필터링
 */

// [상태 변수]
let currentMarkdown = "";
let currentFilename = "report_2026-09-09.md";
let currentFilterDate = "all";
let currentSearchQuery = "";
let isRawMode = false;

// [마크다운 파서]
function parseMarkdown(md) {
  if (!md) return "";

  // 줄 단위 파싱 및 변환
  const lines = md.split("\n");
  let html = [];
  let inList = false;
  let inBlockquote = false;
  let inTable = false;

  for (let i = 0; i < lines.length; i++) {
    let line = lines[i];

    // 헤더 (H1, H2, H3, H4)
    if (line.startsWith("# ")) {
      if (inList) { html.push("</ul>"); inList = false; }
      if (inBlockquote) { html.push("</blockquote>"); inBlockquote = false; }
      html.push(`<h1>${formatInline(line.substring(2))}</h1>`);
      continue;
    }
    if (line.startsWith("## ")) {
      if (inList) { html.push("</ul>"); inList = false; }
      if (inBlockquote) { html.push("</blockquote>"); inBlockquote = false; }
      html.push(`<h2>${formatInline(line.substring(3))}</h2>`);
      continue;
    }
    if (line.startsWith("### ")) {
      if (inList) { html.push("</ul>"); inList = false; }
      if (inBlockquote) { html.push("</blockquote>"); inBlockquote = false; }
      html.push(`<h3>${formatInline(line.substring(4))}</h3>`);
      continue;
    }
    if (line.startsWith("#### ")) {
      if (inList) { html.push("</ul>"); inList = false; }
      if (inBlockquote) { html.push("</blockquote>"); inBlockquote = false; }
      html.push(`<h4>${formatInline(line.substring(5))}</h4>`);
      continue;
    }

    // 인용문 (>)
    if (line.startsWith("> ")) {
      if (!inBlockquote) {
        html.push("<blockquote>");
        inBlockquote = true;
      }
      html.push(`<p>${formatInline(line.substring(2))}</p>`);
      continue;
    } else if (inBlockquote) {
      html.push("</blockquote>");
      inBlockquote = false;
    }

    // 리스트 (- 또는 * 또는 1.)
    const listMatch = line.match(/^(\s*)([-*]|\d+\.)\s+(.*)/);
    if (listMatch) {
      if (!inList) {
        html.push("<ul>");
        inList = true;
      }
      html.push(`<li>${formatInline(listMatch[3])}</li>`);
      continue;
    } else if (inList) {
      html.push("</ul>");
      inList = false;
    }

    // 수평 구분선 (---)
    if (/^---{2,}$/.test(line.trim())) {
      html.push("<hr>");
      continue;
    }

    // 테이블 (| ... |)
    if (line.trim().startsWith("|") && line.trim().endsWith("|")) {
      const cells = line.split("|").map(c => c.trim()).slice(1, -1);
      // 구분선인 경우 (|---|---|)
      if (cells.every(c => /^:?-+:?$/.test(c))) {
        continue;
      }
      if (!inTable) {
        html.push("<table><thead><tr>");
        cells.forEach(c => html.push(`<th>${formatInline(c)}</th>`));
        html.push("</tr></thead><tbody>");
        inTable = true;
      } else {
        html.push("<tr>");
        cells.forEach(c => html.push(`<td>${formatInline(c)}</td>`));
        html.push("</tr>");
      }
      continue;
    } else if (inTable) {
      html.push("</tbody></table>");
      inTable = false;
    }

    // 일반 문단
    if (line.trim().length > 0) {
      html.push(`<p>${formatInline(line)}</p>`);
    }
  }

  if (inList) html.push("</ul>");
  if (inBlockquote) html.push("</blockquote>");
  if (inTable) html.push("</tbody></table>");

  return html.join("\n");
}

// 인라인 포맷 (볼드, 이탤릭, 링크, 코드)
function formatInline(text) {
  return text
    .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
    .replace(/\*(.*?)\*/g, "<em>$1</em>")
    .replace(/`([^`]+)`/g, "<code>$1</code>")
    .replace(/\[(.*?)\]\((.*?)\)/g, '<a href="$2" target="_blank" rel="noopener noreferrer">$1 ↗</a>');
}

// [상태 헬퍼 함수]
function setStatus(text, type = "idle") {
  const statusBox = document.getElementById("reportStatus");
  const statusText = document.getElementById("reportStatusText");
  if (statusBox && statusText) {
    statusBox.className = `status-box ${type}`;
    statusText.textContent = text;
  }
}

function setCollectStatus(text, type = "idle") {
  const statusBox = document.getElementById("collectStatus");
  const statusText = document.getElementById("collectStatusText");
  if (statusBox && statusText) {
    statusBox.className = `status-box ${type}`;
    statusText.textContent = text;
  }
}

// [보고서 렌더링]
function renderReport(dateKey) {
  const reports = window.LOTTE_AI_REPORTS || {};
  const reportContentEl = document.getElementById("reportContent");
  const rawArea = document.getElementById("rawMarkdownArea");
  const fileInfo = document.getElementById("fileInfo");

  let markdown = "";
  let filename = "";

  if (dateKey === "weekly") {
    markdown = reports["weekly"] || "# 주간 종합 보고서\n\n수집된 주간 데이터가 없습니다.";
    filename = "report_weekly_2026-09-02_to_2026-09-09.md";
  } else {
    markdown = reports[dateKey];
    filename = `report_${dateKey}.md`;

    // 혹시 데이터셋에 없는 날짜일 경우 동적 합성
    if (!markdown) {
      markdown = generateFallbackReport(dateKey);
    }
  }

  currentMarkdown = markdown;
  currentFilename = filename;

  fileInfo.textContent = filename;
  rawArea.value = markdown;
  reportContentEl.innerHTML = parseMarkdown(markdown);

  if (isRawMode) {
    reportContentEl.style.display = "none";
    rawArea.style.display = "block";
  } else {
    reportContentEl.style.display = "block";
    rawArea.style.display = "none";
  }
}

// 등록되지 않은 날짜에 대한 자동 브리핑 생성
function generateFallbackReport(targetDate) {
  const articles = (window.LOTTE_NEWS_ARTICLES || []).filter(a => a.date.includes(targetDate.replace(/-/g, ".")));
  
  let articleListMd = "";
  if (articles.length === 0) {
    articleListMd = "- 해당 날짜에 수집된 기사가 존재하지 않습니다.";
  } else {
    articleListMd = articles.map((a, i) => `${i + 1}. [${a.title}](${a.link}) - ${a.date}`).join("\n");
  }

  return `# [롯데자이언츠] ${targetDate} 일일 뉴스 브리핑 보고서

> **생성 모델:** OpenAI \`gpt-5.6-luna\` (수석 스포츠 분석가 프롬프트)  
> **기준 날짜:** ${targetDate} | **수집 기사 수:** 총 ${articles.length}건

## 1. 당일 주요 이슈 및 핵심 성적 요약
${targetDate} 기준 롯데자이언츠 관련 보도 ${articles.length}건을 종합 분석한 결과, 선수단 전력 운용과 다음 경기 준비 및 팬들의 주요 관심사가 집중되었습니다.

## 2. 주요 경기 및 팀 동향 분석
선수들의 경기력 향상과 포지션별 집중 점검이 진행되고 있으며, 투타 균형을 맞추기 위한 현장 코칭스태프의 데이터 분석이 적극적으로 이루어지고 있습니다.

## 3. 참고 기사 목록 (수집 데이터)
${articleListMd}

---
*본 보고서는 NAVER API HUB 검색 API 및 OpenAI gpt-5.6-luna 모델을 통해 실시간 생성되었습니다.*`;
}

// [기사 데이터셋 테이블 렌더링]
function renderArticleTable() {
  const tbody = document.getElementById("articlesTableBody");
  const countBadge = document.getElementById("filteredArticleCount");
  const articles = window.LOTTE_NEWS_ARTICLES || [];

  const query = currentSearchQuery.toLowerCase().trim();

  const filtered = articles.filter(art => {
    // 날짜 필터
    const matchesDate = (currentFilterDate === "all") || art.date.includes(currentFilterDate);
    // 검색어 필터
    const matchesQuery = !query || 
      art.title.toLowerCase().includes(query) || 
      art.content.toLowerCase().includes(query);

    return matchesDate && matchesQuery;
  });

  countBadge.textContent = `${filtered.length}건 표시 중 (전체 ${articles.length}건)`;

  if (filtered.length === 0) {
    tbody.innerHTML = `
      <tr>
        <td colspan="4" style="text-align: center; padding: 40px; color: var(--text-muted);">
          일치하는 롯데자이언츠 뉴스 기사가 없습니다.
        </td>
      </tr>
    `;
    return;
  }

  tbody.innerHTML = filtered.map((art, idx) => `
    <tr>
      <td style="color: var(--text-muted); font-size: 12px;">${idx + 1}</td>
      <td style="font-size: 12.5px; white-space: nowrap; color: #94a3b8;">${art.date}</td>
      <td>
        <a href="${art.link}" target="_blank" rel="noopener noreferrer" class="article-row-title" title="${art.title}">
          ${art.title}
        </a>
      </td>
      <td style="text-align: center;">
        <a href="${art.link}" target="_blank" rel="noopener noreferrer" class="btn-link-out">
          원문 ↗
        </a>
      </td>
    </tr>
  `).join("");
}

// [DOM 초기화 및 이벤트 리스너]
document.addEventListener("DOMContentLoaded", () => {
  const collectWeekBtn = document.getElementById("collectWeekBtn");
  const reportBtn = document.getElementById("reportBtn");
  const weeklyReportBtn = document.getElementById("weeklyReportBtn");
  const targetDateInput = document.getElementById("targetDate");
  const dateSelect = document.getElementById("dateSelect");
  const toggleRawBtn = document.getElementById("toggleRawBtn");
  const copyMdBtn = document.getElementById("copyMdBtn");
  const downloadMdBtn = document.getElementById("downloadMdBtn");
  const articleSearchInput = document.getElementById("articleSearchInput");
  const dateFilterChips = document.getElementById("dateFilterChips");
  const collectStats = document.getElementById("collectStats");
  const collectProgressBar = document.getElementById("collectProgressBar");
  const progressBarFill = collectProgressBar.querySelector(".progress-bar-fill");

  // 초기 날짜 세팅 및 기본 렌더링 (최신 9월 9일 보고서 기본 탑재)
  renderReport("2026-09-09");
  renderArticleTable();

  // 날짜 입력창과 드롭다운 동기화
  dateSelect.addEventListener("change", (e) => {
    const val = e.target.value;
    if (val === "weekly") {
      targetDateInput.disabled = true;
    } else {
      targetDateInput.disabled = false;
      targetDateInput.value = val;
    }
  });

  targetDateInput.addEventListener("change", (e) => {
    const val = e.target.value;
    // 드롭다운에 일치하는 옵션이 있으면 선택
    let matched = false;
    for (let opt of dateSelect.options) {
      if (opt.value === val) {
        dateSelect.value = val;
        matched = true;
        break;
      }
    }
    if (!matched) {
      dateSelect.value = "";
    }
  });

  // 1. 지난 일주일 뉴스 자동 수집 버튼 인터랙션 (수집 시뮬레이션 파이프라인)
  collectWeekBtn.addEventListener("click", () => {
    collectWeekBtn.disabled = true;
    collectProgressBar.style.display = "block";
    progressBarFill.style.width = "10%";

    setCollectStatus("[1/4] NAVER API HUB 뉴스 검색 API 엔드포인트 연결 및 토큰 인증 중...", "loading");

    setTimeout(() => {
      progressBarFill.style.width = "40%";
      setCollectStatus("[2/4] '롯데' & '자이언츠' 메인 뉴스 검색 및 페이징 탐색 중 (start=1, 101, 201...)", "loading");
    }, 600);

    setTimeout(() => {
      progressBarFill.style.width = "75%";
      setCollectStatus("[3/4] 최근 7일(2026.09.03 ~ 2026.09.09) 기사 218건 필터링 및 본문 추출 완료...", "loading");
    }, 1200);

    setTimeout(() => {
      progressBarFill.style.width = "100%";
      setCollectStatus("수집 성공! 최근 일주일치 롯데자이언츠 뉴스 총 218건이 성공적으로 저장되었습니다.", "success");
      collectStats.style.display = "flex";
      collectWeekBtn.disabled = false;

      // 데이터셋 갱신
      renderArticleTable();
    }, 1800);
  });

  // 2. 특정 하루 날짜 AI 보고서 생성 버튼 인터랙션
  reportBtn.addEventListener("click", () => {
    let dateKey = targetDateInput.value;
    if (dateSelect.value === "weekly") {
      dateKey = "weekly";
    }

    if (!dateKey) {
      alert("분석할 날짜를 선택하거나 입력해 주세요.");
      return;
    }

    reportBtn.disabled = true;
    setStatus(`[1/3] [${dateKey}] 기사 데이터 로드 및 토큰 최적화 준비 중...`, "loading");

    setTimeout(() => {
      setStatus(`[2/3] OpenAI 'gpt-5.6-luna' 모델로 심층 스포츠 분석 프롬프트 전송...`, "loading");
    }, 500);

    setTimeout(() => {
      setStatus(`보고서 생성 완료! [${dateKey}] 롯데자이언츠 일일 브리핑이 성공적으로 렌더링되었습니다.`, "success");
      renderReport(dateKey);
      reportBtn.disabled = false;

      // 스크롤 부드럽게 미리보기 영역으로 이동
      document.querySelector(".preview-card").scrollIntoView({ behavior: "smooth", block: "start" });
    }, 1100);
  });

  // 주간 종합 브리핑 퀵 버튼
  weeklyReportBtn.addEventListener("click", () => {
    dateSelect.value = "weekly";
    targetDateInput.disabled = true;
    reportBtn.click();
  });

  // 마크다운 원본 / 뷰어 모드 토글
  toggleRawBtn.addEventListener("click", () => {
    isRawMode = !isRawMode;
    const reportContentEl = document.getElementById("reportContent");
    const rawArea = document.getElementById("rawMarkdownArea");

    if (isRawMode) {
      reportContentEl.style.display = "none";
      rawArea.style.display = "block";
      toggleRawBtn.innerHTML = `<span class="tool-icon">👁️</span> 뷰어 보기`;
    } else {
      reportContentEl.style.display = "block";
      rawArea.style.display = "none";
      toggleRawBtn.innerHTML = `<span class="tool-icon">📄</span> 원본/뷰어 전환`;
    }
  });

  // 클립보드 복사
  copyMdBtn.addEventListener("click", async () => {
    if (!currentMarkdown) return;
    try {
      await navigator.clipboard.writeText(currentMarkdown);
      const originalText = copyMdBtn.innerHTML;
      copyMdBtn.innerHTML = `<span class="tool-icon">✅</span> 복사 완료!`;
      setTimeout(() => {
        copyMdBtn.innerHTML = originalText;
      }, 1800);
    } catch (err) {
      alert("클립보드 복사 권한이 없습니다.");
    }
  });

  // .md 파일 다운로드
  downloadMdBtn.addEventListener("click", () => {
    if (!currentMarkdown) return;
    const blob = new Blob([currentMarkdown], { type: "text/markdown;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = currentFilename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  });

  // 검색어 입력 실시간 필터
  articleSearchInput.addEventListener("input", (e) => {
    currentSearchQuery = e.target.value;
    renderArticleTable();
  });

  // 날짜 필터 칩 클릭 핸들러
  dateFilterChips.addEventListener("click", (e) => {
    if (e.target.classList.contains("chip-btn")) {
      dateFilterChips.querySelectorAll(".chip-btn").forEach(btn => btn.classList.remove("active"));
      e.target.classList.add("active");
      currentFilterDate = e.target.dataset.date;
      renderArticleTable();
    }
  });
});
