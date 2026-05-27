/* ── 정렬 ── */
function applySort(val) {
    const params = new URLSearchParams(location.search);
    params.set('sort', val);
    params.set('page', '1');
    location.href = '/list?' + params.toString();
}

/* ── 드롭다운 (fixed 위치 계산) ── */
let openDrop = null;

function toggleDrop(id, triggerEl) {
    const panel = document.getElementById(id);
    const isOpen = panel.classList.contains('open');
    closeAllDrops();
    if (!isOpen) {
        const rect = triggerEl.getBoundingClientRect();
        panel.style.top  = (rect.bottom + 6) + 'px';
        panel.style.left = rect.left + 'px';
        panel.classList.add('open');
        const pw = panel.offsetWidth;
        const vw = window.innerWidth;
        if (rect.left + pw > vw - 8) {
            panel.style.left = Math.max(8, vw - pw - 8) + 'px';
        }
        document.getElementById('dropDimmer').classList.add('on');
        openDrop = panel;
    }
}
function closeAllDrops() {
    document.querySelectorAll('.drop-panel').forEach(p => p.classList.remove('open'));
    document.getElementById('dropDimmer').classList.remove('on');
    openDrop = null;
}
function clearFields(...names) {
    const form = document.getElementById('filterForm');
    names.forEach(n => { const el = form.querySelector(`[name="${n}"]`); if (el) el.value = ''; });
}
function clearFilter(...names) {
    const params = new URLSearchParams(location.search);
    names.forEach(n => params.delete(n));
    params.set('page', '1');
    location.href = '/list?' + params.toString();
}

/* ── 뷰 전환 ── */
function setView(mode) {
    const m = (mode === '2' || mode === 2) ? 2
            : (mode === '3' || mode === 3) ? 3
            : 'l';
    const grid = document.getElementById('carGrid');
    if (!grid) return;
    grid.className = 'car-grid';
    if (m === 3) grid.classList.add('g3');
    if (m === 'l') grid.classList.add('list-view');
    ['v2', 'v3', 'vl'].forEach(id => {
        const el = document.getElementById(id);
        if (el) el.classList.remove('on');
    });
    const btnMap = { 2: 'v2', 3: 'v3', l: 'vl' };
    const btn = document.getElementById(btnMap[m]);
    if (btn) btn.classList.add('on');
    sessionStorage.setItem('listView', String(m));
}

/* ── 사이드바 브랜드 검색 ── */
function filterBrands(q) {
    const lq = q.toLowerCase();
    document.querySelectorAll('#brandList .sb-brand').forEach(el => {
        const name = el.dataset.name.toLowerCase();
        el.style.display = name.includes(lq) ? '' : 'none';
    });
}

/* ── 찜하기 ── */
const FAV_KEY = 'carmarket_favs';
let favFilter = false;

function getFavs() {
    try { return new Set(JSON.parse(localStorage.getItem(FAV_KEY) || '[]')); } catch { return new Set(); }
}
function saveFavs(s) { localStorage.setItem(FAV_KEY, JSON.stringify([...s])); }

function toggleLike(e, id) {
    e.preventDefault(); e.stopPropagation();
    const favs = getFavs();
    const btn = e.currentTarget;
    const sid = String(id);
    if (favs.has(sid)) {
        favs.delete(sid); btn.textContent = '♥'; btn.classList.remove('liked'); btn.style.color = '#fff';
    } else {
        favs.add(sid); btn.textContent = '♥'; btn.classList.add('liked'); btn.style.color = '#ef4444';
        btn.style.transform = 'scale(1.4)'; setTimeout(() => btn.style.transform = '', 200);
    }
    saveFavs(favs); updateFavUI();
    if (favFilter) applyFavFilter();
}
function updateFavUI() {
    const favs = getFavs();
    const favCnt = document.getElementById('favCount');
    if (favCnt) favCnt.textContent = favs.size;
    const floatCnt = document.getElementById('favCountFloat');
    if (floatCnt) floatCnt.textContent = favs.size;
    const floatBtn = document.getElementById('favFloat');
    if (floatBtn) floatBtn.classList.toggle('on', favs.size > 0);
    document.querySelectorAll('.hd-card').forEach(card => {
        const btn = card.querySelector('.like-btn');
        if (!btn) return;
        if (favs.has(String(card.dataset.id))) {
            btn.textContent = '♥'; btn.classList.add('liked'); btn.style.color = '#ef4444';
        } else {
            btn.textContent = '♥'; btn.classList.remove('liked'); btn.style.color = '#fff';
        }
    });
}
function applyFavFilter() {
    const favs = getFavs();
    document.querySelectorAll('.hd-card').forEach(card =>
        card.classList.toggle('fav-hidden', favFilter && !favs.has(String(card.dataset.id)))
    );
}
function toggleFavFilter() {
    const params = new URLSearchParams(location.search);
    if (params.get('favs')) {
        params.delete('favs');
        params.set('page', '1');
        location.href = '/list?' + params.toString();
    } else {
        const favs = getFavs();
        if (favs.size === 0) return;
        location.href = '/list?favs=' + encodeURIComponent([...favs].join(','));
    }
}

/* ── 차량 비교 ── */
const compareSet = new Set();
const compareNames = new Map();
const COMPARE_KEY = 'carmarket_compare';

function saveCompare() {
    localStorage.setItem(COMPARE_KEY, JSON.stringify({
        ids: [...compareSet],
        names: Object.fromEntries(compareNames)
    }));
}

function loadCompare() {
    try {
        const data = JSON.parse(localStorage.getItem(COMPARE_KEY) || 'null');
        if (!data) return;
        data.ids.forEach(id => compareSet.add(id));
        Object.entries(data.names).forEach(([id, name]) => compareNames.set(Number(id), name));
    } catch {}
}

function toggleCompare(e, carId, btn) {
    e.preventDefault();
    e.stopPropagation();
    const card = btn.closest('.hd-card');
    if (compareSet.has(carId)) {
        compareSet.delete(carId);
        compareNames.delete(carId);
        btn.classList.remove('checked');
        card.classList.remove('selected');
    } else {
        if (compareSet.size >= 2) return;
        compareSet.add(carId);
        const detail = [card.dataset.badge, card.dataset.fuel, card.dataset.year ? card.dataset.year + '년' : '']
            .filter(v => v && v !== 'None').join(' · ');
        compareNames.set(carId, { model: card.dataset.model || '차량', detail });
        btn.classList.add('checked');
        card.classList.add('selected');
    }
    saveCompare();
    updateCompareBar();
}

function updateCompareBar() {
    const bar = document.getElementById('compareBar');
    document.getElementById('compareCnt').textContent = compareSet.size;
    bar.classList.toggle('show', compareSet.size >= 1);
    const center = document.getElementById('compareBarCenter');
    const entries = [...compareNames.entries()];
    const item = (id, info) => {
        const model  = (typeof info === 'object') ? info.model  : info;
        const detail = (typeof info === 'object') ? info.detail : '';
        return '<span class="cmp-item">'
            + '<span class="cmp-chk" onclick="removeCompare(' + id + ')" title="선택 해제">✕</span>'
            + '<span class="cmp-info">'
            +   '<span class="cmp-name">' + model + '</span>'
            +   (detail ? '<span class="cmp-detail">' + detail + '</span>' : '')
            + '</span>'
            + '</span>';
    };
    if (entries.length === 2) {
        center.innerHTML = item(entries[0][0], entries[0][1])
            + '<span class="cmp-vs">vs</span>'
            + item(entries[1][0], entries[1][1]);
    } else if (entries.length === 1) {
        center.innerHTML = item(entries[0][0], entries[0][1])
            + '<span class="cmp-vs cmp-placeholder">+ 1대 더 선택</span>';
    } else {
        center.innerHTML = '';
    }
}

function removeCompare(carId) {
    compareSet.delete(carId);
    compareNames.delete(carId);
    const card = document.querySelector('.hd-card[data-id="' + carId + '"]');
    if (card) {
        card.classList.remove('selected');
        const btn = card.querySelector('.compare-chk');
        if (btn) btn.classList.remove('checked');
    }
    saveCompare();
    updateCompareBar();
}

function clearCompare() {
    compareSet.clear();
    compareNames.clear();
    saveCompare();
    document.querySelectorAll('.compare-chk.checked').forEach(b => b.classList.remove('checked'));
    document.querySelectorAll('.hd-card.selected').forEach(c => c.classList.remove('selected'));
    updateCompareBar();
}

function goCompare() {
    if (compareSet.size < 2) return;
    location.href = '/compare?ids=' + Array.from(compareSet).join(',');
}

/* ── 페이지 로드 ── */
document.addEventListener('DOMContentLoaded', () => {
    const saved = sessionStorage.getItem('listView') || 'l';
    setView(saved);
    updateFavUI();
    const active = document.querySelector('.sb-brand.active');
    if (active) active.scrollIntoView({ block: 'center', behavior: 'instant' });

    loadCompare();
    document.querySelectorAll('.hd-card').forEach(card => {
        if (compareSet.has(Number(card.dataset.id))) {
            card.classList.add('selected');
            const btn = card.querySelector('.compare-chk');
            if (btn) btn.classList.add('checked');
        }
    });
    updateCompareBar();
});
