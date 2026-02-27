import time, threading

from api.auth import load_cfg, get_token

from prepare.candidate_manager import load_or_create_candidates
from prepare.state_manager import load_positions, initialize_state
from ws.websocket_loop import start_ws_loop
from ws.trade_logic import market_close_guard_loop

def main():
    print("[main.py] 실시간 자동매매 시스템 시작")

    # 1) 설정/토큰 로드
    cfg = load_cfg()
    token = get_token(cfg)

    # 파라미터
    TAKE_PROFIT = float(cfg["trading"].get("take_profit", 0.05))
    STOP_LOSS   = float(cfg["trading"].get("stop_loss", 0.03))
    BUY_QTY     = int(cfg["trading"].get("buy_qty", 2)) if "buy_qty" in cfg.get("trading",{}) else 5

    candidates = load_or_create_candidates(cfg, token, limit=959, top_n=20)

    prev_state = load_positions()
    state = initialize_state(candidates, buy_qty=BUY_QTY, prev_state=prev_state)
    print(f"감시 대상: {len(state)}종목")
    for k, v in state.items():
        print(f"  - {k} {v['name']} 목표가 {v['target_price']:.2f}")

    # 3) 공유 컨텍스트 구성 (클래스 없이 dict로 공유)
    ctx = {
        "cfg": cfg,
        "token": token,
        "market_env": "mock" if cfg.get("env","paper") in ("mock","paper") else "real",
        "take_profit": TAKE_PROFIT,
        "stop_loss": STOP_LOSS,
        "buy_qty": BUY_QTY,
        "order_cooldown": 1.0,
        "last_order_ts": {},  # code → last ts
        "state": state,
        "running": True,
    }

    # 4) 실행 (WS + 장마감 청산)
    t_ws = threading.Thread(target=start_ws_loop, args=(ctx,), daemon=True)
    t_mc = threading.Thread(target=market_close_guard_loop, args=(ctx,), daemon=True)
    t_ws.start()
    t_mc.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("사용자 종료 요청 — 종료 중...")
        ctx["running"] = False
        time.sleep(1)
        print("정상 종료 완료")

if __name__ == "__main__":
    main()
