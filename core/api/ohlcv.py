import requests
from api.auth import load_cfg, get_token
from datetime import datetime, timedelta

"""
전일 고가 output2 : stck_hgpr
전일 저가 output2 : stck_lwpr
전일 거래량 output2 : acml_vol
최근 20일 평균 거래량 FID_INPUT_DATE_1 : 시작일자 ~ FID_INPUT_DATE_2 : 조회 종료일자 로 20일 정보 가져와서 평균내기
최근 (고가 - 저가) 평균
"""

# 특정 종목(code)의 최근 21일치 일봉 데이터를 수집
def fetch_daily_ohlcv(cfg, token, code):
    base = cfg["domain"][cfg["env"]]["rest"]
    url = f"{base}/uapi/domestic-stock/v1/quotations/inquire-daily-itemchartprice"
    tr_id = "FHKST03010100"  # (일/주/월/년 시세조회용 TR ID)
    
    headers = {
        "Content-Type": "application/json",
        "authorization": f"Bearer {token}",
        "appKey": cfg["appkey"],
        "appSecret": cfg["appsecret"],
        "tr_id": tr_id
    }
    
    
    today = datetime.now().date()
    end_date = today - timedelta(days=1)      # 하루 전
    start_date = end_date - timedelta(days=21) # 21일 전
    
    params = {
    "FID_COND_MRKT_DIV_CODE": "J",   # 주식시장 (KRX)
    "FID_INPUT_ISCD": code,          # 종목코드, 예: 005930
    "FID_INPUT_DATE_1": start_date.strftime("%Y%m%d"),  # 조회 시작일자 (YYYYMMDD)
    "FID_INPUT_DATE_2": end_date.strftime("%Y%m%d"),  # 조회 종료일자 (오늘 기준 20~30일치)
    "FID_PERIOD_DIV_CODE": "D",      # D = 일봉
    "FID_ORG_ADJ_PRC": "1"           # 수정주가 반영
    }


    res = requests.get(url, headers=headers, params=params)
    if res.status_code != 200:
        raise Exception(f"시세 조회 실패: {res.status_code} / {res.text}")
    
    data = res.json()
    if "output2" not in data:
        raise Exception(f"응답 데이터 이상: {data}")
    
    # 최근 21일만 가져오기
    ohlcv = data["output2"][:21]
    return ohlcv

"""
# 단독 실행 코드
if __name__ == "__main__":
    print("ohlcv.py 테스트")
    cfg = load_cfg()
    token = get_token(cfg)
    data = fetch_daily_ohlcv(cfg, token, "005930")  # 삼성전자
    print(f"{len(data)}개 데이터 수집 완료!")
    for d in data[:3]:  # 최근 3일만 출력
        print(
            f"날짜:{d['stck_bsop_date']}, "
            f"고가:{d['stck_hgpr']}, 저가:{d['stck_lwpr']}, "
            f"종가:{d['stck_clpr']}, 거래량:{d['acml_vol']}"
        )
"""
