// ========================================
// static/js/common.js - 共通JavaScript（重複削除版）
// ========================================

/**
 * 共通ユーティリティクラス
 */
class CommonUtils {
    
    /**
     * CSRFトークンを取得
     */
    static getCsrfToken() {
        const cookies = document.cookie.split(';');
        for (let cookie of cookies) {
            const [name, value] = cookie.trim().split('=');
            if (name === 'csrftoken') {
                return value;
            }
        }
        
        const csrfInput = document.querySelector('[name=csrfmiddlewaretoken]');
        return csrfInput ? csrfInput.value : '';
    }
    
    /**
     * HTMLエスケープ
     */
    static escapeHtml(text) {
        if (!text) return '';
        const map = {
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#039;'
        };
        return text.toString().replace(/[&<>"']/g, m => map[m]);
    }
    
    /**
     * タッチデバイス判定
     */
    static isTouchDevice() {
        return 'ontouchstart' in window || navigator.maxTouchPoints > 0;
    }
    
    /**
     * URLパラメータ更新
     */
    static updateUrlParams(params) {
        const url = new URL(window.location);
        
        Object.entries(params).forEach(([key, value]) => {
            if (value) {
                url.searchParams.set(key, value);
            } else {
                url.searchParams.delete(key);
            }
        });
        
        window.history.replaceState({}, '', url.toString());
    }
    
    /**
     * 動的項目追加
     */
    static addDynamicItem(containerId, itemClass, namePrefix, count, placeholder, removeFunction, value = '') {
        const container = document.getElementById(containerId);
        if (!container) return;
        
        const newItem = document.createElement('div');
        newItem.className = `${itemClass} flex gap-2 mb-2 animate-in`;
        newItem.innerHTML = `
            <input type="text" 
                   name="${namePrefix}_${count}" 
                   value="${this.escapeHtml(value)}"
                   placeholder="${placeholder} ${count + 1}"
                   class="flex-1 bg-gray-700 border border-gray-600 text-white placeholder-gray-400 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500">
            <button type="button" 
                    onclick="${removeFunction}(this)"
                    class="px-3 py-2 text-red-400 hover:text-red-300">
                <svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
                </svg>
            </button>
        `;
        container.appendChild(newItem);
    }
    
    /**
     * 削除ボタンの表示/非表示を更新
     */
    static updateRemoveButtons(className) {
        const items = document.querySelectorAll(`.${className}`);
        items.forEach((item) => {
            const removeButton = item.querySelector('button');
            if (removeButton) {
                if (items.length > 1) {
                    removeButton.classList.remove('hidden');
                } else {
                    removeButton.classList.add('hidden');
                }
            }
        });
    }
}

/**
 * 通知マネージャークラス
 */
class NotificationManager {
    
    /**
     * 通知を表示
     */
    static show(message, type = 'info', duration = 4000) {
        // 既存の通知を削除
        this.clearAll();
        
        const notification = document.createElement('div');
        notification.className = `notification fixed top-4 right-4 z-50 p-4 rounded-lg text-white max-w-sm transform transition-all duration-300 translate-x-full opacity-0`;
        
        const typeClasses = {
            'error': 'bg-red-600',
            'warning': 'bg-yellow-600',
            'success': 'bg-green-600',
            'info': 'bg-blue-600'
        };
        
        notification.classList.add(typeClasses[type] || typeClasses.info);
        notification.innerHTML = `
            <div class="flex items-start justify-between">
                <div class="flex">
                    <div class="mr-3 mt-0.5">
                        ${this.getIcon(type)}
                    </div>
                    <div>
                        <p class="text-sm font-medium">${CommonUtils.escapeHtml(message)}</p>
                    </div>
                </div>
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
        if (duration > 0) {
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.classList.add('translate-x-full', 'opacity-0');
                    setTimeout(() => {
                        if (notification.parentNode) {
                            notification.remove();
                        }
                    }, 300);
                }
            }, duration);
        }
    }
    
    /**
     * 全ての通知をクリア
     */
    static clearAll() {
        const existingNotifications = document.querySelectorAll('.notification');
        existingNotifications.forEach(notification => notification.remove());
    }
    
    /**
     * 通知アイコンを取得
     */
    static getIcon(type) {
        const icons = {
            'success': '<svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path></svg>',
            'error': '<svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path></svg>',
            'warning': '<svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z"></path></svg>',
            'info': '<svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>'
        };
        return icons[type] || icons.info;
    }
}

/**
 * モーダルマネージャークラス
 */
class ModalManager {
    constructor() {
        this.openModals = new Set();
        this.setupGlobalListeners();
    }
    
    setupGlobalListeners() {
        // ESCキーでモーダルを閉じる
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && this.openModals.size > 0) {
                this.closeLastModal();
            }
        });
        
        // モーダル外クリックで閉じる
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('modal-backdrop')) {
                const modalContent = e.target.querySelector('.modal-content');
                if (modalContent) {
                    this.closeModal(modalContent.id || 'unknown');
                }
            }
        });
    }
    
    openModal(modalId) {
        const modal = document.getElementById(modalId);
        if (!modal) {
            console.error(`モーダル ${modalId} が見つかりません`);
            return false;
        }
        
        modal.classList.remove('hidden');
        this.openModals.add(modalId);
        
        // ページのスクロールを無効化
        document.body.style.overflow = 'hidden';
        
        // フォーカス管理
        this.setModalFocus(modal);
        
        return true;
    }
    
    closeModal(modalId) {
        const modal = document.getElementById(modalId);
        if (!modal) {
            console.error(`モーダル ${modalId} が見つかりません`);
            return false;
        }
        
        modal.classList.add('hidden');
        this.openModals.delete(modalId);
        
        // 他にモーダルが開いていない場合のみスクロールを有効化
        if (this.openModals.size === 0) {
            document.body.style.overflow = '';
        }
        
        return true;
    }
    
    closeLastModal() {
        if (this.openModals.size > 0) {
            const lastModal = Array.from(this.openModals).pop();
            this.closeModal(lastModal);
        }
    }
    
    setModalFocus(modal) {
        setTimeout(() => {
            const firstInput = modal.querySelector('input, textarea, select, button');
            if (firstInput) {
                firstInput.focus();
            }
        }, 100);
    }
    
    resetForm(modalId) {
        const modal = document.getElementById(modalId);
        if (!modal) return;
        
        const forms = modal.querySelectorAll('form');
        forms.forEach(form => form.reset());
        
        // カスタムリセット処理
        const customResetElements = modal.querySelectorAll('[data-reset]');
        customResetElements.forEach(element => {
            const resetType = element.dataset.reset;
            switch (resetType) {
                case 'innerHTML':
                    element.innerHTML = '';
                    break;
                case 'value':
                    element.value = '';
                    break;
                case 'selected':
                    element.classList.remove('selected', 'active');
                    break;
            }
        });
    }
}

/**
 * 検索機能マネージャー
 */
class SearchManager {
    
    /**
     * 検索結果をハイライト
     */
    static highlightSearchResults(searchQuery) {
        if (!searchQuery) return;
        
        // ハイライト対象の要素を選択
        const elements = document.querySelectorAll('[data-search-target]');
        elements.forEach(element => {
            this.highlightTextInElement(element, searchQuery);
        });
    }
    
    /**
     * 要素内のテキストをハイライト
     */
    static highlightTextInElement(element, searchTerm) {
        if (!element || !searchTerm) return;
        
        const text = element.textContent;
        const regex = new RegExp(`(${this.escapeRegex(searchTerm)})`, 'gi');
        
        if (regex.test(text)) {
            const highlightedHTML = text.replace(regex, '<span class="search-highlight">$1</span>');
            element.innerHTML = highlightedHTML;
        }
    }
    
    /**
     * 正規表現用エスケープ
     */
    static escapeRegex(string) {
        return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    }
    
    /**
     * URL検索パラメータを取得
     */
    static getSearchParams() {
        return new URLSearchParams(window.location.search);
    }
    
    /**
     * 検索クエリをURLに追加
     */
    static navigateToSearch(query, additionalParams = {}) {
        const url = new URL(window.location.origin + '/notes/');
        url.searchParams.set('q', query);
        
        Object.entries(additionalParams).forEach(([key, value]) => {
            if (value) {
                url.searchParams.set(key, value);
            }
        });
        
        window.location.href = url.toString();
    }
}

/**
 * Ajax リクエストヘルパー
 */
class AjaxHelper {
    
    /**
     * GET リクエスト
     */
    static async get(url, params = {}) {
        const urlObj = new URL(url, window.location.origin);
        Object.entries(params).forEach(([key, value]) => {
            urlObj.searchParams.set(key, value);
        });
        
        const response = await fetch(urlObj.toString(), {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
            },
            credentials: 'same-origin'
        });
        
        return await response.json();
    }
    
    /**
     * POST リクエスト
     */
    static async post(url, data = {}) {
        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'X-CSRFToken': CommonUtils.getCsrfToken(),
                'Content-Type': 'application/json',
            },
            credentials: 'same-origin',
            body: JSON.stringify(data)
        });
        
        return await response.json();
    }
    
    /**
     * エラーハンドリング付きリクエスト
     */
    static async request(method, url, data = {}) {
        try {
            const result = method === 'GET' 
                ? await this.get(url, data)
                : await this.post(url, data);
                
            if (!result.success) {
                throw new Error(result.error || 'リクエストが失敗しました');
            }
            
            return result;
        } catch (error) {
            console.error('Ajax request error:', error);
            NotificationManager.show(error.message, 'error');
            throw error;
        }
    }
}

// グローバルインスタンス
window.modalManager = new ModalManager();
window.CommonUtils = CommonUtils;
window.NotificationManager = NotificationManager;
window.SearchManager = SearchManager;
window.AjaxHelper = AjaxHelper;

// ESCキーでモーダルを閉じる（レガシー対応）
document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') {
        window.modalManager.closeLastModal();
    }
});

// ページロード完了時の共通処理
document.addEventListener('DOMContentLoaded', function() {
    // タッチデバイス対応
    if (CommonUtils.isTouchDevice()) {
        document.body.classList.add('touch-device');
    }
    
    // 既存の検索語をハイライト
    const searchParams = SearchManager.getSearchParams();
    const searchQuery = searchParams.get('q');
    if (searchQuery) {
        SearchManager.highlightSearchResults(searchQuery);
    }
});