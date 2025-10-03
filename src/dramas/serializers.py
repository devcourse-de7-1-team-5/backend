from rest_framework import serializers

from dramas.models import Drama, EpisodeInfo # ExternalIDMapping 모델을 임포트합니다.

class EpisodeInfoSerializer(serializers.ModelSerializer):
    # ForeignKey로 연결된 Drama 모델을 어떻게 보여줄지 선택 가능
    # 기본적으로는 drama의 id가 표시됨
    # 만약 Drama의 특정 필드를 같이 보고 싶다면 StringRelatedField()나 SlugRelatedField() 사용 가능
    drama = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = EpisodeInfo
        fields = [
            'id',
            'drama',
            'episode_no',
            'date',
            'rating',
            'synopsis',
            'query',
            'source_url',
        ]

class DramaListSerializer(serializers.ModelSerializer): # 'a' 제거됨
    class Meta:
        model = Drama
        # is_airing 필드 추가 (models.py에 정의되어 있음)
        fields = ['id', 'title', 'channel','start_date','end_date'] 

class DramaDetailSerializer(serializers.ModelSerializer): # 'a' 제거됨
    episodes = EpisodeInfoSerializer(source='episodeinfo_set', many=True, read_only=True)

    # 상세 정보에서 외부 ID를 보여주기 위한 필드
    external_ids = serializers.SerializerMethodField()
    
    class Meta:
        model = Drama
        fields = '__all__' # 모든 필드 (줄거리 포함)

    # external_ids 필드에 데이터를 채우는 메서드
    def get_external_ids(self, obj):
        # Drama 객체(obj)에 연결된 ExternalIDMapping 객체들을 가져옵니다.
        mappings = obj.externalidmapping_set.all()
        return [{
            'source': mapping.source_name,
            'external_id': mapping.external_id
        } for mapping in mappings]
    

