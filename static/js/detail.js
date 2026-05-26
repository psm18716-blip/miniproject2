/* detail.js
 * 데이터 변수는 detail.html의 <script> 블록에서 주입됨:
 *   CHART_LABELS  (연식 배열)
 *   CHART_DATA    (평균 시세 배열)
 */

new Chart(document.getElementById('priceChart'), {
    type: 'line',
    data: {
        labels: CHART_LABELS,
        datasets: [{
            label: '평균 시세 (만원)',
            data: CHART_DATA,
            borderColor: '#2563eb',
            backgroundColor: 'rgba(37,99,235,0.08)',
            fill: true,
            tension: 0.4,
            pointBackgroundColor: '#2563eb',
            pointBorderColor: '#fff',
            pointBorderWidth: 2,
            pointRadius: 5,
            pointHoverRadius: 7
        }]
    },
    options: {
        responsive: true,
        maintainAspectRatio: true,
        plugins: {
            legend: { display: false },
            tooltip: {
                backgroundColor: '#111827',
                titleColor: '#9ca3af',
                bodyColor: '#fff',
                bodyFont: { weight: 'bold', size: 14 },
                padding: 12,
                cornerRadius: 8,
                callbacks: {
                    label: ctx => `  ${ctx.parsed.y.toLocaleString()}만원`
                }
            }
        },
        scales: {
            x: {
                grid: { display: false },
                ticks: { font: { size: 12 }, color: '#9ca3af' }
            },
            y: {
                beginAtZero: false,
                grid: { color: '#f3f4f6' },
                ticks: {
                    font: { size: 12 },
                    color: '#9ca3af',
                    callback: v => v.toLocaleString() + '만'
                }
            }
        }
    }
});
