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
    const grid = document.getElementById('carGrid');
    if (!grid) return;
    grid.className = 'car-grid';
    if (mode === 3) grid.classList.add('g3');
    if (mode === 'l') grid.classList.add('list-view');
    ['v2', 'v3', 'vl'].forEach(id => document.getElementById(id).classList.remove('on'));
    const map = { 2: 'v2', 3: 'v3', l: 'vl' };
    document.getElementById(map[mode]).classList.add('on');
    sessionStorage.setItem('listView', mode);
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
        favs.delete(sid); btn.textContent = '♡'; btn.classList.remove('liked'); btn.style.color = '';
    } else {
        favs.add(sid); btn.textContent = '♥'; btn.classList.add('liked'); btn.style.color = '#ef4444';
        btn.style.transform = 'scale(1.4)'; setTimeout(() => btn.style.transform = '', 200);
    }
    saveFavs(favs); updateFavUI();
    if (favFilter) applyFavFilter();
}
function updateFavUI() {
    const favs = getFavs();
    document.getElementById('favCount').textContent = favs.size;
    document.querySelectorAll('.hd-card').forEach(card => {
        const btn = card.querySelector('.like-btn');
        if (favs.has(String(card.dataset.id))) {
            btn.textContent = '♥'; btn.classList.add('liked'); btn.style.color = '#ef4444';
        } else {
            btn.textContent = '♡'; btn.classList.remove('liked'); btn.style.color = '';
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

/* ── 페이지 로드 ── */
document.addEventListener('DOMContentLoaded', () => {
    updateFavUI();
    const saved = sessionStorage.getItem('listView');
    if (saved) setView(isNaN(saved) ? saved : Number(saved));
    const active = document.querySelector('.sb-brand.active');
    if (active) active.scrollIntoView({ block: 'center', behavior: 'instant' });
});
