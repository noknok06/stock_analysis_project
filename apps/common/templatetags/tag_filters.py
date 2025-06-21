"""
タグ表示用のテンプレートフィルター
apps/common/templatetags/tag_filters.py
"""

from django import template
from django.utils.safestring import mark_safe
import re

register = template.Library()

@register.filter
def tag_style(tag):
    """
    タグオブジェクトから適切なスタイル属性を生成
    カスタム色が設定されている場合はインラインスタイル、
    未設定の場合は空文字（CSSクラスを使用）
    """
    if hasattr(tag, 'color') and tag.color:
        return mark_safe(f'style="background-color: {tag.color}; color: white; border-color: {tag.color};"')
    return ''

@register.filter
def tag_css_class(tag):
    """
    タグオブジェクトから適切なCSSクラスを生成
    カスタム色が設定されている場合は空文字、
    未設定の場合はカテゴリベースのクラス
    """
    if hasattr(tag, 'color') and tag.color:
        return ''  # カスタム色がある場合はCSSクラスを使用しない
    
    if hasattr(tag, 'get_color_class'):
        return tag.get_color_class()
    
    # フォールバック: カテゴリベースのデフォルトクラス
    category_map = {
        'STOCK': 'bg-red-600',
        'SECTOR': 'bg-green-600', 
        'STRATEGY': 'bg-blue-600',
        'ANALYSIS': 'bg-orange-600',
        'RISK': 'bg-yellow-600',
        'EVENT': 'bg-indigo-600',
        'OTHER': 'bg-gray-600',
    }
    
    category = getattr(tag, 'category', 'OTHER')
    return category_map.get(category, 'bg-gray-600')

@register.filter
def tag_color_value(tag):
    """
    タグの実際の色値を取得
    """
    if hasattr(tag, 'get_effective_color'):
        return tag.get_effective_color()
    elif hasattr(tag, 'color') and tag.color:
        return tag.color
    else:
        # デフォルトカラー
        category_map = {
            'STOCK': '#dc2626',
            'SECTOR': '#16a34a', 
            'STRATEGY': '#2563eb',
            'ANALYSIS': '#ea580c',
            'RISK': '#eab308',
            'EVENT': '#4f46e5',
            'OTHER': '#6b7280',
        }
        category = getattr(tag, 'category', 'OTHER')
        return category_map.get(category, '#6b7280')

@register.simple_tag
def render_tag(tag, classes='', show_count=False):
    """
    タグを適切なスタイルでレンダリング
    
    使用例:
    {% render_tag tag classes="px-2 py-1 text-xs rounded-full" show_count=True %}
    """
    base_classes = f"inline-flex items-center {classes}"
    
    # カスタム色とCSSクラスの決定
    if hasattr(tag, 'color') and tag.color:
        style = f'background-color: {tag.color}; color: white; border-color: {tag.color};'
        css_class = base_classes
    else:
        style = ''
        color_class = tag_css_class(tag)
        css_class = f"{base_classes} {color_class} text-white"
    
    # タグ名の表示
    tag_text = str(tag)
    if show_count and hasattr(tag, 'usage_count'):
        tag_text += f" ({tag.usage_count})"
    
    # HTML生成
    if style:
        html = f'<span class="{css_class}" style="{style}">{tag_text}</span>'
    else:
        html = f'<span class="{css_class}">{tag_text}</span>'
    
    return mark_safe(html)

@register.filter
def highlight_search(text, search_query):
    """
    検索語をハイライト表示（既存のフィルター）
    """
    if not search_query or not text:
        return text
    
    # 検索語を大文字小文字を無視してハイライト
    pattern = re.compile(re.escape(search_query), re.IGNORECASE)
    highlighted = pattern.sub(
        lambda m: f'<span class="search-highlight">{m.group()}</span>',
        str(text)
    )
    
    return mark_safe(highlighted)

@register.filter
def is_custom_color(tag):
    """
    タグにカスタム色が設定されているかチェック
    """
    return hasattr(tag, 'color') and bool(tag.color)

@register.simple_tag
def tag_opacity_style(tag, base_opacity=1.0, hover_opacity=0.8):
    """
    タグのホバー時透明度スタイルを生成
    """
    if hasattr(tag, 'color') and tag.color:
        return mark_safe(f'style="opacity: {base_opacity};" onmouseenter="this.style.opacity=\'{hover_opacity}\'" onmouseleave="this.style.opacity=\'{base_opacity}\'"')
    return ''

@register.filter
def tag_border_style(tag):
    """
    タグのボーダースタイルを生成
    """
    if hasattr(tag, 'color') and tag.color:
        return mark_safe(f'border: 1px solid {tag.color};')
    return 'border: 1px solid #6b7280;'  # デフォルトのグレー