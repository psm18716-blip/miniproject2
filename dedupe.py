import pymysql

conn = pymysql.connect(
    host='127.0.0.1', port=3306,
    database='UsedCar', user='root',
    password='dltnals0920!', charset='utf8mb4'
)

with conn.cursor() as cur:
    # 유지할 id (그룹별 최솟값)
    cur.execute("""
        SELECT MIN(id)
        FROM cars
        GROUP BY manufacturer, model, badge, year, mileage, price
    """)
    keep_ids = {row[0] for row in cur.fetchall()}

    # 전체 id
    cur.execute("SELECT id FROM cars")
    all_ids = {row[0] for row in cur.fetchall()}

    delete_ids = list(all_ids - keep_ids)
    print(f"전체: {len(all_ids)}건 / 유지: {len(keep_ids)}건 / 삭제: {len(delete_ids)}건")

    if not delete_ids:
        print("중복 없음!")
    else:
        # 1000건씩 배치 삭제 (id 기준이라 빠름)
        batch_size = 1000
        for i in range(0, len(delete_ids), batch_size):
            batch = delete_ids[i:i + batch_size]
            placeholders = ','.join(['%s'] * len(batch))
            cur.execute(f"DELETE FROM cars WHERE id IN ({placeholders})", batch)
            conn.commit()
            print(f"삭제 중... {min(i + batch_size, len(delete_ids))}/{len(delete_ids)}")

        print("완료!")

conn.close()
