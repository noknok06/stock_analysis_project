# ========================================
# apps/common/utils.py - SearchHelper修正版（循環インポート回避）
# ========================================

import json
import re
from datetime import datetime, timedelta
from django.utils import timezone
from django.db.models import Q
from django.utils.html import escape
from django.utils.safestring import mark_safe

from apps.notes.models import Notebook, Entry
from apps.tags.models import Tag

class SearchHelper:
    """検索ヘルパークラス（循環インポート回避版）"""
    
    @staticmethod
    def build_search_query(query_string, search_fields):
        """基本的な検索クエリを構築"""
        if not query_string or not search_fields:
            return Q()
        
        # 検索語を分割（スペース区切り）
        terms = [term.strip() for term in query_string.split() if term.strip()]
        q_objects = Q()
        
        for term in terms:
            term_query = Q()
            for field in search_fields:
                term_query |= Q(**{f"{field}__icontains": term})
            q_objects &= term_query
        
        return q_objects
    
    @staticmethod
    def highlight_search_term(text, term):
        """検索語をハイライト"""
        if not term or not text:
            return text
        
        pattern = re.compile(re.escape(term), re.IGNORECASE)
        return pattern.sub(f'<mark>{term}</mark>', text)
    
    @staticmethod
    def extract_search_entities(query_string):
        """
        検索クエリから特定のエンティティを抽出
        （銘柄コード、タグ、日付など）
        """
        entities = {
            'stock_codes': [],
            'tags': [],
            'dates': [],
            'numbers': [],
            'regular_terms': []
        }
        
        if not query_string:
            return entities
        
        terms = query_string.split()
        
        for term in terms:
            term = term.strip()
            if not term:
                continue
            
            # 銘柄コード（4桁数字）
            if re.match(r'^\d{4}$', term):
                entities['stock_codes'].append(term)
            
            # タグ（#で始まる）
            elif term.startswith('#'):
                entities['tags'].append(term)
            
            # 日付パターン
            elif re.match(r'^\d{4}[-/]\d{1,2}[-/]\d{1,2}$', term):
                entities['dates'].append(term)
            
            # 数値
            elif re.match(r'^\d+$', term):
                entities['numbers'].append(term)
            
            # 通常の検索語
            else:
                entities['regular_terms'].append(term)
        
        return entities
    
    @staticmethod
    def build_smart_search_query(query_string, search_fields):
        """
        スマート検索クエリを構築（エンティティ認識付き）
        ※モデル依存を除去した版
        """
        if not query_string or not search_fields:
            return Q()
        
        entities = SearchHelper.extract_search_entities(query_string)
        main_query = Q()
        
        # 通常の検索語
        if entities['regular_terms']:
            for term in entities['regular_terms']:
                term_query = Q()
                for field in search_fields:
                    term_query |= Q(**{f"{field}__icontains": term})
                main_query &= term_query
        
        # 銘柄コード検索（特定フィールドがある場合）
        if entities['stock_codes']:
            stock_fields = [f for f in search_fields if 'stock_code' in f]
            if stock_fields:
                stock_query = Q()
                for code in entities['stock_codes']:
                    for field in stock_fields:
                        stock_query |= Q(**{f"{field}__exact": code})
                main_query &= stock_query
        
        # タグ検索（特定フィールドがある場合）
        if entities['tags']:
            tag_fields = [f for f in search_fields if 'tag' in f]
            if tag_fields:
                tag_query = Q()
                for tag in entities['tags']:
                    for field in tag_fields:
                        tag_query |= Q(**{f"{field}__exact": tag})
                main_query &= tag_query
        
        return main_query
    
    @staticmethod
    def create_comprehensive_search_fields():
        """包括的な検索フィールド設定を返す"""
        return {
            'high_priority': [
                'title',
                'tags__name',
                'entries__stock_code',
            ],
            'medium_priority': [
                'subtitle',
                'description',
                'entries__company_name',
            ],
            'low_priority': [
                'investment_strategy',
                'tags__description',
                'entries__title',
            ],
            'exact_match': [
                'title',
                'tags__name',
                'entries__stock_code',
            ]
        }
    
    @staticmethod
    def build_priority_search_query(query_string, search_fields_config=None):
        """
        優先度付き検索クエリを構築
        """
        if not query_string:
            return Q()
        
        if search_fields_config is None:
            search_fields_config = SearchHelper.create_comprehensive_search_fields()
        
        # 検索語を分割して処理
        search_terms = [term.strip() for term in query_string.split() if term.strip()]
        if not search_terms:
            return Q()
        
        main_query = Q()
        
        for term in search_terms:
            term_query = Q()
            
            # 高優先度フィールド
            for field in search_fields_config.get('high_priority', []):
                term_query |= Q(**{f"{field}__icontains": term})
            
            # 中優先度フィールド
            for field in search_fields_config.get('medium_priority', []):
                term_query |= Q(**{f"{field}__icontains": term})
                
            # 低優先度フィールド
            for field in search_fields_config.get('low_priority', []):
                term_query |= Q(**{f"{field}__icontains": term})
            
            # 完全一致ボーナス
            exact_match_query = Q()
            for field in search_fields_config.get('exact_match', []):
                exact_match_query |= Q(**{f"{field}__iexact": term})
            
            # 部分一致または完全一致
            main_query &= (term_query | exact_match_query)
        
        return main_query


class DateHelper:
    """日付ヘルパークラス"""
    
    @staticmethod
    def get_month_range(year=None, month=None):
        """指定月の開始日と終了日を取得"""
        if not year or not month:
            now = timezone.now()
            year, month = now.year, now.month
        
        start_date = datetime(year, month, 1)
        if month == 12:
            end_date = datetime(year + 1, 1, 1) - timedelta(days=1)
        else:
            end_date = datetime(year, month + 1, 1) - timedelta(days=1)
        
        return start_date, end_date
    
    @staticmethod
    def get_relative_time_display(dt):
        """相対時間表示"""
        now = timezone.now()
        diff = now - dt
        
        if diff.days > 7:
            return dt.strftime('%Y/%m/%d')
        elif diff.days > 0:
            return f'{diff.days}日前'
        elif diff.seconds > 3600:
            hours = diff.seconds // 3600
            return f'{hours}時間前'
        elif diff.seconds > 60:
            minutes = diff.seconds // 60
            return f'{minutes}分前'
        else:
            return 'たった今'


class TagHelper:
    """タグヘルパークラス"""
    
    @staticmethod
    def parse_tag_string(tag_string):
        """タグ文字列をパース（#区切り）"""
        if not tag_string:
            return []
        
        # #で始まる文字列を抽出
        tags = re.findall(r'#(\w+)', tag_string)
        return [tag.strip() for tag in tags if tag.strip()]
    
    @staticmethod
    def suggest_tags(content, existing_tags=None):
        """コンテンツからタグを推奨"""
        suggestions = []
        content_lower = content.lower()
        
        # キーワードベースの推奨
        keyword_mapping = {
            '配当': ['#高配当', '#配当株', '#株主還元'],
            '成長': ['#成長株', '#長期投資'],
            '割安': ['#割安株', '#バリュー投資'],
            '技術': ['#テクノロジー', '#イノベーション'],
            '決算': ['#決算分析', '#業績好調'],
            'リスク': ['#要注意', '#リスク要因'],
        }
        
        for keyword, tags in keyword_mapping.items():
            if keyword in content_lower:
                suggestions.extend(tags)
        
        # 重複除去
        suggestions = list(set(suggestions))
        
        # 既存タグを除外
        if existing_tags:
            existing_names = [tag.name for tag in existing_tags]
            suggestions = [tag for tag in suggestions if tag not in existing_names]
        
        return suggestions[:5]  # 最大5個まで


class ContentHelper:
    """コンテンツヘルパークラス"""
    
    @staticmethod
    def extract_summary(content, max_length=100):
        """コンテンツからサマリーを抽出"""
        if isinstance(content, dict):
            # JSONコンテンツの場合
            text_fields = ['summary', 'analysis', 'description', 'content']
            for field in text_fields:
                if field in content and content[field]:
                    text = content[field]
                    break
            else:
                text = str(content)
        else:
            text = str(content)
        
        # HTMLタグを除去
        text = re.sub(r'<[^>]+>', '', text)
        
        # 改行を空白に変換
        text = re.sub(r'\s+', ' ', text).strip()
        
        # 指定文字数でカット
        if len(text) > max_length:
            text = text[:max_length] + '...'
        
        return text
    
    @staticmethod
    def format_json_content(content, entry_type):
        """エントリータイプに応じたJSON整形"""
        if not isinstance(content, dict):
            return content
        
        formatted = {}
        
        if entry_type == 'ANALYSIS':
            # 決算分析用のフォーマット
            formatted.update({
                'summary': content.get('summary', ''),
                'key_metrics': content.get('key_metrics', {}),
                'analysis': content.get('analysis', ''),
                'outlook': content.get('outlook', ''),
            })
        elif entry_type == 'NEWS':
            # ニュース用のフォーマット
            formatted.update({
                'headline': content.get('headline', ''),
                'content': content.get('content', ''),
                'impact': content.get('impact', ''),
                'stock_impact': content.get('stock_impact', ''),
            })
        elif entry_type == 'CALCULATION':
            # 計算結果用のフォーマット
            formatted.update({
                'current_price': content.get('current_price', ''),
                'calculations': content.get('calculations', {}),
                'fair_value': content.get('fair_value', ''),
                'recommendation': content.get('recommendation', ''),
            })
        elif entry_type == 'MEMO':
            # メモ用のフォーマット
            formatted.update({
                'observation': content.get('observation', ''),
                'market_trend': content.get('market_trend', ''),
                'personal_note': content.get('personal_note', ''),
                'next_action': content.get('next_action', ''),
            })
        else:
            formatted = content
        
        return formatted


# ========================================
# 検索関連のユーティリティ関数（モデル依存なし）
# ========================================

def get_search_autocomplete_suggestions(query_string, user, limit=10):
    """
    検索オートコンプリート候補を生成（関数として独立）
    ※views.pyから直接呼び出し用
    """
    suggestions = []
    
    if not query_string or len(query_string) < 2:
        return suggestions
    
    try:
        
        # ノートタイトルから候補
        notebook_titles = Notebook.objects.filter(
            user=user,
            title__icontains=query_string
        ).values_list('title', flat=True)[:limit//3]
        
        for title in notebook_titles:
            suggestions.append({
                'type': 'notebook',
                'text': title,
                'display': f"📓 {title}",
                'category': 'ノート'
            })
        
        # タグから候補
        tag_names = Tag.objects.filter(
            name__icontains=query_string,
            notebook__user=user
        ).distinct().values_list('name', flat=True)[:limit//3]
        
        for tag_name in tag_names:
            suggestions.append({
                'type': 'tag',
                'text': tag_name,
                'display': f"🏷️ {tag_name}",
                'category': 'タグ'
            })
        
        # 企業名から候補
        company_names = Entry.objects.filter(
            notebook__user=user,
            company_name__icontains=query_string
        ).values_list('company_name', flat=True).distinct()[:limit//3]
        
        for company_name in company_names:
            suggestions.append({
                'type': 'company',
                'text': company_name,
                'display': f"🏢 {company_name}",
                'category': '企業'
            })
        
    except ImportError as e:
        # インポートエラーの場合はログに記録
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"検索候補取得でインポートエラー: {e}")
    
    return suggestions[:limit]