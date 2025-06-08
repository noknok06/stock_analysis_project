from rest_framework import serializers
from apps.notes.models import Notebook, SubNotebook, Entry, EntryRelation
from apps.tags.serializers import TagSerializer

class SubNotebookSerializer(serializers.ModelSerializer):
    """サブノートブックシリアライザー"""
    
    class Meta:
        model = SubNotebook
        fields = [
            'id', 'title', 'description', 'order_index', 
            'entry_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'entry_count', 'created_at', 'updated_at']

class EntrySerializer(serializers.ModelSerializer):
    """エントリーシリアライザー"""
    
    tags = TagSerializer(many=True, read_only=True)
    sub_notebook = SubNotebookSerializer(read_only=True)
    notebook_title = serializers.CharField(source='notebook.title', read_only=True)
    display_name = serializers.CharField(read_only=True)
    
    class Meta:
        model = Entry
        fields = [
            'id', 'title', 'entry_type', 'stock_code', 'company_name', 
            'market', 'event_date', 'event_type', 'summary', 'content',
            'current_price', 'target_price', 'rating', 'importance',
            'is_bookmarked', 'tags', 'sub_notebook', 'notebook_title',
            'display_name', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'display_name', 'created_at', 'updated_at']
    
    def validate_stock_code(self, value):
        """銘柄コードのバリデーション"""
        if value and len(value) != 4:
            raise serializers.ValidationError("銘柄コードは4桁で入力してください")
        return value

class EntryCreateSerializer(serializers.ModelSerializer):
    """エントリー作成用シリアライザー"""
    
    tag_ids = serializers.ListField(
        child=serializers.UUIDField(),
        write_only=True,
        required=False
    )
    
    class Meta:
        model = Entry
        fields = [
            'title', 'entry_type', 'stock_code', 'company_name',
            'summary', 'content', 'importance', 'tag_ids'
        ]
    
    def create(self, validated_data):
        tag_ids = validated_data.pop('tag_ids', [])
        entry = super().create(validated_data)
        
        if tag_ids:
            entry.tags.set(tag_ids)
        
        return entry

class NotebookSerializer(serializers.ModelSerializer):
    """ノートブック一覧用シリアライザー"""
    
    tags = TagSerializer(many=True, read_only=True)
    entry_count = serializers.IntegerField(read_only=True)
    stock_count = serializers.IntegerField(read_only=True)
    sub_notebook_count = serializers.SerializerMethodField()
    recent_entries_count = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Notebook
        fields = [
            'id', 'title', 'subtitle', 'description', 'notebook_type',
            'status', 'objectives', 'key_themes', 'notes', 'tags',
            'entry_count', 'stock_count', 'sub_notebook_count',
            'recent_entries_count', 'last_entry_date', 'is_public',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'entry_count', 'stock_count', 'last_entry_date',
            'created_at', 'updated_at'
        ]
    
    def get_sub_notebook_count(self, obj):
        return obj.sub_notebooks.count()

class NotebookDetailSerializer(NotebookSerializer):
    """ノートブック詳細用シリアライザー"""
    
    sub_notebooks = SubNotebookSerializer(many=True, read_only=True)
    recent_entries = serializers.SerializerMethodField()
    stock_list = serializers.SerializerMethodField()
    
    class Meta(NotebookSerializer.Meta):
        fields = NotebookSerializer.Meta.fields + [
            'sub_notebooks', 'recent_entries', 'stock_list'
        ]
    
    def get_recent_entries(self, obj):
        recent = obj.get_recent_entries(5)
        return EntrySerializer(recent, many=True).data
    
    def get_stock_list(self, obj):
        return obj.get_stock_list()

class NotebookCreateSerializer(serializers.ModelSerializer):
    """ノートブック作成用シリアライザー"""
    
    tag_ids = serializers.ListField(
        child=serializers.UUIDField(),
        write_only=True,
        required=False
    )
    sub_notebooks_data = serializers.ListField(
        child=serializers.DictField(),
        write_only=True,
        required=False
    )
    
    class Meta:
        model = Notebook
        fields = [
            'title', 'subtitle', 'description', 'notebook_type',
            'status', 'objectives', 'key_themes', 'notes',
            'tag_ids', 'sub_notebooks_data'
        ]
    
    def create(self, validated_data):
        tag_ids = validated_data.pop('tag_ids', [])
        sub_notebooks_data = validated_data.pop('sub_notebooks_data', [])
        
        notebook = super().create(validated_data)
        
        # タグの設定
        if tag_ids:
            notebook.tags.set(tag_ids)
        
        # サブノートブックの作成
        for i, sub_data in enumerate(sub_notebooks_data):
            SubNotebook.objects.create(
                notebook=notebook,
                title=sub_data['title'],
                description=sub_data.get('description', ''),
                order_index=i + 1
            )
        
        return notebook

class EntryRelationSerializer(serializers.ModelSerializer):
    """エントリー関連シリアライザー"""
    
    from_entry_title = serializers.CharField(source='from_entry.title', read_only=True)
    to_entry_title = serializers.CharField(source='to_entry.title', read_only=True)
    
    class Meta:
        model = EntryRelation
        fields = [
            'id', 'from_entry', 'to_entry', 'relation_type', 'notes',
            'from_entry_title', 'to_entry_title', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']

class SearchSerializer(serializers.Serializer):
    """検索用シリアライザー"""
    
    query = serializers.CharField(max_length=200, required=False)
    notebook_type = serializers.ChoiceField(
        choices=Notebook.NOTEBOOK_TYPE_CHOICES,
        required=False
    )
    entry_type = serializers.ChoiceField(
        choices=Entry.ENTRY_TYPE_CHOICES,
        required=False
    )
    stock_code = serializers.CharField(max_length=10, required=False)
    date_from = serializers.DateField(required=False)
    date_to = serializers.DateField(required=False)
    bookmarked_only = serializers.BooleanField(required=False)
    limit = serializers.IntegerField(min_value=1, max_value=100, default=20)
