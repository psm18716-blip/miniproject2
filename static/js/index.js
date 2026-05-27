/* ── 마키 배너 (끊김 없음 + sessionStorage 위치 유지) ── */
(function () {
    const items = [
        '<b>엔카 데이터 기반</b> 실시간 시세', '·',
        '연식별 <b>평균 시세 차트</b>', '·',
        '국산 · 수입 <b>전 차종 지원</b>', '·',
        '<b>무료</b> 이용', '·',
        '<b>18,000대+</b> 매물 분석', '·',
        '브랜드별 <b>시세 비교</b>', '·',
        '<b>KDT 14기</b> 화이팅', '·',
    ];

    const track = document.getElementById('marqueeTrack');
    const repeat = 4;
    for (let r = 0; r < repeat; r++) {
        items.forEach(text => {
            const span = document.createElement('span');
            span.innerHTML = text;
            track.appendChild(span);
        });
    }

    const speed = 0.5;
    let pos = parseFloat(sessionStorage.getItem('mqPos') || '0');
    let raf;
    let halfW = 0;

    function measure() { halfW = track.scrollWidth / 2; }

    function tick() {
        pos += speed;
        if (pos >= halfW) pos -= halfW;
        track.style.transform = `translateX(-${pos}px)`;
        sessionStorage.setItem('mqPos', pos);
        raf = requestAnimationFrame(tick);
    }

    requestAnimationFrame(() => { measure(); tick(); });

    document.addEventListener('visibilitychange', () => {
        if (document.hidden) cancelAnimationFrame(raf);
        else tick();
    });
})();

/* ── 검색 ── */
function doSearch() {
    const q = document.getElementById('heroSearch').value.trim();
    if (q) location.href = '/list?q=' + encodeURIComponent(q);
}
document.getElementById('heroSearch').addEventListener('keydown', e => {
    if (e.key === 'Enter') doSearch();
});

/* ── 캐러셀 ── */
function createCarousel(trackId, prevId, nextId, barId, textId) {
    const track = document.getElementById(trackId);
    if (!track) return () => {};
    const PER_PAGE = 3;
    const totalPages = Math.ceil(track.children.length / PER_PAGE);
    let current = 0;
    function goTo(page) {
        current = Math.max(0, Math.min(page, totalPages - 1));
        const cardW = (track.parentElement.offsetWidth - 28) / 3;
        track.style.transform = `translateX(-${(cardW + 14) * PER_PAGE * current}px)`;
        const bar = barId ? document.getElementById(barId) : null;
        if (bar) bar.style.width = ((current + 1) / totalPages) * 100 + '%';
        const txt = document.getElementById(textId);
        if (txt) txt.textContent = current + 1 + ' / ' + totalPages;
        const cp = document.getElementById(prevId);
        const cn = document.getElementById(nextId);
        if (cp) cp.disabled = current === 0;
        if (cn) cn.disabled = current === totalPages - 1;
    }
    function move(dir) { goTo(current + dir); }
    let startX = 0;
    track.addEventListener('touchstart', (e) => { startX = e.touches[0].clientX; });
    track.addEventListener('touchend', (e) => {
        const diff = startX - e.changedTouches[0].clientX;
        if (Math.abs(diff) > 40) move(diff > 0 ? 1 : -1);
    });
    goTo(0);
    return move;
}
const moveDomestic = createCarousel('carouselTrackDomestic', 'counterPrevDomestic', 'counterNextDomestic', 'progressBarDomestic', 'counterTextDomestic');
const moveImported  = createCarousel('carouselTrackImported', 'counterPrevImported', 'counterNextImported', 'progressBarImported', 'counterTextImported');
function moveCarousel(type, dir) {
    if (type === 'domestic') moveDomestic(dir);
    if (type === 'imported') moveImported(dir);
}
