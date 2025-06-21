# ========================================
# apps/notes/help_views.py - ヘルプ・ガイド機能
# ========================================

from django.shortcuts import render
from django.views.generic import TemplateView
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin

class NotebookHelpView(LoginRequiredMixin, TemplateView):
    """ノート作成ヘルプビュー"""
    template_name = 'notes/help/notebook_guide.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # ヘルプコンテンツを構造化
        context['help_sections'] = [
            {
                'id': 'overview',
                'title': '📋 ノート作成の基本',
                'description': 'ノートブックの基本的な概念と作成フロー',
                'items': [
                    'ノートブックは「投資テーマ」単位で管理します',
                    '複数の銘柄や関連情報をまとめて記録できます', 
                    'サブノートで情報を分類・整理できます',
                    'タグで横断的な検索・フィルタリングが可能です'
                ]
            },
            {
                'id': 'fields',
                'title': '📝 各項目の記入ガイド',
                'description': 'フォームの各フィールドの効果的な書き方',
                'items': []
            },
            {
                'id': 'strategy',
                'title': '🎯 投資戦略の書き方',
                'description': '効果的な投資戦略の記述方法',
                'items': []
            },
            {
                'id': 'examples',
                'title': '💡 記入例・テンプレート',
                'description': '投資スタイル別の記入例',
                'items': []
            },
            {
                'id': 'tips',
                'title': '🚀 活用のコツ',
                'description': 'より効果的にノートを活用するためのヒント',
                'items': []
            }
        ]
        
        # フィールドガイド
        context['field_guides'] = [
            {
                'field': 'title',
                'label': 'ノートタイトル',
                'description': '投資テーマを表現する分かりやすいタイトル',
                'examples': [
                    '2025年 高配当株ウォッチ',
                    '米国成長株リサーチ',
                    'REIT銘柄比較分析',
                    '決算シーズン注目銘柄'
                ],
                'tips': [
                    '年度や期間を入れると管理しやすい',
                    '投資スタイルを明記する',
                    '後から見て分かりやすい名前にする'
                ]
            },
            {
                'field': 'investment_strategy',
                'label': '投資戦略',
                'description': 'このテーマでの投資方針と戦略を詳しく記述',
                'examples': [
                    '配当利回り3%以上、連続増配実績のある企業を中心に長期保有。四半期ごとに配当性向と財務健全性を確認し、継続保有の判断を行う。',
                    '売上成長率20%以上を3年継続している企業に投資。PEGレシオ1.5倍以下で購入し、成長鈍化の兆候が見えた時点で売却を検討。',
                    'J-REITの中でもFFO利回り4%以上、NAV倍率0.9倍以下の割安銘柄を選定。分配金利回りの持続性と資産の質を重視。'
                ],
                'tips': [
                    '具体的な数値基準を含める',
                    '買い時・売り時の判断基準を明記',
                    'リスク管理方法も記載する',
                    '定期的な見直し頻度も決める'
                ]
            }
        ]
        
        # 投資スタイル別テンプレート例
        context['style_templates'] = [
            {
                'style': '🏆 高配当株投資',
                'title': '高配当株ポートフォリオ',
                'subtitle': '配当利回り3%以上の優良銘柄で構成',
                'strategy': '配当利回り3%以上、配当性向70%以下、自己資本比率40%以上の財務健全な企業を選定。四半期ごとに業績と配当の持続性を確認し、減配リスクの高い銘柄は早期に売却する。',
                'criteria': ['配当利回り3%以上', '連続増配または安定配当', '配当性向70%以下', '自己資本比率40%以上'],
                'risks': ['減配リスク', '金利上昇による株価下落', '業績悪化による配当カット'],
                'tags': ['#高配当', '#配当株', '#長期投資', '#安定配当']
            },
            {
                'style': '🚀 成長株投資',
                'title': '成長株発掘プロジェクト',
                'subtitle': '将来性豊かな成長企業を早期発見',
                'strategy': '売上成長率年20%以上、営業利益成長率15%以上を継続している企業を重点投資。ROE15%以上、競合優位性が明確な企業を選定し、PEGレシオ1.5倍以下で購入する。',
                'criteria': ['売上成長率20%以上（3年平均）', '営業利益成長率15%以上', 'ROE15%以上', 'PEGレシオ1.5倍以下'],
                'risks': ['成長鈍化リスク', '高バリュエーションによる株価急落', '競合激化による収益性悪化'],
                'tags': ['#成長株', '#グロース投資', '#テクノロジー', '#中長期投資']
            },
            {
                'style': '💰 バリュー投資',
                'title': '割安株発掘ノート',
                'subtitle': '市場に見過ごされた優良企業を発見',
                'strategy': 'PER15倍以下、PBR1.5倍以下の割安株の中から、ROE10%以上、営業利益率5%以上の収益性を持つ企業を選定。業績改善や事業転換の兆候を捉えて投資する。',
                'criteria': ['PER15倍以下', 'PBR1.5倍以下', 'ROE10%以上', '営業利益率5%以上'],
                'risks': ['バリュートラップ（割安な理由がある）', '業績回復の遅れ', '市場評価の長期低迷'],
                'tags': ['#割安株', '#バリュー投資', '#逆張り', '#財務分析']
            }
        ]
        
        return context

@login_required
def notebook_examples_ajax(request):
    """ノート作成例をAjaxで返す"""
    from django.http import JsonResponse
    
    style = request.GET.get('style', 'high_dividend')
    
    examples = {
        'high_dividend': {
            'title': '2025年 高配当株ポートフォリオ',
            'subtitle': '配当利回り3%以上の安定銘柄で資産形成',
            'description': 'インカムゲイン重視の長期投資戦略。配当の継続性と成長性を重視した銘柄選択を行います。',
            'investment_strategy': '配当利回り3%以上かつ配当性向70%以下の財務健全な企業を選定。四半期決算での業績確認と配当政策の変更点を継続監視し、減配リスクの高い銘柄は早めに入れ替えを行う。目標年間配当利回り4%以上。',
            'target_allocation': 'ポートフォリオの40%、月額投資額の50%',
            'key_criteria': ['配当利回り3%以上', '配当性向70%以下', '連続増配または安定配当', '自己資本比率40%以上', '営業CF安定'],
            'risk_factors': ['金利上昇による株価下落', '減配・無配転落リスク', '景気後退による業績悪化'],
            'suggested_tags': ['#高配当', '#配当株', '#長期投資', '#インカムゲイン'],
            'suggested_sub_notebooks': ['日本高配当株', '米国配当株', 'REITs', '配当貴族銘柄']
        },
        'growth': {
            'title': '成長株研究ラボ',
            'subtitle': '次世代を担う成長企業の発掘と分析',
            'description': '技術革新や市場拡大の恩恵を受ける企業への投資機会を追求します。',
            'investment_strategy': '売上成長率年20%以上、ROE15%以上の高成長企業を選定。PEGレシオ1.5倍以下で購入し、四半期決算での成長持続性を確認。競合優位性の源泉と市場シェア拡大の可能性を重視する。',
            'target_allocation': 'ポートフォリオの30%、リスク資金の範囲内',
            'key_criteria': ['売上成長率20%以上（3年平均）', 'ROE15%以上', 'PEGレシオ1.5倍以下', '競合優位性あり', '市場拡大性'],
            'risk_factors': ['成長率鈍化リスク', '高バリュエーション調整', '競合激化', '技術革新の遅れ'],
            'suggested_tags': ['#成長株', '#グロース投資', '#テクノロジー', '#イノベーション'],
            'suggested_sub_notebooks': ['AI・DX関連', 'バイオテック', 'クリーンエネルギー', '新興市場']
        }
    }
    
    return JsonResponse({
        'success': True,
        'example': examples.get(style, examples['high_dividend'])
    })