import json
import time
import websocket

from api.auth import get_approval
from .utils import now_str, parse_h0stcnt0
from .trade_logic import handle_tick

def start_ws_loop(ctx):
    """
    자동 재연결 + 종료 신호 대응
    ctx: {
      cfg, token, state, hts_id, market_env,
      take_profit, stop_loss, buy_qty,
      last_order_ts (dict), order_cooldown (float),
      running (bool)
    }
    """

    def on_open(ws):
        print("WebSocket 연결 성공")
        # 종목별 체결가 구독
        approval = ctx.get("approval_key")
        for code in ctx["state"].keys():
            data = {
                "header": {
                    "approval_key": approval,
                    "custtype": "P",
                    "tr_type": "1",
                    "content-type": "utf-8",
                },
                "body": {"input": {"tr_id": "H0STCNT0", "tr_key": code}},
            }
            ws.send(json.dumps(data))
            print(f"체결가 구독 요청: {code}")
            time.sleep(0.15)


    def on_message(ws, message):
        try:
            # JSON 응답 처리 (구독 성공 알림 등)
            # print(message)
            if message.startswith("{"):
                data = json.loads(message)
                body = data.get("body", {})
                header = data.get("header", {})
                msg = body.get("msg1", "")
                if msg == "SUBSCRIBE SUCCESS":
                    print(f"구독 성공: {header.get('tr_key')}")
                return
            
            
            evt = parse_h0stcnt0(message)
            if not evt:
                return
            
        
            code = evt["code"]
            price = evt["price"]
            handle_tick(ctx, code, price)

        except Exception as e:
            print(f"메시지 처리 오류: {e}")

    def on_error(ws, error):
        print(f"WebSocket 오류 발생: {error}")

    def on_close(ws, code, reason):
        print(f"WebSocket 연결 종료 (code={code}, reason={reason})")

    # === 루프 ===
    while ctx["running"]:
        try:
            ctx["approval_key"] = get_approval(ctx["cfg"])
            ws_url = ctx["cfg"]["domain"][ctx["cfg"]["env"]]["ws"]

            WS = websocket.WebSocketApp(
                ws_url,
                on_open=on_open,
                on_message=on_message,
                on_error=on_error,
                on_close=on_close,
            )

            print(f"[{now_str()}] WebSocket 연결 시도 중...")
            WS.run_forever(ping_interval=30, ping_timeout=10)

        except Exception as e:
            print(f"[{now_str()}] WebSocket 예외 발생: {e}")

        if not ctx["running"]:
            print("종료 신호 감지 — WebSocket 루프 종료")
            break

        print(f"[{now_str()}] 5초 후 WebSocket 재연결 시도...")
        time.sleep(5)
