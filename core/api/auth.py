import requests
import yaml

# config/info.yaml 파일을 읽어서 파이썬 dict로 반환
def load_cfg(path="../config/info.yaml"):
    try:
        with open(path, encoding="utf-8") as f:
            cfg = yaml.safe_load(f)
        return cfg
    except FileNotFoundError:
        raise Exception(f"파일을 찾을 수 없습니다: {path}")
    except yaml.YAMLError as e:
        raise Exception(f"YAML 구문 오류: {e}")

# REST API용 액세스 토큰 발급
def get_token(cfg):
    base = cfg["domain"][cfg["env"]]["rest"]
    url = f"{base}/oauth2/tokenP"
    body = {
        "grant_type": "client_credentials",
        "appkey": cfg["appkey"],
        "appsecret": cfg["appsecret"]
    }

    res = requests.post(url, json=body)
    if res.status_code != 200:
        raise Exception(f"토큰 발급 실패 [{res.status_code}]: {res.text}")

    data = res.json()
    if "access_token" not in data:
        raise Exception(f"응답에 access_token 없음: {data}")
    
    return data["access_token"]

# 웹소켓 접속용 승인키 발급
def get_approval(cfg):
    base = cfg["domain"][cfg["env"]]["rest"]
    url = f"{base}/oauth2/Approval"
    body = {
        "grant_type": "client_credentials",
        "appkey": cfg["appkey"],
        "secretkey": cfg["appsecret"]
    }

    res = requests.post(url, json=body)
    if res.status_code != 200:
        raise Exception(f"승인키 발급 실패 [{res.status_code}]: {res.text}")

    data = res.json()
    if "approval_key" not in data:
        raise Exception(f"응답에 approval_key 없음: {data}")

    return data["approval_key"]

"""""
# 단독 실행 코드
if __name__ == "__main__":
    print("[auth.py 테스트]")
    cfg = load_cfg()
    token = get_token(cfg)
    print("토큰:", token)
    approval = get_approval(cfg)
    print("승인키:", approval)
"""""
