import time
from datetime import datetime
from typing import Dict, Any

from .utils import KST, now_str, cooldown_ok
from prepare.state_manager import save_positions
from api.order import send_order

def handle_tick(ctx: Dict[str, Any], code: str, price: float):
    """
    실시간 틱(체결)가 들어올 때 호출: 매수/익절/손절 판정 및 주문 실행
    ctx: {
      cfg, token, market_env, hts_id,
      take_profit, stop_loss, buy_qty,
      order_cooldown, last_order_ts (dict),
      state (dict)
    }
    """
    state = ctx["state"]
    if code not in state:
        return

    info = state[code]
    # 로그
    print(f"[{now_str()}] {code} {info['name']} 현재가: {price:.2f} / 목표가: {info['target_price']:.2f}")

    # 중복 주문 쿨다운
    if not cooldown_ok(ctx["last_order_ts"], code, ctx["order_cooldown"]):
        return

    # 이미 다른 종목 보유 중이면 매수 안 함(동시 보유 방지) -> 한 종목만 감시
    if any(v.get("bought") and not v.get("sold") for v in state.values()):
        # 그러나 보유 종목의 익절/손절 체크는 on_message에서 code별로 들어오므로 거기서 처리
        return

    # 목표가 돌파 → 매수
    if not info["bought"] and price >= info["target_price"]:
        print(f"목표가 돌파 → 시장가 매수 시도: {code} {info['name']} @ {price:.2f}")
        res = send_order(ctx["cfg"], ctx["token"], code, info["name"],
                         qty=ctx["buy_qty"], price = price, side="buy", market=ctx["market_env"])
        if str(res.get("rt_cd", "1")) == "0":
            info["bought"] = True
            info["buy_price"] = price
            info["buy_time"] = datetime.now(KST).isoformat()
            info["tp"] = round(price * (1 + ctx["take_profit"]), 2)
            info["sl"] = round(price * (1 - ctx["stop_loss"]), 2)
            print(f"매수 성공: {code} {info['name']} @ {price:.2f} | TP {info['tp']} / SL {info['sl']}")
            save_positions(state)
        else:
            print(f"매수 실패: {res.get('msg1', '')}")
        return

    # 익절 / 손절
    if info.get("bought") and not info.get("sold"):
        tp = info.get("tp")
        sl = info.get("sl")
        if tp is not None and price >= tp:
            print(f"익절 조건 충족 → 매도: {code} {info['name']} @ {price:.2f}")
            res = send_order(ctx["cfg"], ctx["token"], code, info["name"],
                             qty=info.get("qty", ctx["buy_qty"]), price=price, side="sell", market=ctx["market_env"])
            if str(res.get("rt_cd", "1")) == "0":
                info["sold"] = True
                info["sell_reason"] = "take_profit"
                info["sell_time"] = datetime.now(KST).isoformat()
                print(f"익절 완료: {code} {info['name']}")
                save_positions(state)
            return
        if sl is not None and price <= sl:
            print(f"손절 조건 충족 → 매도: {code} {info['name']} @ {price:.2f}")
            res = send_order(ctx["cfg"], ctx["token"], code, info["name"],
                             qty=info.get("qty", ctx["buy_qty"]), price=price, side="sell", market=ctx["market_env"])
            if str(res.get("rt_cd", "1")) == "0":
                info["sold"] = True
                info["sell_reason"] = "stop_loss"
                info["sell_time"] = datetime.now(KST).isoformat()
                print(f"손절 완료: {code} {info['name']}")
                save_positions(state)
            return

def market_close_guard_loop(ctx: Dict[str, Any]):
    """15:20 도달 시 미청산 포지션 자동 청산"""
    from prepare.state_manager import save_positions  # 순환 import 회피용
    while True:
        now = datetime.now(KST)
        if now.hour == 15 and now.minute >= 20:
            print("장마감 청산 루프 작동")
            for code, info in ctx["state"].items():
                if info.get("bought") and not info.get("sold"):
                    try:
                        print(f"장마감 청산 시도: {code} {info['name']}")
                        res = send_order(ctx["cfg"], ctx["token"], code, info["name"],
                                         qty=info.get("qty", ctx["buy_qty"]),
                                         price=0, side="sell", market=ctx["market_env"])
                        if str(res.get("rt_cd", "1")) == "0":
                            info["sold"] = True
                            info["sell_reason"] = "market_close"
                            info["sell_time"] = datetime.now(KST).isoformat()
                            print(f"장마감 청산 완료: {code} {info['name']}")
                            save_positions(ctx["state"])
                        else:
                            print(f"장마감 청산 실패: {code} {info['name']} / {res.get('msg1', '')}")
                    except Exception as e:
                        print(f"장마감 청산 오류: {code} {e}")
            break
        time.sleep(30)
