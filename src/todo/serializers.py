from rest_framework import serializers

from .models import Drama, ExternalIDMapping # ExternalIDMapping 모델을 임포트합니다.


class DramaListSerializer(serializers.ModelSerializer): # 'a' 제거됨
    class Meta:
        model = Drama
        # is_airing 필드 추가 (models.py에 정의되어 있음)
        fields = ['id', 'title', 'channel','start_date','end_date'] 

class DramaDetailSerializer(serializers.ModelSerializer): # 'a' 제거됨
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