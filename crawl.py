import requests
import pymysql
import time

DB_CONFIG = {
    "host": "127.0.0.1",
    "port": 3306,
    "db": "UsedCar",
    "user": "root",
    "password": "dltnals0920!",
    "charset": "utf8mb4",
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36"
}

BASE_URL = "https://api.encar.com/search/car/list/general"
PAGE_SIZE = 100


def fetch_cars(car_type_flag: str, offset: int) -> dict:
    q = f"(And.Hidden.N._.CarType.{car_type_flag}.)"
    sr = f"|ModifiedDate|{offset}|{PAGE_SIZE}"
    params = {"count": "true", "q": q, "sr": sr}
    resp = requests.get(BASE_URL, params=params, headers=HEADERS, timeout=10)
    resp.raise_for_status()
    return resp.json()


def save_cars(conn, rows: list, car_type: str):
    sql = """
        INSERT IGNORE INTO cars
            (id, car_type, manufacturer, model, badge, fuel_type, year, mileage, price, region)
        VALUES
            (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    with conn.cursor() as cur:
        for car in rows:
            year_raw = car.get("Year")
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
            ))
    conn.commit()


def crawl(car_type_flag: str, car_type_label: str, conn, max_count: int = 5000):
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
        if not results:
            break

        save_cars(conn, results, car_type_label)
        total_saved += len(results)
        print(f"  offset={offset} | 저장 {len(results)}건 (누적 {total_saved}건)")

        offset += PAGE_SIZE
        time.sleep(0.5)

    print(f"[{car_type_label}] 완료 — 총 {total_saved}건 저장")


def main():
    conn = pymysql.connect(**DB_CONFIG)
    try:
        crawl("Y", "국산", conn, max_count=5000)
        crawl("N", "수입", conn, max_count=5000)
    finally:
        conn.close()
    print("\n전체 완료")


if __name__ == "__main__":
    main()
