# ========================================
# apps/common/templatetags/search_filters.py
# ========================================

import re
from django import template
from django.utils.safestring import mark_safe
from django.utils.html import escape

register = template.Library()

@register.filter
def highlight_search(text, search_term):
    """
    テキスト内の検索語をハイライト表示する
    
    使用例:
    {{ notebook.title|highlight_search:search_query }}
    """
    if not text or not search_term:
        return text
    
    # HTMLエスケープ
    escaped_text = escape(str(text))
    escaped_search_term = escape(str(search_term))
    
    # 検索語を複数の単語に分割
    search_words = [word.strip() for word in escaped_search_term.split() if word.strip()]
    
    # 各単語をハイライト
    highlighted_text = escaped_text
    for word in search_words:
        if word:
            # 大文字小文字を区別しない検索
            pattern = re.compile(re.escape(word), re.IGNORECASE)
            highlighted_text = pattern.sub(
                f'<span class="search-highlight">{word}</span>', 
                highlighted_text
            )
    
    return mark_safe(highlighted_text)

@register.filter
def highlight_tag_search(tag_name, search_term):
    """
    タグ名内の検索語をハイライト表示する（タグ用の特別なスタイル）
    
    使用例:
    {{ tag.name|highlight_tag_search:search_query }}
    """
    if not tag_name or not search_term:
        return tag_name
    
    escaped_tag = escape(str(tag_name))
    escaped_search = escape(str(search_term))
    
    if escaped_search.lower() in escaped_tag.lower():
        pattern = re.compile(re.escape(escaped_search), re.IGNORECASE)
        highlighted = pattern.sub(
            f'<span class="tag-search-highlight">{escaped_search}</span>', 
            escaped_tag
        )
        return mark_safe(highlighted)
    
    return tag_name

@register.filter
def contains_search_term(text, search_term):
    """
    テキストが検索語を含むかどうかをチェックする
    
    使用例:
    {% if notebook.title|contains_search_term:search_query %}
        <span class="search-match-badge">一致</span>
    {% endif %}
    """
    if not text or not search_term:
        return False
    
    return str(search_term).lower() in str(text).lower()

@register.filter
def search_match_count(text, search_term):
    """
    テキスト内の検索語の出現回数を返す
    
    使用例:
    {% if notebook.description|search_match_count:search_query > 0 %}
        <span class="match-count">{{ notebook.description|search_match_count:search_query }}箇所</span>
    {% endif %}
    """
    if not text or not search_term:
        return 0
    
    text_lower = str(text).lower()
    search_lower = str(search_term).lower()
    
    # 検索語を単語に分割
    search_words = [word.strip() for word in search_lower.split() if word.strip()]
    
    total_matches = 0
    for word in search_words:
        total_matches += text_lower.count(word)
    
    return total_matches

@register.filter
def truncate_highlight(text, search_term, max_length=100):
    """
    検索語周辺のテキストを切り出してハイライトする
    
    使用例:
    {{ notebook.investment_strategy|truncate_highlight:search_query:150 }}
    """
    if not text or not search_term:
        return text[:max_length] + '...' if len(text) > max_length else text
    
    text_str = str(text)
    search_str = str(search_term).lower()
    text_lower = text_str.lower()
    
    # 検索語の位置を見つける
    search_pos = text_lower.find(search_str)
    
    if search_pos == -1:
        # 検索語が見つからない場合は通常の切り詰め
        return text_str[:max_length] + '...' if len(text_str) > max_length else text_str
    
    # 検索語を中心とした範囲を計算
    half_length = max_length // 2
    start_pos = max(0, search_pos - half_length)
    end_pos = min(len(text_str), search_pos + len(search_str) + half_length)
    
    # テキストを切り出し
    excerpt = text_str[start_pos:end_pos]
    
    # 前後に省略記号を追加
    if start_pos > 0:
        excerpt = '...' + excerpt
    if end_pos < len(text_str):
        excerpt = excerpt + '...'
    
    # ハイライトを適用
    return highlight_search(excerpt, search_term)

@register.simple_tag
def search_summary(notebooks, search_query):
    """
    検索結果の要約情報を生成する
    
    使用例:
    {% search_summary notebooks search_query as summary %}
    {{ summary.total_matches }}件の一致
    """
    if not search_query or not notebooks:
        return {
            'total_matches': 0,
            'title_matches': 0,
            'tag_matches': 0,
            'content_matches': 0
        }
    
    search_lower = search_query.lower()
    summary = {
        'total_matches': 0,
        'title_matches': 0,
        'tag_matches': 0,
        'content_matches': 0
    }
    
    for notebook in notebooks:
        # タイトルでの一致
        if search_lower in notebook.title.lower():
            summary['title_matches'] += 1
            summary['total_matches'] += 1
        
        # タグでの一致
        for tag in notebook.tags.all():
            if search_lower in tag.name.lower():
                summary['tag_matches'] += 1
                summary['total_matches'] += 1
                break
        
        # 内容での一致
        if (hasattr(notebook, 'investment_strategy') and 
            notebook.investment_strategy and 
            search_lower in notebook.investment_strategy.lower()):
            summary['content_matches'] += 1
            summary['total_matches'] += 1
    
    return summary

@register.inclusion_tag('common/search_breadcrumb.html')
def search_breadcrumb(search_query, result_count):
    """
    検索結果のパンくずリストを表示する
    
    使用例:
    {% search_breadcrumb search_query notebooks.count %}
    """
    return {
        'search_query': search_query,
        'result_count': result_count,
        'has_search': bool(search_query)
    }