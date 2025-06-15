// ========================================
// static/js/main.js - 簡素化版（common.js使用）
// ========================================

// グローバル検索機能（ページ固有の機能のみ）
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
                    performGlobalSearch(query);
                }, 300);
            }
        });
        
        // Enterキーでの検索
        globalSearch.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                e.preventDefault();
                const query = this.value.trim();
                if (query) {
                    CommonUtils.performSearch(query, '/notes/');
                }
            }
        });
    }
});

// グローバル検索実行（Ajax検索用）
function performGlobalSearch(query) {
    CommonUtils.debug('グローバル検索実行:', query);
    // 将来的にAjax検索を実装する場合はここに追加
}

// タグ選択機能（ページ固有）
function toggleTag(tagElement) {
    tagElement.classList.toggle('selected');
    tagElement.classList.toggle('bg-blue-600');
}