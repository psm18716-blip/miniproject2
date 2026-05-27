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
