# core/screener.py
import os
import time
import statistics
import json
from api.auth import load_cfg, get_token
from api.ohlcv import fetch_daily_ohlcv
from prepare.kospy_list import get_kospi_stock_list_from_csv

# 후보 종목 조회
def screen_candidates(cfg, token, stock_list, min_candidates = 5):
    """
    조건1, 조건2를 모두 만족하는 후보 종목 필터링
    """
    candidates = []
    total = len(stock_list)

    for i, stock in enumerate(stock_list, start=1):
        code = stock["code"]
        name = stock["name"]

        try:
            data = fetch_daily_ohlcv(cfg, token, code)
            if len(data) < 10:
                continue
            
            # 최근 20일 + 전일 데이터 분리
            prev_day = data[0]
            past_20 = data[1:21]
            
            print(name)
            print("전일고가 : " + prev_day["stck_hgpr"])
            print("전일저가 : " + prev_day["stck_lwpr"])
            print("전일거래량 : " + prev_day["acml_vol"])
            
            # 변동성 계산
            prev_vol = float(prev_day["stck_hgpr"]) - float(prev_day["stck_lwpr"])
            avg_vol = statistics.mean([
                float(d["stck_hgpr"]) - float(d["stck_lwpr"]) for d in past_20
            ])
            
            
            # 거래량 계산
            prev_volm = float(prev_day["acml_vol"])
            avg_volm = statistics.mean([float(d["acml_vol"]) for d in past_20])
            
            # 목표값 계산
            k = cfg["trading"]["k"]
            target_price = float(prev_day["stck_clpr"]) + (float(prev_day["stck_hgpr"]) - float(prev_day["stck_lwpr"])) * k
            
            print("20일 평균 거래량 : " + str(avg_volm))

            # 조건 확인
            cond1 = prev_vol < avg_vol * 0.6
            cond2 = prev_volm < avg_volm

            if cond1 and cond2:
                candidates.append({
                    "code": code,
                    "name": name,
                    "prev_vol": prev_vol,
                    "avg_vol": avg_vol,
                    "prev_volm": prev_volm,
                    "avg_volm": avg_volm,
                    "target_price": target_price
                })
                

        except Exception as e:
            print(f"[{i}/{total}] {name}({code}) 오류: {e}")
            continue

        if i % 10 == 0:
            print(f"{i}/{total}개 진행 중... 후보 {len(candidates)}개 발견")

        time.sleep(0.2)  # API 요청 제한 방지용 대기
        
    if len(candidates) < min_candidates:
        print(f"\n 후보가 너무 적습니다 ({len(candidates)}개). 조건2만 적용하여 재검색\n")
        relaxed = []
        for stock in stock_list:
            try:
                data = fetch_daily_ohlcv(cfg, token, stock["code"])
                if len(data) < 10:
                    continue

                prev_day = data[0]
                past_20 = data[1:21]

                prev_vol = float(prev_day["stck_hgpr"]) - float(prev_day["stck_lwpr"])
                avg_vol = statistics.mean([
                    float(d["stck_hgpr"]) - float(d["stck_lwpr"]) for d in past_20
                ])
                prev_volm = float(prev_day["acml_vol"])
                avg_volm = statistics.mean([float(d["acml_vol"]) for d in past_20])

                cond2 = prev_volm < avg_volm
                if cond2:
                    k = cfg["trading"]["k"]
                    target_price = float(prev_day["stck_clpr"]) + \
                        (float(prev_day["stck_hgpr"]) - float(prev_day["stck_lwpr"])) * k

                    relaxed.append({
                        "code": stock["code"],
                        "name": stock["name"],
                        "target_price": target_price,
                        "prev_vol": prev_vol,
                        "avg_vol": avg_vol,
                        "prev_volm": prev_volm,
                        "avg_volm": avg_volm
                    })
            except Exception as e:
                print(f"[완화 조건 오류] {stock['name']}({stock['code']}) → {e}")
                continue
            time.sleep(0.2)

        candidates = relaxed

    return candidates        



if __name__ == "__main__":
    print("[screener.py 단독 실행 테스트]")
    # start_all = time.time()
    cfg = load_cfg()
    token = get_token(cfg)
    all_stocks = get_kospi_stock_list_from_csv()

    print(f"총 {len(all_stocks)}개 KOSPI 종목 로드 완료!")
    candidates = screen_candidates(cfg, token, all_stocks[:959], min_candidates=5)  # 처음엔 50개만 테스트
    
    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(os.path.dirname(base_dir), "data")
    os.makedirs(data_dir, exist_ok=True)

    output_path = os.path.join(data_dir, "candidates.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(candidates, f, ensure_ascii=False, indent=2)

    print(f"\n최종 후보 종목 {len(candidates)}개 발견!")
    for c in candidates[:]:
        print(f"{c['code']} {c['name']} / 변동성:{c['prev_vol']:.2f} / 거래량:{c['prev_volm']:.0f}")
        
    # elapsed = time.time() - start_all
    # print(f"\n🕒 전체 실행 시간: {elapsed:.2f}초")
