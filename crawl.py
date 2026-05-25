import requests
import pymysql
import time

# MySQL 접속 정보
DB_CONFIG = {
    "host": "127.0.0.1",
    "port": 3306,
    "database": "UsedCar",
    "user": "root",
    "password": "dltnals0920!",
    "charset": "utf8mb4",
}

# 엔카 서버가 봇 차단을 하기 때문에 브라우저처럼 보이게 User-Agent 설정
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36"
}

BASE_URL = "https://api.encar.com/search/car/list/general"
PHOTO_BASE = "https://ci.encar.com"  # 엔카 이미지 CDN 주소
PAGE_SIZE = 100  # 한 번 요청에 가져올 매물 수


def fetch_cars(car_type_flag: str, offset: int, retries: int = 5) -> dict:
    # CarType.Y = 국산, CarType.N = 수입
    q = f"(And.Hidden.N._.CarType.{car_type_flag}.)"
    # sr 파라미터: |정렬기준|시작위치|개수 형식
    sr = f"|ModifiedDate|{offset}|{PAGE_SIZE}"
    params = {"count": "true", "q": q, "sr": sr}

    # 서버가 끊기거나 오류 날 때를 대비해 최대 5번 재시도
    for attempt in range(retries):
        try:
            resp = requests.get(BASE_URL, params=params, headers=HEADERS, timeout=15)
            resp.raise_for_status()  # 4xx, 5xx 응답이면 예외 발생
            return resp.json()
        except Exception as e:
            wait = 5 * (attempt + 1)  # 실패할수록 대기 시간 늘림 (5초, 10초, 15초...)
            print(f"  재시도 {attempt+1}/{retries} (offset={offset}), {wait}초 대기... ({e})")
            time.sleep(wait)
    raise Exception(f"offset={offset} 최대 재시도 초과")


def get_photo_url(car: dict) -> str:
    photos = car.get("Photos", [])
    # type이 "001"인 게 대표 사진
    for photo in photos:
        if photo.get("type") == "001":
            return PHOTO_BASE + photo.get("location", "")
    # 대표 사진이 없으면 첫 번째 사진 사용
    if photos:
        return PHOTO_BASE + photos[0].get("location", "")
    return None


def save_cars(conn, rows: list, car_type: str):
    # INSERT IGNORE: 같은 id가 이미 있으면 에러 없이 그냥 건너뜀
    sql = """
        INSERT IGNORE INTO cars
            (id, car_type, manufacturer, model, badge, fuel_type, year, mileage, price, region, photo_url)
        VALUES
            (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    with conn.cursor() as cur:
        for car in rows:
            year_raw = car.get("Year")
            # API에서 연식이 202402.0 형태로 오기 때문에 앞 4자리만 추출
            year = int(str(year_raw)[:4]) if year_raw else None
            cur.execute(sql, (
                car.get("Id"),
                car_type,
                car.get("Manufacturer"),
                car.get("Model"),
                car.get("Badge"),
                car.get("FuelType"),
                year,
                int(car.get("Mileage", 0)),
                int(car.get("Price", 0)),
                car.get("OfficeCityState"),
                get_photo_url(car),
            ))
    conn.commit()  # 100건 모아서 한 번에 커밋 (속도 향상)


def crawl(car_type_flag: str, car_type_label: str, conn, max_count: int = 200000):
    offset = 0
    total_saved = 0

    print(f"\n[{car_type_label}] 크롤링 시작")
    while offset < max_count:
        try:
            data = fetch_cars(car_type_flag, offset)
        except Exception as e:
            print(f"  요청 실패 (offset={offset}): {e}")
            break

        results = data.get("SearchResults", [])
        # 결과가 없으면 마지막 페이지에 도달한 것
        if not results:
            break

        save_cars(conn, results, car_type_label)
        total_saved += len(results)
        print(f"  offset={offset} | 저장 {len(results)}건 (누적 {total_saved}건)")

        offset += PAGE_SIZE
        time.sleep(1.0)  # 너무 빠르게 요청하면 서버가 IP 차단하므로 1초 대기

    print(f"[{car_type_label}] 완료 — 총 {total_saved}건 저장")


def main():
    conn = pymysql.connect(**DB_CONFIG)
    try:
        crawl("Y", "국산", conn)
        crawl("N", "수입", conn)
    finally:
        conn.close()  # 에러가 나도 반드시 DB 연결 닫기
    print("\n전체 완료")


# 이 파일을 직접 실행할 때만 main() 호출 (다른 파일에서 import하면 실행 안 됨)
if __name__ == "__main__":
    main()
