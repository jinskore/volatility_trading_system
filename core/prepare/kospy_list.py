import csv
import os

# 코스피 종목 csv 파일에서 가져오기
def get_kospi_stock_list_from_csv():
    
    base_dir = os.path.dirname(os.path.abspath(__file__))   # prepare/
    core_dir = os.path.dirname(base_dir)                    # core/
    data_path = os.path.join(core_dir, "data", "kospi_data.csv")

    if not os.path.exists(data_path):
        raise FileNotFoundError(f"CSV 파일이 없습니다: {data_path}")

    stocks = []
    encodings = ["utf-8-sig", "utf-8", "euc-kr"]

    for enc in encodings:
        try:
            with open(data_path, "r", encoding=enc) as f:
                rdr = csv.reader(f)
                header = next(rdr, None)

                # 헤더 자동 감지
                if header and ("code" in header[0].lower() or "종목" in header[0]):
                    pass
                else:
                    f.seek(0)
                    rdr = csv.reader(f)

                for line in rdr:
                    if len(line) >= 2:
                        code = line[0].strip()
                        name = line[1].strip()

                        # ✅ 종목코드가 숫자로 저장되어 앞자리 0이 잘린 경우 보정
                        if code.isdigit() and len(code) < 6:
                            code = code.zfill(6)

                        if code and name:
                            stocks.append({"code": code, "name": name})
            print(f"CSV 인코딩 감지 성공: {enc}")
            break
        except UnicodeDecodeError:
            continue

    if not stocks:
        raise Exception("CSV 데이터를 읽지 못했습니다. 인코딩 또는 구분자(,) 확인하세요.")

    return stocks

"""
if __name__ == "__main__":
    print("[stock_list.py CSV 테스트]")
    stocks = get_kospi_stock_list_from_csv()
    print(f"KOSPI 종목 {len(stocks)}개 불러옴")
    for s in stocks[:959]:
        print(f"{s['code']} {s['name']}")
    print(len(stocks))
"""
