// ========================================
// static/js/common.js - 共通ライブラリ
// ========================================

/**
 * グローバル共通機能クラス
 */
class CommonUtils {
    
    // ========================================
    // 通知機能
    // ========================================
    
    static showNotification(message, type = 'info', duration = 4000) {
        // 既存の通知を削除
        const existingNotifications = document.querySelectorAll('.notification');
        existingNotifications.forEach(notification => notification.remove());
        
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
                        ${this.getNotificationIcon(type)}
                    </div>
                    <div>
                        <p class="text-sm font-medium">${this.escapeHtml(message)}</p>
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
    
    static getNotificationIcon(type) {
        const icons = {
            'success': '<svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path></svg>',
            'error': '<svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path></svg>',
            'warning': '<svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z"></path></svg>',
            'info': '<svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>'
        };
        return icons[type] || icons.info;
    }
    
    // ========================================
    // セキュリティ・ユーティリティ
    // ========================================
    
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
    
    static getCsrfToken() {
        // Cookieから取得
        const cookies = document.cookie.split(';');
        for (let cookie of cookies) {
            const [name, value] = cookie.trim().split('=');
            if (name === 'csrftoken') {
                return value;
            }
        }
        
        // フォームから取得
        const csrfInput = document.querySelector('[name=csrfmiddlewaretoken]');
        if (csrfInput) {
            return csrfInput.value;
        }
        
        return '';
    }
    
    // ========================================
    // デバイス判定
    // ========================================
    
    static isTouchDevice() {
        return 'ontouchstart' in window || navigator.maxTouchPoints > 0;
    }
    
    static isMobile() {
        return window.innerWidth <= 768;
    }
    
    // ========================================
    // URL操作
    // ========================================
    
    static updateUrlParams(params, replaceState = true) {
        const url = new URL(window.location);
        
        Object.keys(params).forEach(key => {
            if (params[key] !== null && params[key] !== undefined && params[key] !== '') {
                url.searchParams.set(key, params[key]);
            } else {
                url.searchParams.delete(key);
            }
        });
        
        if (replaceState) {
            window.history.replaceState({}, '', url.toString());
        } else {
            window.history.pushState({}, '', url.toString());
        }
    }
    
    static getUrlParam(name) {
        const urlParams = new URLSearchParams(window.location.search);
        return urlParams.get(name);
    }
    
    static removeUrlParam(name) {
        const url = new URL(window.location);
        url.searchParams.delete(name);
        window.history.replaceState({}, '', url.toString());
    }
    
    // ========================================
    // 検索関連
    // ========================================
    
    static performSearch(query, targetUrl = null) {
        if (!query || !query.trim()) {
            this.showNotification('検索語を入力してください', 'warning');
            return;
        }
        
        this.showSearchIndicator();
        
        const url = new URL(targetUrl || '/notes/', window.location.origin);
        url.searchParams.set('q', query.trim());
        url.searchParams.delete('page'); // ページネーションをリセット
        
        setTimeout(() => {
            window.location.href = url.toString();
        }, 200);
    }
    
    static showSearchIndicator() {
        const indicator = document.getElementById('search-indicator');
        if (indicator) {
            indicator.classList.remove('hidden');
        }
    }
    
    static hideSearchIndicator() {
        const indicator = document.getElementById('search-indicator');
        if (indicator) {
            indicator.classList.add('hidden');
        }
    }
    
    // ========================================
    // アニメーション・UI
    // ========================================
    
    static addLoadingState(element, loadingText = 'Loading...') {
        if (!element) return;
        
        element.disabled = true;
        element.dataset.originalText = element.textContent;
        element.innerHTML = `
            <svg class="animate-spin -ml-1 mr-3 h-4 w-4 text-white inline" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            ${loadingText}
        `;
    }
    
    static removeLoadingState(element) {
        if (!element) return;
        
        element.disabled = false;
        if (element.dataset.originalText) {
            element.textContent = element.dataset.originalText;
            delete element.dataset.originalText;
        }
    }
    
    static smoothScrollTo(element) {
        if (element) {
            element.scrollIntoView({
                behavior: 'smooth',
                block: 'start'
            });
        }
    }
    
    // ========================================
    // フォーム関連
    // ========================================
    
    static validateForm(formElement) {
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
    
    static resetForm(formElement) {
        formElement.reset();
        
        // エラー状態をクリア
        const errorFields = formElement.querySelectorAll('.border-red-500');
        errorFields.forEach(field => field.classList.remove('border-red-500'));
        
        // カスタムリセット
        const customResetElements = formElement.querySelectorAll('[data-reset]');
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
    
    // ========================================
    // ローカルストレージ
    // ========================================
    
    static saveToStorage(key, data) {
        try {
            localStorage.setItem(key, JSON.stringify(data));
            return true;
        } catch (e) {
            console.warn('ローカルストレージへの保存に失敗:', e);
            return false;
        }
    }
    
    static loadFromStorage(key) {
        try {
            const data = localStorage.getItem(key);
            return data ? JSON.parse(data) : null;
        } catch (e) {
            console.warn('ローカルストレージからの読み込みに失敗:', e);
            return null;
        }
    }
    
    static removeFromStorage(key) {
        try {
            localStorage.removeItem(key);
            return true;
        } catch (e) {
            console.warn('ローカルストレージからの削除に失敗:', e);
            return false;
        }
    }
    
    // ========================================
    // デバッグ
    // ========================================
    
    static debug(message, data = null) {
        if (window.DEBUG || localStorage.getItem('debug') === 'true') {
            console.log(`[DEBUG] ${message}`, data);
        }
    }
    
    static error(message, error = null) {
        console.error(`[ERROR] ${message}`, error);
    }
}

/**
 * タグ機能の共通クラス
 */
class TagUtils {
    static performTagSearch(tagName, targetUrl = '/notes/') {
        if (!tagName) {
            CommonUtils.showNotification('タグ名が指定されていません', 'warning');
            return;
        }
        
        CommonUtils.debug('タグ検索実行:', tagName);
        CommonUtils.performSearch(tagName, targetUrl);
    }
    
    static applyTagClickAnimation(tagElement) {
        if (!tagElement) return;
        
        tagElement.classList.add('clicked');
        
        setTimeout(() => {
            tagElement.classList.remove('clicked');
        }, 300);
        
        // タッチデバイス対応
        if (CommonUtils.isTouchDevice()) {
            tagElement.style.transform = 'scale(0.95)';
            setTimeout(() => {
                tagElement.style.transform = 'scale(1)';
            }, 150);
        }
    }
    
    static setupTagClickHandlers(selector = '.tag-clickable') {
        const tags = document.querySelectorAll(selector);
        
        tags.forEach(tag => {
            tag.addEventListener('click', function(e) {
                e.preventDefault();
                e.stopPropagation();
                
                const tagName = this.getAttribute('data-tag') || this.textContent.trim();
                
                TagUtils.applyTagClickAnimation(this);
                TagUtils.performTagSearch(tagName);
            });
            
            // アクセシビリティ対応
            tag.addEventListener('keydown', function(e) {
                if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    this.click();
                }
            });
        });
        
        CommonUtils.debug(`${tags.length}個のタグにクリックハンドラーを設定`);
    }
}

/**
 * モーダル管理クラス
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
            CommonUtils.error(`モーダル ${modalId} が見つかりません`);
            return false;
        }
        
        modal.classList.remove('hidden');
        this.openModals.add(modalId);
        
        // ページのスクロールを無効化
        document.body.style.overflow = 'hidden';
        
        // フォーカス管理
        this.setModalFocus(modal);
        
        CommonUtils.debug(`モーダル ${modalId} を開きました`);
        return true;
    }
    
    closeModal(modalId) {
        const modal = document.getElementById(modalId);
        if (!modal) {
            CommonUtils.error(`モーダル ${modalId} が見つかりません`);
            return false;
        }
        
        modal.classList.add('hidden');
        this.openModals.delete(modalId);
        
        // 他にモーダルが開いていない場合のみスクロールを有効化
        if (this.openModals.size === 0) {
            document.body.style.overflow = '';
        }
        
        CommonUtils.debug(`モーダル ${modalId} を閉じました`);
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
        forms.forEach(form => CommonUtils.resetForm(form));
    }
}

// ========================================
// グローバルインスタンス
// ========================================

// グローバルモーダルマネージャー
window.modalManager = new ModalManager();

// 共通関数のエイリアス（下位互換性のため）
window.showNotification = CommonUtils.showNotification.bind(CommonUtils);
window.escapeHtml = CommonUtils.escapeHtml.bind(CommonUtils);
window.getCsrfToken = CommonUtils.getCsrfToken.bind(CommonUtils);
window.isTouchDevice = CommonUtils.isTouchDevice.bind(CommonUtils);

// ========================================
// DOMContentLoaded 時の初期化
// ========================================

document.addEventListener('DOMContentLoaded', function() {
    CommonUtils.debug('共通ライブラリが初期化されました');
    
    // タグクリック機能の自動設定
    TagUtils.setupTagClickHandlers();
    
    // スムーススクロールの設定
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                CommonUtils.smoothScrollTo(target);
            }
        });
    });
    
    // 自動でメッセージを隠す
    setTimeout(() => {
        const alerts = document.querySelectorAll('.alert');
        alerts.forEach(alert => {
            alert.style.opacity = '0';
            setTimeout(() => {
                alert.remove();
            }, 300);
        });
    }, 5000);
    
    // 検索インジケーターを隠す
    CommonUtils.hideSearchIndicator();
    
    CommonUtils.debug('共通ライブラリの初期化完了');
});

// ページロード完了時の処理
window.addEventListener('load', function() {
    CommonUtils.hideSearchIndicator();
    CommonUtils.debug('ページロード完了');
});

// ページから離れる前の処理
window.addEventListener('beforeunload', function() {
    // 一時的なデータを保存
    CommonUtils.debug('ページを離れます');
});

// ========================================
// エクスポート
// ========================================

if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        CommonUtils,
        TagUtils,
        ModalManager
    };
}