// 시도별 좌표
const COORDS = {
    '서울': [37.5665, 126.9780],
    '경기': [37.4138, 127.5183],
    '인천': [37.4563, 126.7052],
    '부산': [35.1796, 129.0756],
    '대구': [35.8714, 128.6014],
    '광주': [35.1595, 126.8526],
    '대전': [36.3504, 127.3845],
    '울산': [35.5384, 129.3114],
    '경남': [35.4606, 128.2132],
    '경북': [36.4919, 128.8889],
    '전북': [35.7175, 127.1530],
    '전남': [34.8679, 126.9910],
    '충남': [36.5184, 126.8000],
    '충북': [36.6357, 127.4914],
    '강원': [37.8228, 128.1555],
    '세종': [36.4801, 127.2890],
    '제주': [33.4996, 126.5312],
};

// 지도 초기화 — 제주도 포함 전국 범위로 자동 맞춤
const map = L.map('map', { zoomControl: true });
map.fitBounds([[33.0, 124.5], [38.7, 131.0]]);
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '© OpenStreetMap',
    maxZoom: 13,
}).addTo(map);

// 최대 매물 수 (마커 크기 비례용)
const maxCnt = Math.max(...REGION_DATA.map(d => d.cnt));
const maxPrice = Math.max(...REGION_DATA.map(d => d.avg_price));

function priceColor(avg_price) {
    const ratio = avg_price / maxPrice;
    const hue = Math.round(120 - ratio * 120);
    return `hsl(${hue}, 70%, 45%)`;
}

const markers = {};

REGION_DATA.forEach(d => {
    const coord = COORDS[d.region];
    if (!coord) return;

    const r = 18 + Math.round((d.cnt / maxCnt) * 30);

    const circle = L.circleMarker(coord, {
        radius: r,
        fillColor: priceColor(d.avg_price),
        color: '#fff',
        weight: 2.5,
        opacity: 1,
        fillOpacity: 0.82,
    }).addTo(map);

    circle.bindTooltip(
        `<b>${d.region}</b><br>${d.avg_price.toLocaleString()}만원<br>매물 ${d.cnt.toLocaleString()}건`,
        { direction: 'top', offset: [0, -r] }
    );

    circle.on('click', () => goRegion(d.region, null));
    markers[d.region] = circle;
});

// 정렬 상태
let currentSort = 'cnt';
let lastData = REGION_DATA;

function setSort(sort) {
    currentSort = sort;
    document.getElementById('sort-cnt').classList.toggle('active', sort === 'cnt');
    document.getElementById('sort-price').classList.toggle('active', sort === 'price');
    renderList(lastData);
}

function renderList(data) {
    if (!data.length) return;
    const maxP = Math.max(...data.map(d => d.avg_price));
    const sorted = currentSort === 'cnt'
        ? [...data].sort((a, b) => b.cnt - a.cnt)
        : [...data].sort((a, b) => a.avg_price - b.avg_price);
    const list = document.querySelector('.region-list');
    list.innerHTML = sorted.map((d, i) => {
        const ratio = d.avg_price / maxP;
        const hue = Math.round(120 - ratio * 120);
        return `<a class="region-item" href="#" onclick="goRegion('${d.region}', this); return false;">
            <span class="region-rank">${i + 1}</span>
            <span class="region-dot" style="background:hsl(${hue},70%,45%)"></span>
            <div class="region-info">
                <div class="region-name">${d.region}</div>
                <div class="region-cnt">매물 ${d.cnt.toLocaleString()}건</div>
            </div>
            <span class="region-price">${d.avg_price.toLocaleString()}만</span>
        </a>`;
    }).join('');
}

// 브랜드/모델 필터
const filterMfr   = document.getElementById('filter-mfr');
const filterModel = document.getElementById('filter-model');
const filterLabel = document.getElementById('filter-label');

filterMfr.addEventListener('change', () => {
    const mfr = filterMfr.value;
    filterModel.innerHTML = '<option value="">전체 모델</option>';
    if (mfr) {
        fetch(`/api/models?manufacturer=${encodeURIComponent(mfr)}`)
            .then(r => r.json())
            .then(models => {
                models.forEach(m => {
                    const opt = document.createElement('option');
                    opt.value = m; opt.textContent = m;
                    filterModel.appendChild(opt);
                });
            });
    }
    updateMap();
});

filterModel.addEventListener('change', updateMap);

function updateMap() {
    const mfr   = filterMfr.value;
    const model = filterModel.value;
    let url = '/api/region-stats';
    const params = [];
    if (mfr)   params.push(`manufacturer=${encodeURIComponent(mfr)}`);
    if (model) params.push(`model=${encodeURIComponent(model)}`);
    if (params.length) url += '?' + params.join('&');

    filterLabel.textContent = model ? `"${model}" 지역별 평균시세` : mfr ? `"${mfr}" 지역별 평균시세` : '';

    fetch(url)
        .then(r => r.json())
        .then(data => {
            if (!data.length) return;
            const maxP = Math.max(...data.map(d => d.avg_price));
            const maxC = Math.max(...data.map(d => d.cnt));
            const activeRegions = new Set(data.map(d => d.region));

            Object.entries(markers).forEach(([region, m]) => {
                if (!activeRegions.has(region)) {
                    m.setStyle({ fillOpacity: 0, opacity: 0 });
                    m.off('click');
                } else {
                    m.setStyle({ fillOpacity: 0.82, opacity: 1 });
                }
            });

            data.forEach(d => {
                const m = markers[d.region];
                if (!m) return;
                const r = 18 + Math.round((d.cnt / maxC) * 30);
                const ratio = d.avg_price / maxP;
                const hue = Math.round(120 - ratio * 120);
                m.setRadius(r);
                m.setStyle({ fillColor: `hsl(${hue},70%,45%)`, fillOpacity: 0.82, opacity: 1 });
                m.setTooltipContent(`<b>${d.region}</b><br>${d.avg_price.toLocaleString()}만원<br>매물 ${d.cnt.toLocaleString()}건`);
                m.off('click');
                m.on('click', () => goRegion(d.region, null));
            });

            lastData = data;
            renderList(data);
        });
}

// 지역 이동 — 선택된 브랜드/모델도 함께 전달
function goRegion(region, listEl) {
    document.querySelectorAll('.region-item').forEach(el => el.classList.remove('active'));
    if (listEl) listEl.classList.add('active');

    Object.entries(markers).forEach(([r, m]) => {
        m.setStyle({ weight: r === region ? 4 : 2.5, color: r === region ? '#2563eb' : '#fff' });
    });

    const mfr   = filterMfr.value;
    const model = filterModel.value;
    const qsFinal = new URLSearchParams({ region });
    if (mfr)   qsFinal.set('manufacturer', mfr);
    if (model) qsFinal.set('q', model);

    document.querySelector('.region-wrap').classList.add('slide-out');
    setTimeout(() => {
        window.location.href = `/list?${qsFinal.toString()}`;
    }, 280);
}

// 초기 리스트
renderList(lastData);

// 뒤로가기로 돌아올 때 bfcache 새로고침
window.addEventListener('pageshow', e => {
    if (e.persisted) window.location.reload();
});
