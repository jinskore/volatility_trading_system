import os, json
from api.screener import screen_candidates
from prepare.kospy_list import get_kospi_stock_list_from_csv

def load_or_create_candidates(cfg, token, limit=959, top_n=20):
    """
    후보 종목(candidates)을 불러오거나 새로 생성하는 함수.
    - 기존 candidates.json이 있으면 로드
    - 없으면 screener로 새 후보 생성 후 저장
    
    Args:
        cfg: 설정 정보
        token: API 토큰
        limit: 전체 종목 중 상위 몇 개만 검사할지
        top_n: 실제 감시할 후보 종목 개수

    Returns:
        list[dict]: 후보 종목 리스트
    """
    if os.path.exists("data/candidates.json"):
        with open("data/candidates.json", "r", encoding="utf-8") as f:
            candidates = json.load(f)
        print(f"기존 후보 불러옴 ({len(candidates)}개 종목)")
    else:
        print("신규 후보 생성 중...")
        all_stocks = get_kospi_stock_list_from_csv()
        candidates = screen_candidates(cfg, token, all_stocks[:limit], min_candidates = 5)
        os.makedirs("data", exist_ok=True)
        with open("data/candidates.json", "w", encoding="utf-8") as f:
            json.dump(candidates, f, ensure_ascii=False, indent=2)
        print(f"후보 저장 완료 ({len(candidates)}개)")

    if len(candidates) > top_n:
        candidates = candidates[:top_n]
    print(f"감시 대상 {len(candidates)}개 선택 완료")
    return candidates
