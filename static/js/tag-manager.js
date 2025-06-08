// ========================================
// static/js/tag-manager.js - 統一タグ管理システム
// ========================================

class TagManager {
    constructor(options = {}) {
        this.selectedTags = options.selectedTags || [];
        this.tagChanges = { added: [], removed: [] };
        this.containers = {
            selectedTags: options.selectedTagsContainer || 'selected-tags-container',
            suggestedTags: options.suggestedTagsContainer || 'suggested-tags',
            tagInput: options.tagInput || 'custom-tag-input',
            tagChangesInput: options.tagChangesInput || 'selected-tags-json'
        };
        
        this.init();
    }
    
    init() {
        this.setupEventListeners();
        this.updateSelectedTagsDisplay();
        this.updateSuggestedTags();
    }
    
    setupEventListeners() {
        // エンターキーでタグ追加
        const tagInput = document.getElementById(this.containers.tagInput);
        if (tagInput) {
            tagInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    e.preventDefault();
                    this.addCustomTag();
                }
            });
        }
    }
    
    // カスタムタグ追加
    addCustomTag() {
        const input = document.getElementById(this.containers.tagInput);
        if (!input) {
            console.error('タグ入力フィールドが見つかりません');
            return;
        }
        
        let tagName = input.value.trim();
        if (!tagName) {
            this.showNotification('タグ名を入力してください', 'warning');
            return;
        }
        
        // #がない場合は自動で追加
        if (!tagName.startsWith('#')) {
            tagName = '#' + tagName;
        }
        
        // 重複チェック
        if (this.selectedTags.includes(tagName)) {
            this.showNotification('このタグは既に選択されています', 'warning');
            return;
        }
        
        // タグを追加
        this.addTag(tagName);
        input.value = '';
        
        this.showNotification(`タグ「${tagName}」を追加しました`, 'success');
    }
    
    // タグ追加（内部処理）
    addTag(tagName) {
        this.selectedTags.push(tagName);
        this.tagChanges.added.push(tagName);
        this.updateSelectedTagsDisplay();
        this.updateSuggestedTags();
        this.updateHiddenInput();
    }
    
    // 推奨タグをクリック
    selectSuggestedTag(tagName) {
        if (this.selectedTags.includes(tagName)) {
            this.showNotification('このタグは既に選択されています', 'warning');
            return;
        }
        
        this.addTag(tagName);
        this.showNotification(`タグ「${tagName}」を追加しました`, 'success');
    }
    
    // 選択済みタグを削除
    removeSelectedTag(tagName) {
        this.selectedTags = this.selectedTags.filter(tag => tag !== tagName);
        
        // 追加リストから削除（新しく追加したタグの場合）
        this.tagChanges.added = this.tagChanges.added.filter(tag => tag !== tagName);
        
        // 削除リストに追加（既存タグの場合）
        if (!this.tagChanges.added.includes(tagName)) {
            this.tagChanges.removed.push(tagName);
        }
        
        this.updateSelectedTagsDisplay();
        this.updateSuggestedTags();
        this.updateHiddenInput();
        
        this.showNotification(`タグ「${tagName}」を削除しました`, 'info');
    }
    
    // 既存タグを削除（編集時）
    removeExistingTag(tagId, tagName) {
        this.tagChanges.removed.push(tagId);
        this.selectedTags = this.selectedTags.filter(tag => tag !== tagName);
        this.updateSelectedTagsDisplay();
        this.updateHiddenInput();
        
        this.showNotification(`タグ「${tagName}」を削除しました`, 'info');
    }
    
    // 選択済みタグの表示を更新
    updateSelectedTagsDisplay() {
        const container = document.getElementById(this.containers.selectedTags);
        if (!container) {
            console.error('選択済みタグコンテナが見つかりません');
            return;
        }
        
        if (this.selectedTags.length === 0) {
            container.innerHTML = '<span class="text-gray-400 text-sm">タグが選択されていません</span>';
            return;
        }
        
        container.innerHTML = '';
        this.selectedTags.forEach(tag => {
            const tagElement = this.createTagElement(tag, () => this.removeSelectedTag(tag));
            container.appendChild(tagElement);
        });
    }
    
    // タグ要素を作成
    createTagElement(tagName, onRemove) {
        const tagElement = document.createElement('span');
        tagElement.className = 'inline-flex items-center px-3 py-1 rounded-full text-sm bg-blue-600 text-white animate-in slide-in-from-left duration-200';
        
        tagElement.innerHTML = `
            ${this.escapeHtml(tagName)}
            <button type="button" class="ml-2 text-blue-200 hover:text-white transition-colors" 
                    title="タグを削除">
                <svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
                </svg>
            </button>
        `;
        
        // 削除ボタンのイベント
        const removeButton = tagElement.querySelector('button');
        removeButton.addEventListener('click', (e) => {
            e.preventDefault();
            onRemove();
        });
        
        return tagElement;
    }
    
    // AI推奨タグを更新
    updateSuggestedTags() {
        const container = document.getElementById(this.containers.suggestedTags);
        if (!container) return;
        
        // フォーム内容を取得
        const content = this.getFormContent();
        const suggestions = this.generateTagSuggestions(content);
        
        container.innerHTML = '';
        const availableSuggestions = suggestions.filter(tag => !this.selectedTags.includes(tag));
        
        if (availableSuggestions.length === 0) {
            container.innerHTML = '<span class="text-gray-400 text-sm">推奨タグはありません</span>';
            return;
        }
        
        availableSuggestions.forEach(tag => {
            const tagElement = document.createElement('button');
            tagElement.type = 'button';
            tagElement.className = 'tag-suggestion px-3 py-1 rounded-full text-sm border border-gray-600 text-gray-300 hover:bg-gray-700 hover:border-blue-500 transition-all duration-200 transform hover:scale-105';
            tagElement.textContent = tag;
            tagElement.title = `「${tag}」を追加`;
            
            tagElement.addEventListener('click', (e) => {
                e.preventDefault();
                this.selectSuggestedTag(tag);
            });
            
            container.appendChild(tagElement);
        });
    }
    
    // フォーム内容を取得
    getFormContent() {
        return {
            stockCode: this.getFieldValue('id_stock_code') || this.getFieldValue('stock_code'),
            companyName: this.getFieldValue('id_company_name') || this.getFieldValue('company_name'),
            title: this.getFieldValue('id_title') || this.getFieldValue('title'),
            investmentReason: this.getFieldValue('id_investment_reason') || this.getFieldValue('investment_reason'),
            targetPrice: this.getFieldValue('id_target_price') || this.getFieldValue('target_price'),
            status: this.getFieldValue('id_status') || this.getFieldValue('status')
        };
    }
    
    // フィールド値を取得
    getFieldValue(fieldId) {
        const field = document.getElementById(fieldId);
        return field ? field.value : '';
    }
    
    // タグ推奨ロジック（模擬AI）
    generateTagSuggestions(content) {
        const suggestions = [];
        const text = Object.values(content).join(' ').toLowerCase();
        
        // キーワードベースの推奨
        const keywordMap = {
            '配当': ['#高配当', '#配当株', '#株主還元'],
            '成長': ['#成長株', '#長期投資'],
            '割安': ['#割安株', '#バリュー投資'],
            'テクノロジー': ['#テクノロジー', '#IT'],
            '自動車': ['#自動車', '#製造業'],
            'トヨタ': ['#7203トヨタ', '#自動車', '#高配当'],
            'ソニー': ['#6758ソニー', '#エンタメ', '#半導体'],
            'ソフトバンク': ['#9984ソフトバンク', '#通信', '#投資事業'],
            '決算': ['#決算分析', '#業績好調'],
            'リスク': ['#要注意', '#リスク要因'],
            '目標': ['#投資目標', '#戦略'],
            '長期': ['#長期投資', '#長期保有'],
            '短期': ['#短期取引', '#スイング'],
            '優待': ['#株主優待', '#優待株']
        };
        
        for (const [keyword, tags] of Object.entries(keywordMap)) {
            if (text.includes(keyword)) {
                suggestions.push(...tags);
            }
        }
        
        // ステータスベースの推奨
        const status = content.status;
        if (status === 'ACTIVE') {
            suggestions.push('#アクティブ投資');
        } else if (status === 'MONITORING') {
            suggestions.push('#要監視');
        } else if (status === 'ATTENTION') {
            suggestions.push('#要注意');
        }
        
        // 銘柄コードベースの推奨
        const stockCode = content.stockCode;
        if (stockCode && stockCode.length === 4) {
            suggestions.push(`#${stockCode}${content.companyName || ''}`);
        }
        
        // 重複除去して最大5個まで
        return [...new Set(suggestions)].slice(0, 6);
    }
    
    // 隠しフィールドを更新
    updateHiddenInput() {
        const input = document.getElementById(this.containers.tagChangesInput);
        if (input) {
            input.value = JSON.stringify({
                selected: this.selectedTags,
                changes: this.tagChanges
            });
        }
    }
    
    // 通知表示
    showNotification(message, type = 'info') {
        // 既存の通知を削除
        const existingNotifications = document.querySelectorAll('.tag-notification');
        existingNotifications.forEach(notification => notification.remove());
        
        const notification = document.createElement('div');
        notification.className = `tag-notification fixed top-4 right-4 z-50 p-3 rounded-lg text-white max-w-sm transform transition-all duration-300 translate-x-full opacity-0`;
        
        const typeClasses = {
            'error': 'bg-red-600',
            'warning': 'bg-yellow-600',
            'success': 'bg-green-600',
            'info': 'bg-blue-600'
        };
        
        notification.classList.add(typeClasses[type] || typeClasses.info);
        
        notification.innerHTML = `
            <div class="flex items-center justify-between">
                <span class="text-sm">${this.escapeHtml(message)}</span>
                <button onclick="this.parentElement.parentElement.remove()" 
                        class="ml-3 text-white/80 hover:text-white">
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
    
    // HTMLエスケープ
    escapeHtml(text) {
        const map = {
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#039;'
        };
        return text.replace(/[&<>"']/g, m => map[m]);
    }
    
    // 既存タグを設定（編集時用）
    setExistingTags(tags) {
        this.selectedTags = tags.map(tag => tag.name || tag);
        this.updateSelectedTagsDisplay();
        this.updateSuggestedTags();
    }
    
    // バリデーション
    validate() {
        if (this.selectedTags.length === 0) {
            this.showNotification('少なくとも1つのタグを選択してください', 'warning');
            return false;
        }
        return true;
    }
    
    // データを取得
    getData() {
        return {
            selectedTags: this.selectedTags,
            tagChanges: this.tagChanges
        };
    }
}

// グローバル関数（下位互換性のため）
let globalTagManager = null;

function initTagManager(options = {}) {
    globalTagManager = new TagManager(options);
    return globalTagManager;
}

function addCustomTag() {
    if (globalTagManager) {
        globalTagManager.addCustomTag();
    }
}

function selectSuggestedTag(tagName) {
    if (globalTagManager) {
        globalTagManager.selectSuggestedTag(tagName);
    }
}

function removeSelectedTag(tagName) {
    if (globalTagManager) {
        globalTagManager.removeSelectedTag(tagName);
    }
}