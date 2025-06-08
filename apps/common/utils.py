# ========================================
# apps/common/utils.py
# ========================================

import json
from datetime import datetime, timedelta
from django.utils import timezone
from django.db.models import Q

class SearchHelper:
    """検索ヘルパークラス"""
    
    @staticmethod
    def build_search_query(query_string, search_fields):
        """検索クエリを構築"""
        if not query_string or not search_fields:
            return Q()
        
        # 検索語を分割（スペース区切り）
        terms = query_string.split()
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
        
        import re
        pattern = re.compile(re.escape(term), re.IGNORECASE)
        return pattern.sub(f'<mark>{term}</mark>', text)

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
        import re
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
        import re
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