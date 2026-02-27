# core/order.py
import requests
import json
import os
from datetime import datetime, timezone, timedelta

KST = timezone(timedelta(hours=9))

# 주문 로그
"""
    주문 로그 파일의 절대 경로 반환.
    (core/data/order_log.txt)
    폴더가 없으면 자동으로 생성.
"""
def _get_log_path():
    base_dir = os.path.dirname(os.path.abspath(__file__))   # api/
    core_dir = os.path.dirname(base_dir)                    # core/
    data_dir = os.path.join(core_dir, "data")               # core/data/
    os.makedirs(data_dir, exist_ok=True)
    return os.path.join(data_dir, "order_log.txt")

def log_order_result(action, code, name, qty, price, res):
    now = datetime.now(KST).strftime("%Y-%m-%d %H:%M:%S")
    rt_cd = res.get("rt_cd", "")
    msg = res.get("msg1", "")
    order_no = res.get("output", {}).get("ODNO", "N/A")
    
    if price == 0:
        log = f"[{now}] [{action}] {name}({code}) {qty}주 시장가 청산 → 결과: {rt_cd}, {msg}, 주문번호: {order_no}"
        print(log)
    else:    
        log = f"[{now}] [{action}] {name}({code}) {qty}주 {price}원 → 결과: {rt_cd}, {msg}, 주문번호: {order_no}"
        print(log)
    
    log_path = _get_log_path()
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(log + "\n")


# 주문
def send_order(cfg, token, code, name, qty, price, side="buy", market="mock"):
    """
    국내주식주문(현금) API
    - POST /uapi/domestic-stock/v1/trading/order-cash
    - 매수: VTTC0012U / TTTC0012U
    - 매도: VTTC0011U / TTTC0011U
    """

    # 기본 URL
    base_url = cfg["domain"][cfg["env"]]["rest"]
    url = f"{base_url}/uapi/domestic-stock/v1/trading/order-cash"

    # TR ID 설정
    if market == "mock":  # 모의투자
        tr_id = "VTTC0012U" if side == "buy" else "VTTC0011U"
    else:  # 실전
        tr_id = "TTTC0012U" if side == "buy" else "TTTC0011U"

    # 요청 헤더
    headers = {
        "content-type": "application/json; charset=UTF-8",
        "authorization": f"Bearer {token}",
        "appkey": cfg["appkey"],
        "appsecret": cfg["appsecret"],
        "tr_id": tr_id,
        "custtype": "P",  # 개인
    }

    # 요청 바디
    body = {
        "CANO": cfg["acc_no"],     # 종합계좌번호 앞 8자리
        "ACNT_PRDT_CD": "01",       # 계좌상품코드
        "PDNO": code,               # 종목코드
        "ORD_DVSN": "01",           # 시장가 (01), 지정가(00)
        "ORD_QTY": str(qty),        # 수량
        "ORD_UNPR": "0", # str(price) if price > 0 else  # 시장가면 0
        "SLL_TYPE": "01" if side == "sell" else "",    # 매도일 때만 일반매도
        "EXCG_ID_DVSN_CD": "KRX",   # 거래소 구분코드 (모의는 KRX 고정)
    }

    # 주문 전송
    try:
        res = requests.post(url, headers=headers, data=json.dumps(body))
        res_json = res.json()
        log_order_result("매수" if side == "buy" else "매도", code, name, qty, price, res_json)
        return res_json

    except Exception as e:
        print(f" 주문 요청 중 오류: {e}")
        return {"rt_cd": "1", "msg1": str(e)}


'''
# 단독 실행 코드
if __name__ == "__main__":
    from .auth import load_cfg, get_token

    print("[order.py 테스트]")
    cfg = load_cfg()
    token = get_token(cfg)

    # 예시: 삼성전자 1주 매수
    # res_buy = send_order(cfg, token, "005930", "삼성전자", qty=1, price=0, side="buy", market="mock")
    # print(json.dumps(res_buy, indent=2, ensure_ascii=False))

    # 예시: 삼성전자 1주 매도
    res_sell = send_order(cfg, token, "005930", "삼성전자", qty=1, price=0, side="sell", market="mock")
    print(json.dumps(res_sell, indent=2, ensure_ascii=False))
'''