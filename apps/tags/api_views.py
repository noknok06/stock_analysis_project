# ========================================
# apps/tags/api_views.py - ユーザー固有タグAPI
# ========================================

import json
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from apps.tags.models import Tag
from apps.common.utils import SearchHelper

@login_required
@require_http_methods(["GET"])
def tag_search_api(request):
    """ユーザー固有タグ検索API"""
    try:
        query = request.GET.get('q', '').strip()
        category = request.GET.get('category', '')
        limit = int(request.GET.get('limit', 20))
        
        # ユーザー固有のタグのみ取得
        tags = Tag.objects.get_for_user(request.user).filter(is_active=True)
        
        if query:
            tags = tags.filter(name__icontains=query)
        
        if category:
            tags = tags.filter(category=category)
        
        tags = tags.order_by('-usage_count', 'name')[:limit]
        
        results = [
            {
                'id': tag.pk,
                'name': tag.name,
                'category': tag.category,
                'usage_count': tag.usage_count,
                'description': tag.description
            }
            for tag in tags
        ]
        
        return JsonResponse({
            'success': True,
            'tags': results,
            'count': len(results)
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@csrf_exempt
@require_http_methods(["POST"])
def tag_create_api(request):
    """ユーザー固有タグ作成API"""
    try:
        data = json.loads(request.body)
        tag_name = data.get('name', '').strip()
        category = data.get('category', 'OTHER')
        description = data.get('description', '')
        
        if not tag_name:
            return JsonResponse({
                'success': False,
                'error': 'タグ名は必須です'
            }, status=400)
        
        # #がない場合は自動で追加
        if not tag_name.startswith('#'):
            tag_name = '#' + tag_name
        
        # ユーザー内での重複チェック
        if Tag.objects.filter(user=request.user, name=tag_name).exists():
            existing_tag = Tag.objects.get(user=request.user, name=tag_name)
            return JsonResponse({
                'success': True,
                'tag': {
                    'id': existing_tag.pk,
                    'name': existing_tag.name,
                    'category': existing_tag.category,
                    'usage_count': existing_tag.usage_count,
                    'is_existing': True
                },
                'message': '既存のタグを返します'
            })
        
        # 新規タグ作成（ユーザー固有）
        tag = Tag.objects.create(
            user=request.user,
            name=tag_name,
            category=category,
            description=description,
            usage_count=1
        )
        
        return JsonResponse({
            'success': True,
            'tag': {
                'id': tag.pk,
                'name': tag.name,
                'category': tag.category,
                'usage_count': tag.usage_count,
                'is_existing': False
            },
            'message': 'タグを作成しました'
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': '無効なJSONデータです'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@require_http_methods(["GET"])
def tag_suggestions_api(request):
    """ユーザー固有AI支援タグ推奨API"""
    try:
        content = request.GET.get('content', '')
        stock_code = request.GET.get('stock_code', '')
        company_name = request.GET.get('company_name', '')
        investment_reason = request.GET.get('investment_reason', '')
        status = request.GET.get('status', '')
        
        # 既存のタグを除外するためのリスト
        existing_tags_str = request.GET.get('existing_tags', '[]')
        try:
            existing_tags = json.loads(existing_tags_str)
        except:
            existing_tags = []
        
        # ユーザーの既存タグも考慮した推奨ロジック
        suggestions = generate_tag_suggestions_for_user(
            request.user,
            {
                'content': content,
                'stock_code': stock_code,
                'company_name': company_name,
                'investment_reason': investment_reason,
                'status': status
            }, 
            existing_tags
        )
        
        return JsonResponse({
            'success': True,
            'suggestions': suggestions,
            'count': len(suggestions)
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


def generate_tag_suggestions_for_user(user, content_data, existing_tags=None):
    """ユーザー固有のタグ推奨ロジック"""
    if existing_tags is None:
        existing_tags = []
    
    suggestions = []
    
    # 全てのコンテンツを結合
    text = ' '.join([
        content_data.get('content', ''),
        content_data.get('stock_code', ''),
        content_data.get('company_name', ''),
        content_data.get('investment_reason', '')
    ]).lower()
    
    # ユーザーの既存タグから類似するものを提案
    user_tags = Tag.objects.get_for_user(user).filter(
        is_active=True,
        usage_count__gt=0
    ).order_by('-usage_count')
    
    # キーワードベースの推奨マッピング
    keyword_mapping = {
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
        '優待': ['#株主優待', '#優待株'],
        '新規': ['#新規投資', '#初回購入'],
        '追加': ['#追加投資', '#買い増し'],
        'ニュース': ['#ニュース', '#市場動向'],
        '業績': ['#業績分析', '#決算'],
        '競合': ['#競合分析', '#業界動向']
    }
    
    # キーワードマッチング
    for keyword, tags in keyword_mapping.items():
        if keyword in text:
            suggestions.extend(tags)
    
    # ユーザーの既存タグから関連するものを提案
    for tag in user_tags[:10]:  # 上位10個のタグをチェック
        tag_words = tag.name.replace('#', '').lower()
        if any(word in text for word in tag_words.split()):
            suggestions.append(tag.name)
    
    # ステータスベースの推奨
    status = content_data.get('status', '')
    if status == 'ACTIVE':
        suggestions.append('#アクティブ投資')
    elif status == 'MONITORING':
        suggestions.append('#要監視')
    elif status == 'ATTENTION':
        suggestions.append('#要注意')
    elif status == 'ARCHIVED':
        suggestions.append('#アーカイブ')
    
    # 銘柄コードベースの推奨
    stock_code = content_data.get('stock_code', '').strip()
    company_name = content_data.get('company_name', '').strip()
    if stock_code and len(stock_code) == 4:
        if company_name:
            suggestions.append(f'#{stock_code}{company_name}')
        else:
            suggestions.append(f'#{stock_code}')
    
    # 既存のタグと重複除去
    unique_suggestions = []
    for tag in suggestions:
        if tag not in existing_tags and tag not in unique_suggestions:
            unique_suggestions.append(tag)
    
    # ユーザーが既に持っているタグを優先
    prioritized_suggestions = []
    for suggestion in unique_suggestions:
        if Tag.objects.filter(user=user, name=suggestion).exists():
            prioritized_suggestions.insert(0, suggestion)
        else:
            prioritized_suggestions.append(suggestion)
    
    # 最大6個まで
    return prioritized_suggestions[:6]


@login_required 
@require_http_methods(["GET"])
def popular_tags_api(request):
    """ユーザー固有人気タグAPI"""
    try:
        category = request.GET.get('category', '')
        limit = int(request.GET.get('limit', 10))
        
        # ユーザー固有のタグのみ取得
        tags = Tag.objects.get_for_user(request.user).filter(is_active=True)
        
        if category:
            tags = tags.filter(category=category)
        
        tags = tags.order_by('-usage_count')[:limit]
        
        results = [
            {
                'id': tag.pk,
                'name': tag.name,
                'category': tag.category,
                'usage_count': tag.usage_count
            }
            for tag in tags
        ]
        
        return JsonResponse({
            'success': True,
            'tags': results,
            'count': len(results)
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@require_http_methods(["GET"])
def user_tag_stats_api(request):
    """ユーザータグ統計API"""
    try:
        user_tags = Tag.objects.get_for_user(request.user)
        
        stats = {
            'total_tags': user_tags.count(),
            'active_tags': user_tags.filter(is_active=True).count(),
            'used_tags': user_tags.filter(usage_count__gt=0).count(),
            'total_usage': sum(user_tags.values_list('usage_count', flat=True)),
            'categories': {}
        }
        
        # カテゴリ別統計
        for category, display_name in Tag.CATEGORY_CHOICES:
            category_tags = user_tags.filter(category=category)
            stats['categories'][category] = {
                'display_name': display_name,
                'count': category_tags.count(),
                'used_count': category_tags.filter(usage_count__gt=0).count(),
                'total_usage': sum(category_tags.values_list('usage_count', flat=True))
            }
        
        return JsonResponse({
            'success': True,
            'stats': stats
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)