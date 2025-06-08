// グローバル検索機能
document.addEventListener('DOMContentLoaded', function() {
    const globalSearch = document.getElementById('global-search');
    
    if (globalSearch) {
        // リアルタイム検索の実装
        let searchTimeout;
        
        globalSearch.addEventListener('input', function() {
            clearTimeout(searchTimeout);
            const query = this.value.trim();
            
            if (query.length >= 2) {
                searchTimeout = setTimeout(() => {
                    performSearch(query);
                }, 300);
            }
        });
        
        // Enterキーでの検索
        globalSearch.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                e.preventDefault();
                const query = this.value.trim();
                if (query) {
                    window.location.href = `/notes/?q=${encodeURIComponent(query)}`;
                }
            }
        });
    }
});

// 検索実行関数
function performSearch(query) {
    // ここでAjax検索を実装（将来の拡張用）
    console.log('Searching for:', query);
}

// タグ選択機能
function toggleTag(tagElement) {
    tagElement.classList.toggle('selected');
    tagElement.classList.toggle('bg-blue-600');
}

// フォームバリデーション
function validateForm(formElement) {
    const requiredFields = formElement.querySelectorAll('[required]');
    let isValid = true;
    
    requiredFields.forEach(field => {
        if (!field.value.trim()) {
            field.classList.add('border-red-500');
            isValid = false;
        } else {
            field.classList.remove('border-red-500');
        }
    });
    
    return isValid;
}

// 成功メッセージの自動非表示
setTimeout(() => {
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        alert.style.opacity = '0';
        setTimeout(() => {
            alert.remove();
        }, 300);
    });
}, 5000);