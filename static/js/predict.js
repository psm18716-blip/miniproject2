const selMfr   = document.getElementById('sel-manufacturer');
const selModel = document.getElementById('sel-model');
const selBadge = document.getElementById('sel-badge');

function loadModels(manufacturer, selectValue) {
    if (!manufacturer) {
        selModel.innerHTML = '<option value="">브랜드를 먼저 선택하세요</option>';
        selBadge.innerHTML = '<option value="">모델을 먼저 선택하세요</option>';
        return;
    }
    selModel.innerHTML = '<option value="">불러오는 중...</option>';
    fetch(`/api/models?manufacturer=${encodeURIComponent(manufacturer)}`)
        .then(r => r.json())
        .then(models => {
            selModel.innerHTML = '<option value="">모델 선택</option>';
            models.forEach(m => {
                const opt = document.createElement('option');
                opt.value = m;
                opt.textContent = m;
                if (m === selectValue) opt.selected = true;
                selModel.appendChild(opt);
            });
            if (selectValue) loadBadges(manufacturer, selectValue, _savedBadge);
        });
}

function loadBadges(manufacturer, model, selectValue) {
    if (!model) {
        selBadge.innerHTML = '<option value="">모델을 먼저 선택하세요</option>';
        return;
    }
    selBadge.innerHTML = '<option value="">불러오는 중...</option>';
    fetch(`/api/badges?manufacturer=${encodeURIComponent(manufacturer)}&model=${encodeURIComponent(model)}`)
        .then(r => r.json())
        .then(badges => {
            selBadge.innerHTML = '<option value="">트림 선택</option>';
            badges.forEach(b => {
                const opt = document.createElement('option');
                opt.value = b;
                opt.textContent = b;
                if (b === selectValue) opt.selected = true;
                selBadge.appendChild(opt);
            });
        });
}

selMfr.addEventListener('change', () => loadModels(selMfr.value, ''));
selModel.addEventListener('change', () => loadBadges(selMfr.value, selModel.value, ''));

// 폼 제출 후 복원 (savedModel/savedBadge는 HTML 인라인 스크립트에서 주입)
function initPredict(savedModel, savedBadge) {
    window._savedBadge = savedBadge;
    if (selMfr.value) loadModels(selMfr.value, savedModel);
}
