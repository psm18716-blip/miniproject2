/* analysis.js */
const BLUE   = '#2563eb';
const BLUE_L = 'rgba(37,99,235,0.12)';
const COLORS = ['#2563eb','#7c3aed','#059669','#d97706','#dc2626',
                '#0891b2','#65a30d','#9333ea','#e11d48','#0f766e'];

Chart.defaults.font.family = "'Pretendard', sans-serif";
Chart.defaults.color = '#9ca3af';

function buildBrandChart() {
    new Chart(document.getElementById('brandChart'), {
        type: 'bar',
        data: {
            labels: BRAND_LABELS,
            datasets: [{
                label: '평균 시세 (만원)',
                data: BRAND_PRICES,
                backgroundColor: COLORS,
                borderRadius: 6,
                borderSkipped: false,
            }]
        },
        options: {
            indexAxis: 'y',
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        label: ctx => ` 평균 ${ctx.parsed.x.toLocaleString()}만원 · ${BRAND_COUNTS[ctx.dataIndex].toLocaleString()}대`
                    }
                }
            },
            scales: {
                x: { grid: { color: '#f3f4f6' }, ticks: { callback: v => v.toLocaleString() + '만' } },
                y: { grid: { display: false }, ticks: { autoSkip: false } }
            }
        }
    });
}

function buildFuelChart() {
    new Chart(document.getElementById('fuelChart'), {
        type: 'bar',
        data: {
            labels: FUEL_LABELS,
            datasets: [{
                data: FUEL_COUNTS,
                backgroundColor: COLORS,
                borderRadius: 6,
                borderSkipped: false,
            }]
        },
        options: {
            indexAxis: 'y',
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: { callbacks: { label: ctx => ` ${ctx.parsed.x.toLocaleString()}대` } }
            },
            scales: {
                x: { grid: { color: '#f3f4f6' }, ticks: { callback: v => v.toLocaleString() + '대' } },
                y: { grid: { display: false }, ticks: { autoSkip: false, maxRotation: 0 } }
            }
        }
    });
}

function buildYearChart() {
    new Chart(document.getElementById('yearChart'), {
        type: 'line',
        data: {
            labels: YEAR_LABELS,
            datasets: [{
                label: '평균 시세 (만원)',
                data: YEAR_PRICES,
                borderColor: BLUE,
                backgroundColor: BLUE_L,
                fill: true,
                tension: 0.4,
                pointBackgroundColor: BLUE,
                pointBorderColor: '#fff',
                pointBorderWidth: 2,
                pointRadius: 5,
                pointHoverRadius: 7,
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: { callbacks: { label: ctx => ` 평균 ${ctx.parsed.y.toLocaleString()}만원` } }
            },
            scales: {
                x: { grid: { display: false } },
                y: { beginAtZero: false, grid: { color: '#f3f4f6' }, ticks: { callback: v => v.toLocaleString() + '만' } }
            }
        }
    });
}

function buildPriceDistChart() {
    new Chart(document.getElementById('priceDistChart'), {
        type: 'bar',
        data: {
            labels: PD_LABELS,
            datasets: [{
                label: '매물 수',
                data: PD_COUNTS,
                backgroundColor: COLORS,
                borderRadius: 8,
                borderSkipped: false,
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: { callbacks: { label: ctx => ` ${ctx.parsed.y.toLocaleString()}대` } }
            },
            scales: {
                x: { grid: { display: false } },
                y: { grid: { color: '#f3f4f6' }, ticks: { callback: v => v.toLocaleString() + '대' } }
            }
        }
    });
}

/* ── 브랜드별 감가율 차트 ── */
const DEP_BRANDS      = Object.keys(DEP_DATA);
const COLORS_DEP      = ['#2563eb','#7c3aed','#059669','#d97706','#dc2626',
                          '#0891b2','#65a30d','#9333ea','#e11d48','#0f766e'];
const depActiveBrands = new Set(DEP_BRANDS.slice(0, 3));
let depChart = null;

function buildDepChart() {
    const activeBrands = DEP_BRANDS.filter(b => depActiveBrands.has(b));
    const datasets = activeBrands.map(b => {
        const idx = DEP_BRANDS.indexOf(b);
        const color = COLORS_DEP[idx % COLORS_DEP.length];
        return {
            label: b,
            data: DEP_DATA[b].years.map((y, j) => ({ x: y, y: DEP_DATA[b].prices[j] })),
            borderColor: color,
            backgroundColor: 'transparent',
            tension: 0.3, pointRadius: 4, pointHoverRadius: 7, borderWidth: 2,
        };
    });
    if (depChart) depChart.destroy();
    depChart = new Chart(document.getElementById('depChart'), {
        type: 'line',
        data: { datasets },
        options: {
            responsive: true, maintainAspectRatio: false, parsing: false,
            plugins: {
                legend: { display: false },
                tooltip: { callbacks: { label: ctx => ` ${ctx.dataset.label}: ${ctx.parsed.y.toLocaleString()}만원` } }
            },
            scales: {
                x: { type: 'linear', ticks: { stepSize: 1, callback: v => v + '년' }, grid: { display: false } },
                y: { grid: { color: '#f3f4f6' }, ticks: { callback: v => v.toLocaleString() + '만' } }
            }
        }
    });
}

function highlightDepBrand(focusBrand) {
    if (!depChart) return;
    depChart.data.datasets.forEach(ds => {
        const isFocused = (focusBrand === null) || ds.label === focusBrand;
        const idx = DEP_BRANDS.indexOf(ds.label);
        const color = COLORS_DEP[idx % COLORS_DEP.length];
        ds.borderColor = isFocused ? color : color + '33';
        ds.borderWidth = isFocused ? 3 : 1;
        ds.pointRadius = isFocused ? 5 : 2;
    });
    depChart.update('none');
}

function renderDepBtns() {
    const wrap = document.getElementById('depBrandBtns');
    wrap.innerHTML = '';
    DEP_BRANDS.forEach((b, i) => {
        const btn = document.createElement('button');
        btn.textContent = b;
        const color = COLORS_DEP[i % COLORS_DEP.length];
        btn.style.cssText = `padding:4px 12px; border-radius:999px; border:2px solid ${color}; font-size:0.8rem; font-weight:700; cursor:pointer; transition:all .15s;`;
        btn.style.background = depActiveBrands.has(b) ? color : '#fff';
        btn.style.color      = depActiveBrands.has(b) ? '#fff' : color;
        btn.addEventListener('click', () => {
            if (depActiveBrands.has(b)) { if (depActiveBrands.size <= 1) return; depActiveBrands.delete(b); }
            else { depActiveBrands.add(b); }
            renderDepBtns(); buildDepChart();
        });
        btn.addEventListener('mouseenter', () => highlightDepBrand(b));
        btn.addEventListener('mouseleave', () => highlightDepBrand(null));
        wrap.appendChild(btn);
    });
}

/* ── 캐러셀 ── */
const SLIDE_TITLES = [
    '🏆 브랜드별 평균 시세',
    '⛽ 연료 타입 분포',
    '📉 연식별 평균 시세',
    '💰 가격대별 매물 분포',
    '📉 브랜드별 연식 감가율',
];

const chartInitFns = [
    buildBrandChart,
    buildFuelChart,
    buildYearChart,
    buildPriceDistChart,
    () => { renderDepBtns(); buildDepChart(); },
];
const chartInited = [false, false, false, false, false];

let currentSlide = 0;
const totalSlides = 5;
let animating = false;

function initDots() {
    const dots = document.getElementById('carouselDots');
    dots.innerHTML = '';
    for (let i = 0; i < totalSlides; i++) {
        const d = document.createElement('button');
        d.className = 'carousel-dot' + (i === 0 ? ' active' : '');
        d.onclick = () => goToSlide(i);
        dots.appendChild(d);
    }
}

function getDir(from, to) {
    if (from === to) return 0;
    if (to === (from + 1) % totalSlides) return 1;
    if (from === (to + 1) % totalSlides) return -1;
    return to > from ? 1 : -1;
}

function goToSlide(idx) {
    const target = (idx + totalSlides) % totalSlides;
    if (target === currentSlide || animating) return;
    animating = true;

    const dir = getDir(currentSlide, target);
    const oldSlide = document.getElementById('slide-' + currentSlide);
    const newSlide = document.getElementById('slide-' + target);

    oldSlide.style.transform = `translateX(${dir * -60}px)`;
    oldSlide.style.opacity = '0';
    oldSlide.style.pointerEvents = 'none';

    newSlide.style.transition = 'none';
    newSlide.style.transform = `translateX(${dir * 60}px)`;
    newSlide.style.opacity = '0';
    newSlide.offsetHeight;

    if (!chartInited[target]) {
        chartInitFns[target]();
        chartInited[target] = true;
    }

    newSlide.style.transition = '';
    newSlide.style.transform = 'translateX(0)';
    newSlide.style.opacity = '1';
    newSlide.style.pointerEvents = 'auto';

    document.querySelectorAll('.carousel-dot')[currentSlide].classList.remove('active');
    document.querySelectorAll('.carousel-dot')[target].classList.add('active');
    document.getElementById('carouselTitle').textContent = SLIDE_TITLES[target];

    currentSlide = target;

    setTimeout(() => {
        oldSlide.classList.remove('active');
        oldSlide.style.transform = '';
        oldSlide.style.opacity = '';
        oldSlide.style.pointerEvents = '';
        newSlide.classList.add('active');
        Chart.instances && Object.values(Chart.instances).forEach(c => {
            if (newSlide.contains(c.canvas)) c.resize();
        });
        animating = false;
    }, 380);
}

function slideMove(dir) { goToSlide(currentSlide + dir); }

initDots();
buildBrandChart();
chartInited[0] = true;

/* ── Gemini Q&A ── */
function setQuestion(q) {
    document.getElementById('qaInput').value = q;
    askGemini();
}
async function askGemini() {
    const input = document.getElementById('qaInput');
    const box   = document.getElementById('qaAnswer');
    const q = input.value.trim();
    if (!q) return;
    box.style.display = 'block';
    box.innerHTML = '<div style="color:var(--gray-400); font-size:.88rem; display:flex; align-items:center; gap:8px;"><span style="animation:spin 1s linear infinite; display:inline-block;">⏳</span> Gemini가 분석 중...</div>';
    try {
        const res  = await fetch('/api/ai-insight?q=' + encodeURIComponent(q));
        if (!res.ok) {
            box.innerHTML = `<div style="color:#dc2626; font-size:.85rem;">⚠️ 서버 오류 (${res.status})</div>`;
            return;
        }
        const data = await res.json();
        if (data.error) {
            box.innerHTML = `<div style="color:#dc2626; font-size:.85rem;">⚠️ ${data.error}</div>`;
        } else {
            const qLabel = `<div style="font-size:.78rem; font-weight:700; color:var(--blue-500); margin-bottom:.6rem;">Q. ${q}</div>`;
            const answer = `<div style="font-size:.9rem; color:var(--gray-700); line-height:1.8;">${data.insight.replace(/\n/g,'<br>')}</div>`;
            box.innerHTML = qLabel + answer;
        }
    } catch(e) {
        box.innerHTML = '<div style="color:#dc2626; font-size:.85rem;">⚠️ 요청 실패</div>';
    }
}
