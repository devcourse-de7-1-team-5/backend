from django.core.management.base import BaseCommand
from todo.models import EpisodeInfo,Drama
from todo.tests.episodes_info_crawler import get_all_episode_info


class Command(BaseCommand):
    help = "드라마 회차별 정보 크롤링"

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("드라마 회차별 정보 크롤링!"))

        titles = list(Drama.objects.values_list('title', flat=True))
        
        for drama in Drama.objects.all():
            print("="*10 + drama.title + "="*10)
            episodes_list = get_all_episode_info(drama.title)
            
            if episodes_list == None: continue

            for episode in episodes_list:
                if all(value is None for value in episode.values()): continue

                print(f"{drama.title} {episode['episode_no']}회 저장중...")
                EpisodeInfo.objects.update_or_create(
                    drama=drama,                           # ← 인스턴스 전달
                    episode_no=episode["episode_no"],      # ← 조회(고유조합) 기준
                    defaults={                             # ← 나머지는 defaults로
                        "date": episode["date"],           # date는 date 객체 권장(문자열이면 변환)
                        "rating": episode["rating"],
                        "synopsis": episode.get("synopsis"),
                        "query": episode["query"],
                        "source_url": episode["source_url"],
    }
)
            


    