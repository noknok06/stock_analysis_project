// ========================================
// static/js/tag-management.js - タグ管理専用JavaScript
// ========================================

class TagManager {
    constructor() {
        this.selectedTags = new Set();
        this.currentEditingTagId = null;
        this.searchTimeout = null;
        this.isLoading = false;
        
        this.init();
    }
    
    init() {
        this.setupEventListeners();
        this.setupKeyboardShortcuts();
        this.setupAutoSave();
        this.initializeComponents();
    }
    
    // =================================
    // イベントリスナーの設定
    // =================================
    
    setupEventListeners() {
        // バルクアクション関連
        document.addEventListener('change', (e) => {
            if (e.target.matches('.tag-checkbox')) {
                this.updateBulkActionsVisibility();
            }
            if (e.target.matches('#select-all-checkbox')) {
                this.toggleAllTags(e.target.checked);
            }
        });
        
        // 検索・フィルター関連
        const searchInput = document.querySelector('input[name="q"]');
        if (searchInput) {
            searchInput.addEventListener('input', (e) => {
                this.handleSearchInput(e.target.value);
            });
        }
        
        const filterSelects = document.querySelectorAll('select[name="category"], select[name="is_active"], select[name="usage"], select[name="sort"]');
        filterSelects.forEach(select => {
            select.addEventListener('change', () => {
                this.submitFilterForm();
            });
        });
        
        // モーダル関連
        document.addEventListener('click', (e) => {
            if (e.target.matches('[data-modal-close]') || e.target.closest('[data-modal-close]')) {
                this.closeAllModals();
            }
        });
        
        // クイック編集フォーム
        const quickEditForm = document.getElementById('quick-edit-form');
        if (quickEditForm) {
            quickEditForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.submitQuickEdit();
            });
        }
        
        // プレビュー更新
        const previewInputs = document.querySelectorAll('#edit-tag-name, #edit-tag-category');
        previewInputs.forEach(input => {
            input.addEventListener('input', () => this.updatePreview());
        });
    }
    
    setupKeyboardShortcuts() {
        document.addEventListener('keydown', (e) => {
            // Escape でモーダルを閉じる
            if (e.key === 'Escape') {
                this.closeAllModals();
            }
            
            // Ctrl+A で全選択
            if (e.ctrlKey && e.key === 'a' && !e.target.matches('input, textarea')) {
                e.preventDefault();
                this.selectAllTags();
            }
            
            // Ctrl+F で検索にフォーカス
            if (e.ctrlKey && e.key === 'f') {
                e.preventDefault();
                const searchInput = document.querySelector('input[name="q"]');
                if (searchInput) {
                    searchInput.focus();
                    searchInput.select();
                }
            }
            
            // Delete で選択したタグを削除
            if (e.key === 'Delete' && this.selectedTags.size > 0 && !e.target.matches('input, textarea')) {
                e.preventDefault();
                this.bulkDelete();
            }
        });
    }
    
    setupAutoSave() {
        // フォーム変更の自動保存（オプション）
        const formInputs = document.querySelectorAll('input, textarea, select');
        formInputs.forEach(input => {
            input.addEventListener('change', () => {
                this.scheduleAutoSave();
            });
        });
    }
    
    initializeComponents() {
        // 既存のタグ選択状態を復元
        this.restoreSelection();
        
        // ツールチップの初期化
        this.initializeTooltips();
        
        // 遅延読み込みの設定
        this.setupLazyLoading();
        
        // 無限スクロールの設定（必要に応じて）
        this.setupInfiniteScroll();
    }
    
    // =================================
    // バルクアクション
    // =================================
    
    updateBulkActionsVisibility() {
        const checkboxes = document.querySelectorAll('.tag-checkbox:checked');
        const bulkActionsBar = document.getElementById('bulk-actions-bar');
        const selectedCount = document.getElementById('selected-count');
        
        this.selectedTags.clear();
        checkboxes.forEach(cb => {
            this.selectedTags.add(cb.value);
            cb.closest('.tag-item').classList.add('selected');
        });
        
        // 選択されていないアイテムから selected クラスを削除
        document.querySelectorAll('.tag-checkbox:not(:checked)').forEach(cb => {
            cb.closest('.tag-item').classList.remove('selected');
        });
        
        if (this.selectedTags.size > 0) {
            selectedCount.textContent = `${this.selectedTags.size}個のタグを選択中`;
            bulkActionsBar.classList.add('show');
        } else {
            bulkActionsBar.classList.remove('show');
        }
        
        // 全選択チェックボックスの状態を更新
        const allCheckboxes = document.querySelectorAll('.tag-checkbox');
        const selectAllCheckbox = document.getElementById('select-all-checkbox');
        if (selectAllCheckbox) {
            selectAllCheckbox.checked = allCheckboxes.length > 0 && checkboxes.length === allCheckboxes.length;
            selectAllCheckbox.indeterminate = checkboxes.length > 0 && checkboxes.length < allCheckboxes.length;
        }
    }
    
    toggleAllTags(checked) {
        const checkboxes = document.querySelectorAll('.tag-checkbox');
        checkboxes.forEach(cb => {
            cb.checked = checked;
            if (checked) {
                cb.closest('.tag-item').classList.add('selected');
            } else {
                cb.closest('.tag-item').classList.remove('selected');
            }
        });
        this.updateBulkActionsVisibility();
    }
    
    selectAllTags() {
        const selectAllCheckbox = document.getElementById('select-all-checkbox');
        if (selectAllCheckbox) {
            selectAllCheckbox.checked = true;
            this.toggleAllTags(true);
        }
    }
    
    clearSelection() {
        const selectAllCheckbox = document.getElementById('select-all-checkbox');
        if (selectAllCheckbox) {
            selectAllCheckbox.checked = false;
            this.toggleAllTags(false);
        }
    }
    
    // 一括操作の実行
    async performBulkAction(action, additionalData = {}) {
        if (this.selectedTags.size === 0) {
            this.showNotification('タグが選択されていません', 'warning');
            return;
        }
        
        try {
            this.setLoading(true);
            
            const response = await fetch('/tags/bulk-action/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCsrfToken()
                },
                body: JSON.stringify({
                    action: action,
                    tag_ids: Array.from(this.selectedTags),
                    ...additionalData
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.showNotification(data.message, 'success');
                setTimeout(() => location.reload(), 1000);
            } else {
                this.showNotification(data.error, 'error');
            }
        } catch (error) {
            console.error('Bulk action error:', error);
            this.showNotification('操作に失敗しました', 'error');
        } finally {
            this.setLoading(false);
        }
    }
    
    bulkActivate() {
        if (this.selectedTags.size === 0) return;
        
        if (confirm(`選択された${this.selectedTags.size}個のタグをアクティブにしますか？`)) {
            this.performBulkAction('activate');
        }
    }
    
    bulkDeactivate() {
        if (this.selectedTags.size === 0) return;
        
        if (confirm(`選択された${this.selectedTags.size}個のタグを無効にしますか？`)) {
            this.performBulkAction('deactivate');
        }
    }
    
    bulkDelete() {
        if (this.selectedTags.size === 0) return;
        
        if (confirm(`選択された${this.selectedTags.size}個のタグを削除しますか？この操作は元に戻せません。`)) {
            this.performBulkAction('delete');
        }
    }
    
    bulkChangeCategory() {
        if (this.selectedTags.size === 0) return;
        
        const newCategory = prompt('新しいカテゴリを選択してください：\n\nSTOCK - 銘柄\nSTYLE - 投資スタイル\nSECTOR - セクター\nANALYSIS - 分析手法\nSTRATEGY - 投資戦略\nMARKET - 市場\nRISK - リスク\nEVENT - イベント\nOTHER - その他');
        
        if (newCategory && ['STOCK', 'STYLE', 'SECTOR', 'ANALYSIS', 'STRATEGY', 'MARKET', 'RISK', 'EVENT', 'OTHER'].includes(newCategory.toUpperCase())) {
            this.performBulkAction('change_category', { new_category: newCategory.toUpperCase() });
        }
    }
    
    // =================================
    // 個別タグ操作
    // =================================
    
    async toggleTagStatus(tagId) {
        try {
            this.setLoading(true);
            
            const response = await fetch(`/tags/${tagId}/toggle-status/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': this.getCsrfToken()
                }
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.showNotification(data.message, 'success');
                setTimeout(() => location.reload(), 1000);
            } else {
                this.showNotification(data.error, 'error');
            }
        } catch (error) {
            console.error('Toggle status error:', error);
            this.showNotification('ステータスの切り替えに失敗しました', 'error');
        } finally {
            this.setLoading(false);
        }
    }
    
    async viewTagUsage(tagId) {
        try {
            this.setLoading(true);
            
            const response = await fetch(`/tags/${tagId}/usage-stats/`);
            const data = await response.json();
            
            if (data.success) {
                this.displayUsageStats(data);
                this.showModal('usage-modal');
            } else {
                this.showNotification(data.error, 'error');
            }
        } catch (error) {
            console.error('Usage stats error:', error);
            this.showNotification('使用状況の取得に失敗しました', 'error');
        } finally {
            this.setLoading(false);
        }
    }
    
    // =================================
    // クイック編集
    // =================================
    
    quickEditTag(tagId) {
        this.currentEditingTagId = tagId;
        const tagItem = document.querySelector(`[data-tag-id="${tagId}"]`);
        const tagName = tagItem.dataset.tagName;
        
        // フォームに現在の値を設定
        document.getElementById('edit-tag-name').value = tagName;
        
        // モーダルを表示
        this.showModal('quick-edit-modal');
        
        // 名前フィールドにフォーカス
        setTimeout(() => {
            document.getElementById('edit-tag-name').focus();
            document.getElementById('edit-tag-name').select();
        }, 100);
    }
    
    async submitQuickEdit() {
        if (!this.currentEditingTagId) return;
        
        const formData = {
            name: document.getElementById('edit-tag-name').value,
            description: document.getElementById('edit-tag-description').value,
            category: document.getElementById('edit-tag-category').value,
            is_active: document.getElementById('edit-tag-active').checked
        };
        
        try {
            this.setLoading(true);
            this.showButtonLoading('save-button-text', 'save-button-loader');
            
            const response = await fetch(`/tags/${this.currentEditingTagId}/quick-edit/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCsrfToken()
                },
                body: JSON.stringify(formData)
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.showNotification(data.message, 'success');
                this.closeModal('quick-edit-modal');
                setTimeout(() => location.reload(), 1000);
            } else {
                this.showNotification(data.error, 'error');
            }
        } catch (error) {
            console.error('Quick edit error:', error);
            this.showNotification('更新に失敗しました', 'error');
        } finally {
            this.setLoading(false);
            this.hideButtonLoading('save-button-text', 'save-button-loader');
        }
    }
    
    // =================================
    // 検索・フィルター
    // =================================
    
    handleSearchInput(value) {
        clearTimeout(this.searchTimeout);
        this.searchTimeout = setTimeout(() => {
            if (value.length >= 2 || value.length === 0) {
                this.submitFilterForm();
            }
        }, 500);
    }
    
    submitFilterForm() {
        const form = document.getElementById('filter-form');
        if (form) {
            form.submit();
        }
    }
    
    async performRealtimeSearch(query) {
        try {
            const response = await fetch(`/tags/search/?q=${encodeURIComponent(query)}&limit=20`);
            const data = await response.json();
            
            if (data.success) {
                this.updateSearchResults(data.results);
            }
        } catch (error) {
            console.error('Realtime search error:', error);
        }
    }
    
    updateSearchResults(results) {
        // リアルタイム検索結果の表示（必要に応じて実装）
        console.log('Search results:', results);
    }
    
    // =================================
    // モーダル管理
    // =================================
    
    showModal(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.classList.remove('hidden');
            document.body.style.overflow = 'hidden';
            
            // フォーカストラップの設定
            this.setupFocusTrap(modal);
        }
    }
    
    closeModal(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.classList.add('hidden');
            document.body.style.overflow = '';
            this.currentEditingTagId = null;
        }
    }
    
    closeAllModals() {
        const modals = document.querySelectorAll('[id$="-modal"]');
        modals.forEach(modal => {
            modal.classList.add('hidden');
        });
        document.body.style.overflow = '';
        this.currentEditingTagId = null;
    }
    
    setupFocusTrap(modal) {
        const focusableElements = modal.querySelectorAll(
            'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
        );
        const firstElement = focusableElements[0];
        const lastElement = focusableElements[focusableElements.length - 1];
        
        modal.addEventListener('keydown', (e) => {
            if (e.key === 'Tab') {
                if (e.shiftKey) {
                    if (document.activeElement === firstElement) {
                        e.preventDefault();
                        lastElement.focus();
                    }
                } else {
                    if (document.activeElement === lastElement) {
                        e.preventDefault();
                        firstElement.focus();
                    }
                }
            }
        });
        
        if (firstElement) {
            firstElement.focus();
        }
    }
    
    // =================================
    // カラーピッカー
    // =================================
    
    selectColor(color) {
        // 隠しフィールドを更新
        const colorInput = document.getElementById('edit-tag-color') || document.querySelector('input[name="color"]');
        if (colorInput) {
            colorInput.value = color;
        }
        
        // 視覚的な選択状態を更新
        document.querySelectorAll('.color-option').forEach(option => {
            option.classList.remove('selected');
        });
        const selectedOption = document.querySelector(`[data-color="${color}"]`);
        if (selectedOption) {
            selectedOption.classList.add('selected');
        }
        
        // プレビューを更新
        this.updatePreview();
    }
    
    updatePreview() {
        const nameInput = document.getElementById('edit-tag-name') || document.querySelector('input[name="name"]');
        const categorySelect = document.getElementById('edit-tag-category') || document.querySelector('select[name="category"]');
        const colorInput = document.getElementById('edit-tag-color') || document.querySelector('input[name="color"]');
        
        const preview = document.getElementById('tag-preview');
        const categoryPreview = document.getElementById('category-preview');
        
        if (preview && nameInput) {
            preview.textContent = nameInput.value || 'プレビュー';
        }
        
        if (preview && colorInput) {
            const color = colorInput.value || '#6b7280';
            preview.style.backgroundColor = color;
        }
        
        if (categoryPreview && categorySelect) {
            const selectedOption = categorySelect.options[categorySelect.selectedIndex];
            categoryPreview.textContent = selectedOption.text;
        }
    }
    
    // =================================
    // エクスポート機能
    // =================================
    
    exportTags(format = 'csv') {
        const tags = Array.from(document.querySelectorAll('.tag-item'));
        let content = '';
        let filename = `tags_export_${new Date().toISOString().split('T')[0]}`;
        let mimeType = '';
        
        switch (format) {
            case 'csv':
                content = this.generateCSV(tags);
                filename += '.csv';
                mimeType = 'text/csv';
                break;
            case 'json':
                content = this.generateJSON(tags);
                filename += '.json';
                mimeType = 'application/json';
                break;
            case 'xml':
                content = this.generateXML(tags);
                filename += '.xml';
                mimeType = 'application/xml';
                break;
        }
        
        this.downloadFile(content, filename, mimeType);
        this.showNotification(`タグリストを${format.toUpperCase()}形式でエクスポートしました`, 'success');
    }
    
    generateCSV(tags) {
        const headers = ['タグ名', 'カテゴリ', '説明', '使用回数', 'ステータス', '作成日', '更新日'];
        const rows = [headers.join(',')];
        
        tags.forEach(tag => {
            const name = tag.dataset.tagName || '';
            const category = tag.querySelector('.rounded-full')?.textContent.trim() || '';
            const usageCount = tag.textContent.match(/(\d+)回使用/)?.[1] || '0';
            const isActive = tag.textContent.includes('アクティブ') ? 'アクティブ' : '無効';
            
            const row = [
                this.escapeCsv(name),
                this.escapeCsv(category),
                this.escapeCsv(''), // 説明
                usageCount,
                this.escapeCsv(isActive),
                this.escapeCsv(''), // 作成日
                this.escapeCsv('')  // 更新日
            ];
            rows.push(row.join(','));
        });
        
        return rows.join('\n');
    }
    
    generateJSON(tags) {
        const data = tags.map(tag => ({
            name: tag.dataset.tagName || '',
            category: tag.querySelector('.rounded-full')?.textContent.trim() || '',
            usageCount: parseInt(tag.textContent.match(/(\d+)回使用/)?.[1] || '0'),
            isActive: tag.textContent.includes('アクティブ'),
            exportedAt: new Date().toISOString()
        }));
        
        return JSON.stringify(data, null, 2);
    }
    
    generateXML(tags) {
        let xml = '<?xml version="1.0" encoding="UTF-8"?>\n<tags>\n';
        
        tags.forEach(tag => {
            const name = this.escapeXml(tag.dataset.tagName || '');
            const category = this.escapeXml(tag.querySelector('.rounded-full')?.textContent.trim() || '');
            const usageCount = tag.textContent.match(/(\d+)回使用/)?.[1] || '0';
            const isActive = tag.textContent.includes('アクティブ');
            
            xml += `  <tag>\n`;
            xml += `    <name>${name}</name>\n`;
            xml += `    <category>${category}</category>\n`;
            xml += `    <usageCount>${usageCount}</usageCount>\n`;
            xml += `    <isActive>${isActive}</isActive>\n`;
            xml += `  </tag>\n`;
        });
        
        xml += '</tags>';
        return xml;
    }
    
    // =================================
    // ユーティリティ関数
    // =================================
    
    displayUsageStats(data) {
        const content = document.getElementById('usage-content');
        if (!content) return;
        
        content.innerHTML = `
            <div class="space-y-6">
                <div class="text-center">
                    <h4 class="text-xl font-bold text-white">${this.escapeHtml(data.tag.name)}</h4>
                    <p class="text-gray-400">総使用回数: ${data.tag.usage_count}回</p>
                </div>
                
                <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div>
                        <h5 class="font-semibold text-white mb-3">関連ノートブック (${data.notebooks.count}件)</h5>
                        <div class="space-y-2 max-h-32 overflow-y-auto">
                            ${data.notebooks.data.map(nb => `
                                <div class="text-sm">
                                    <a href="${nb.url}" class="text-blue-400 hover:text-blue-300">${this.escapeHtml(nb.title)}</a>
                                    <div class="text-gray-500">${new Date(nb.updated_at).toLocaleDateString()}</div>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                    
                    <div>
                        <h5 class="font-semibold text-white mb-3">関連エントリー (${data.entries.count}件)</h5>
                        <div class="space-y-2 max-h-32 overflow-y-auto">
                            ${data.entries.data.map(entry => `
                                <div class="text-sm">
                                    <a href="${entry.url}" class="text-blue-400 hover:text-blue-300">${this.escapeHtml(entry.title)}</a>
                                    <div class="text-gray-500">${this.escapeHtml(entry.notebook_title)}</div>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                </div>
            </div>
        `;
    }
    
    showNotification(message, type = 'info') {
        // 既存の通知を削除
        const existingNotifications = document.querySelectorAll('.notification');
        existingNotifications.forEach(notification => notification.remove());
        
        const notification = document.createElement('div');
        notification.className = `notification fixed top-4 right-4 z-50 px-4 py-3 rounded-lg text-white max-w-sm transform transition-all duration-300 translate-x-full opacity-0`;
        
        const typeClasses = {
            'error': 'bg-red-600',
            'warning': 'bg-yellow-600',
            'success': 'bg-green-600',
            'info': 'bg-blue-600'
        };
        
        notification.classList.add(typeClasses[type] || typeClasses.info);
        
        notification.innerHTML = `
            <div class="flex items-center justify-between">
                <span class="text-sm font-medium">${this.escapeHtml(message)}</span>
                <button onclick="this.parentElement.parentElement.remove()" 
                        class="ml-3 text-white/80 hover:text-white transition-colors">
                    <svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
                    </svg>
                </button>
            </div>
        `;
        
        document.body.appendChild(notification);
        
        // アニメーション
        setTimeout(() => {
            notification.classList.remove('translate-x-full', 'opacity-0');
        }, 100);
        
        // 自動削除
        setTimeout(() => {
            if (notification.parentNode) {
                notification.classList.add('translate-x-full', 'opacity-0');
                setTimeout(() => {
                    if (notification.parentNode) {
                        notification.remove();
                    }
                }, 300);
            }
        }, 4000);
    }
    
    setLoading(isLoading) {
        this.isLoading = isLoading;
        const buttons = document.querySelectorAll('button');
        buttons.forEach(button => {
            if (isLoading) {
                button.disabled = true;
                button.classList.add('opacity-50', 'cursor-not-allowed');
            } else {
                button.disabled = false;
                button.classList.remove('opacity-50', 'cursor-not-allowed');
            }
        });
    }
    
    showButtonLoading(textElementId, loaderElementId) {
        const textElement = document.getElementById(textElementId);
        const loaderElement = document.getElementById(loaderElementId);
        
        if (textElement) textElement.classList.add('hidden');
        if (loaderElement) loaderElement.classList.remove('hidden');
    }
    
    hideButtonLoading(textElementId, loaderElementId) {
        const textElement = document.getElementById(textElementId);
        const loaderElement = document.getElementById(loaderElementId);
        
        if (textElement) textElement.classList.remove('hidden');
        if (loaderElement) loaderElement.classList.add('hidden');
    }
    
    getCsrfToken() {
        const token = document.querySelector('[name=csrfmiddlewaretoken]');
        return token ? token.value : '';
    }
    
    downloadFile(content, filename, mimeType) {
        const blob = new Blob([content], { type: mimeType });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
    }
    
    escapeHtml(text) {
        const map = {
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#039;'
        };
        return String(text).replace(/[&<>"']/g, m => map[m]);
    }
    
    escapeCsv(text) {
        if (typeof text !== 'string') text = String(text);
        if (text.includes(',') || text.includes('"') || text.includes('\n')) {
            return '"' + text.replace(/"/g, '""') + '"';
        }
        return text;
    }
    
    escapeXml(text) {
        const map = {
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&apos;'
        };
        return String(text).replace(/[&<>"']/g, m => map[m]);
    }
    
    restoreSelection() {
        // ページリロード後の選択状態復元（localStorage使用）
        try {
            const savedSelection = localStorage.getItem('tagSelection');
            if (savedSelection) {
                const tagIds = JSON.parse(savedSelection);
                tagIds.forEach(id => {
                    const checkbox = document.querySelector(`input[value="${id}"]`);
                    if (checkbox) {
                        checkbox.checked = true;
                        checkbox.closest('.tag-item').classList.add('selected');
                    }
                });
                this.updateBulkActionsVisibility();
                localStorage.removeItem('tagSelection');
            }
        } catch (e) {
            console.warn('Failed to restore selection:', e);
        }
    }
    
    saveSelection() {
        // 選択状態を保存
        try {
            localStorage.setItem('tagSelection', JSON.stringify(Array.from(this.selectedTags)));
        } catch (e) {
            console.warn('Failed to save selection:', e);
        }
    }
    
    scheduleAutoSave() {
        // 自動保存のスケジューリング（オプション）
        clearTimeout(this.autoSaveTimeout);
        this.autoSaveTimeout = setTimeout(() => {
            console.log('Auto-save scheduled');
        }, 5000);
    }
    
    initializeTooltips() {
        // ツールチップの初期化（必要に応じて）
        const tooltipElements = document.querySelectorAll('[data-tooltip]');
        tooltipElements.forEach(element => {
            // ツールチップの実装
        });
    }
    
    setupLazyLoading() {
        // 画像の遅延読み込み設定（必要に応じて）
        if ('IntersectionObserver' in window) {
            const imageObserver = new IntersectionObserver((entries) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        // 遅延読み込みの実装
                    }
                });
            });
        }
    }
    
    setupInfiniteScroll() {
        // 無限スクロールの設定（必要に応じて）
        if ('IntersectionObserver' in window) {
            const scrollObserver = new IntersectionObserver((entries) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        // 次のページの読み込み
                    }
                });
            });
            
            const sentinel = document.querySelector('.scroll-sentinel');
            if (sentinel) {
                scrollObserver.observe(sentinel);
            }
        }
    }
}

// =================================
// グローバル関数（後方互換性）
// =================================

let tagManager = null;

// DOMが読み込まれたら初期化
document.addEventListener('DOMContentLoaded', function() {
    tagManager = new TagManager();
    
    // グローバル関数をtagManagerのメソッドにバインド
    window.selectAllTags = () => tagManager.selectAllTags();
    window.clearSelection = () => tagManager.clearSelection();
    window.bulkActivate = () => tagManager.bulkActivate();
    window.bulkDeactivate = () => tagManager.bulkDeactivate();
    window.bulkDelete = () => tagManager.bulkDelete();
    window.toggleTagStatus = (id) => tagManager.toggleTagStatus(id);
    window.viewTagUsage = (id) => tagManager.viewTagUsage(id);
    window.quickEditTag = (id) => tagManager.quickEditTag(id);
    window.selectColor = (color) => tagManager.selectColor(color);
    window.exportTags = (format) => tagManager.exportTags(format);
    window.closeQuickEditModal = () => tagManager.closeModal('quick-edit-modal');
    window.closeUsageModal = () => tagManager.closeModal('usage-modal');
    
    console.log('Tag management system initialized');
});

// ページを離れる前に選択状態を保存
window.addEventListener('beforeunload', function() {
    if (tagManager) {
        tagManager.saveSelection();
    }
});