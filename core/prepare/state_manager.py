import os, json
from typing import Dict, Any

# 항상 core/data 폴더 아래로 경로 고정
def _get_positions_path():
    """
    positions.json 파일의 절대 경로 반환
    (없으면 data 폴더를 자동 생성)
    """
    base_dir = os.path.dirname(os.path.abspath(__file__))         # ws/
    core_dir = os.path.dirname(base_dir)                          # core/
    data_dir = os.path.join(core_dir, "data")                     # core/data/
    os.makedirs(data_dir, exist_ok=True)
    return os.path.join(data_dir, "positions.json")


def save_positions(state: Dict[str, Dict[str, Any]]):
    """현재 포지션 상태를 data/positions.json에 저장"""
    path = _get_positions_path()
    with open(path, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)
    print(f"포지션 상태 저장 완료 → {path}")


def load_positions():
    """저장된 포지션 상태를 data/positions.json에서 로드"""
    path = _get_positions_path()
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    print(f"포지션 파일 없음 (새로 생성 예정) → {path}")
    return {}


def initialize_state(candidates, buy_qty=1, prev_state=None):
    """
    candidates: [{code, name, target_price}, ...]
    prev_state: 이전 저장된 포지션(state). 있으면 미체결 포지션 승계
    """
    prev_state = prev_state or {}
    new_state = {}

    for c in candidates:
        code = c["code"]
        name = c["name"]

        # 기존 미청산 포지션 유지
        if code in prev_state and prev_state[code].get("bought") and not prev_state[code].get("sold"):
            new_state[code] = prev_state[code]
            continue

        # 신규 포지션 생성
        new_state[code] = {
            "name": name,
            "target_price": float(c["target_price"]),
            "bought": False,
            "sold": False,
            "buy_price": None,
            "buy_time": None,
            "tp": None,
            "sl": None,
            "qty": buy_qty,
        }

    save_positions(new_state)
    return new_state
