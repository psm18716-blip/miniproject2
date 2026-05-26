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
