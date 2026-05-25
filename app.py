from flask import Flask, render_template, request
import pymysql

app = Flask(__name__)

# DB 연결 함수
def get_db():
    return pymysql.connect(
        host='127.0.0.1',
        port=3306,
        database='UsedCar',
        user='root',
        password='dltnals0920!',
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor  # 결과를 딕셔너리로 받음
    )

@app.route('/')
def index():
    car_type = request.args.get('car_type', '')

    conn = get_db()
    with conn.cursor() as cur:
        if car_type:
            cur.execute("""
                SELECT manufacturer, COUNT(*) as count
                FROM cars
                WHERE car_type = %s
                GROUP BY manufacturer
                ORDER BY count DESC
            """, (car_type,))
        else:
            cur.execute("""
                SELECT manufacturer, COUNT(*) as count
                FROM cars
                GROUP BY manufacturer
                ORDER BY count DESC
            """)
        brands = cur.fetchall()
    conn.close()

    return render_template('index.html', brands=brands, car_type=car_type)




@app.route('/list')
def car_list():
    manufacturer  = request.args.get('manufacturer', '')
    fuel_type     = request.args.get('fuel_type', '')
    year_min      = request.args.get('year_min', '')
    year_max      = request.args.get('year_max', '')
    price_min     = request.args.get('price_min', '')
    price_max     = request.args.get('price_max', '')
    mileage_min   = request.args.get('mileage_min', '')
    mileage_max   = request.args.get('mileage_max', '')
    q             = request.args.get('q', '')      # 모델명·브랜드 통합 검색
    favs          = request.args.get('favs', '')   # 찜한 차 ID 목록 (콤마 구분)
    page          = int(request.args.get('page', 1))
    per_page      = 60
    offset        = (page - 1) * per_page

    # 찜한 차 모드: 특정 ID 목록만 조회 (다른 필터 무시)
    if favs:
        fav_ids = [fid.strip() for fid in favs.split(',') if fid.strip()]
        if fav_ids:
            placeholders = ','.join(['%s'] * len(fav_ids))
            conditions = [f'id IN ({placeholders})']
            params = list(fav_ids)
        else:
            conditions = ['1=0']
            params = []
    else:
        conditions = ['price > 50']
        params = []

        if manufacturer:
            conditions.append('manufacturer = %s');  params.append(manufacturer)
        if fuel_type:
            conditions.append('fuel_type = %s');     params.append(fuel_type)
        if year_min:
            conditions.append('year >= %s');         params.append(year_min)
        if year_max:
            conditions.append('year <= %s');         params.append(year_max)
        if price_min:
            conditions.append('price >= %s');        params.append(price_min)
        if price_max:
            conditions.append('price <= %s');        params.append(price_max)
        if mileage_min:
            conditions.append('mileage >= %s');      params.append(mileage_min)
        if mileage_max:
            conditions.append('mileage <= %s');      params.append(mileage_max)
        if q:
            # 브랜드명, 모델명, 배지(세부모델) 모두 포함 검색
            conditions.append('(manufacturer LIKE %s OR model LIKE %s OR badge LIKE %s)')
            like_q = f'%{q}%'
            params.extend([like_q, like_q, like_q])

    where = 'WHERE ' + ' AND '.join(conditions)

    conn = get_db()
    with conn.cursor() as cur:
        cur.execute("""
            SELECT manufacturer, COUNT(*) as count
            FROM cars
            GROUP BY manufacturer
            ORDER BY count DESC
        """)
        brands = cur.fetchall()

        cur.execute(f'SELECT COUNT(*) as total FROM cars {where}', params)
        total = cur.fetchone()['total']

        cur.execute(f"""
            SELECT id, manufacturer, model, badge, fuel_type, year, mileage, price, region, photo_url
            FROM cars {where}
            ORDER BY price ASC
            LIMIT %s OFFSET %s
        """, params + [per_page, offset])
        cars = cur.fetchall()
    conn.close()

    total_pages = (total + per_page - 1) // per_page

    return render_template('list.html', cars=cars, brands=brands,
                           manufacturer=manufacturer, total=total,
                           page=page, total_pages=total_pages,
                           fuel_type=fuel_type, year_min=year_min, year_max=year_max,
                           price_min=price_min, price_max=price_max,
                           mileage_min=mileage_min, mileage_max=mileage_max,
                           q=q, favs=favs)



@app.route('/car/<car_id>')
def car_detail(car_id):
    conn = get_db()
    with conn.cursor() as cur:
        cur.execute("""
            SELECT * FROM cars WHERE id = %s
            """, (car_id,))
        car = cur.fetchone()

        # 같은 모델의 연식별 평균 가격 (차트용)
        cur.execute("""
            SELECT year, ROUND(AVG(price)) as avg_price
            FROM cars
            WHERE model = %s AND price > 0
            GROUP BY year
            ORDER BY year
            """, (car['model'],))
        chart_data = cur.fetchall()
    conn.close()

    return render_template('detail.html', car=car, chart_data=chart_data)

if __name__ == '__main__':
    app.run(debug=True)