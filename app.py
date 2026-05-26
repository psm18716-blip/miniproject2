from flask import Flask, render_template, request
import pymysql
import joblib
import numpy as np
import pandas as pd

app = Flask(__name__)


ml_model    = joblib.load('model.pkl')
ml_encoders = joblib.load('encoders.pkl')

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
    region        = request.args.get('region', '')
    q             = request.args.get('q', '')
    favs          = request.args.get('favs', '')
    sort          = request.args.get('sort', 'price_asc')
    page          = int(request.args.get('page', 1))
    per_page      = 60
    offset        = (page - 1) * per_page

    sort_map = {
        'price_asc':   'price ASC',
        'price_desc':  'price DESC',
        'year_desc':   'year DESC, price ASC',
        'mileage_asc': 'mileage ASC',
    }
    order_by = sort_map.get(sort, 'price ASC')

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
        conditions = ['price > 50', 'price NOT IN (9990, 9999)', 'price < 99000']
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
        if region:
            conditions.append('region = %s');        params.append(region)
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
            ORDER BY {order_by}
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
                           q=q, favs=favs, sort=sort, region=region)



@app.route('/analysis')
def analysis():
    conn = get_db()
    with conn.cursor() as cur:
        # 브랜드별 평균 시세 + 매물 수 (상위 10개)
        cur.execute("""
            SELECT manufacturer, ROUND(AVG(price)) as avg_price, COUNT(*) as cnt
            FROM cars WHERE price > 50 AND price NOT IN (9990, 9999) AND price < 99000
            GROUP BY manufacturer ORDER BY cnt DESC LIMIT 10
        """)
        brand_stats = cur.fetchall()

        # 연식별 전체 평균 시세 (2010년 이후)
        cur.execute("""
            SELECT year, ROUND(AVG(price)) as avg_price, COUNT(*) as cnt
            FROM cars WHERE price > 50 AND price NOT IN (9990, 9999) AND price < 99000 AND year >= 2010
            GROUP BY year ORDER BY year
        """)
        year_stats = cur.fetchall()

        # 연료 타입별 매물 수
        cur.execute("""
            SELECT fuel_type, COUNT(*) as cnt
            FROM cars WHERE price > 50 AND price NOT IN (9990, 9999) AND price < 99000 AND fuel_type IS NOT NULL
            GROUP BY fuel_type ORDER BY cnt DESC
        """)
        fuel_stats = cur.fetchall()

        # 가격대별 분포
        cur.execute("""
            SELECT
                CASE
                    WHEN price < 500  THEN '500만 미만'
                    WHEN price < 1000 THEN '500~1000만'
                    WHEN price < 2000 THEN '1000~2000만'
                    WHEN price < 3000 THEN '2000~3000만'
                    WHEN price < 5000 THEN '3000~5000만'
                    ELSE '5000만 이상'
                END as label,
                COUNT(*) as cnt,
                MIN(price) as min_p
            FROM cars WHERE price > 50 AND price NOT IN (9990, 9999) AND price < 99000
            GROUP BY label ORDER BY min_p
        """)
        price_dist = cur.fetchall()

        # 국산 vs 수입 요약
        cur.execute("""
            SELECT car_type, ROUND(AVG(price)) as avg_price, COUNT(*) as cnt
            FROM cars WHERE price > 50 AND price NOT IN (9990, 9999) AND price < 99000
            GROUP BY car_type
        """)
        type_stats = cur.fetchall()

        # 전체 요약 통계
        cur.execute("""
            SELECT COUNT(*) as total, ROUND(AVG(price)) as avg_price,
                   MIN(price) as min_price, MAX(price) as max_price
            FROM cars WHERE price > 50 AND price NOT IN (9990, 9999) AND price < 99000
        """)
        summary = cur.fetchone()
    conn.close()

    return render_template('analysis.html',
                           brand_stats=brand_stats, year_stats=year_stats,
                           fuel_stats=fuel_stats, price_dist=price_dist,
                           type_stats=type_stats, summary=summary)


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
            WHERE model = %s AND price > 50 AND price NOT IN (9990, 9999) AND price < 99000
            GROUP BY year
            ORDER BY year
            """, (car['model'],))
        chart_data = cur.fetchall()
    conn.close()

    # AI 예측 시세
    ai_price = None
    try:
        mfr_enc   = ml_encoders['manufacturer'].transform([car['manufacturer']])[0]
        mdl_enc   = ml_encoders['model'].transform([car['model']])[0]
        fuel_enc  = ml_encoders['fuel_type'].transform([car['fuel_type'] or '기타'])[0]
        badge_val = str(car['badge']) if car['badge'] else 'None'
        badge_enc = ml_encoders['badge'].transform([badge_val])[0]
        X = pd.DataFrame([[mfr_enc, mdl_enc, fuel_enc, car['year'], car['mileage'], badge_enc]],
                          columns=['manufacturer', 'model', 'fuel_type', 'year', 'mileage', 'badge'])
        ai_price = int(np.expm1(ml_model.predict(X)[0]))
    except Exception:
        pass

    return render_template('detail.html', car=car, chart_data=chart_data, ai_price=ai_price)

@app.route('/api/models')
def api_models():
    from flask import jsonify
    manufacturer = request.args.get('manufacturer', '')
    conn = get_db()
    with conn.cursor() as cur:
        cur.execute("""
            SELECT DISTINCT model FROM cars
            WHERE manufacturer = %s
            ORDER BY model
        """, (manufacturer,))
        models = [r['model'] for r in cur.fetchall()]
    conn.close()
    return jsonify(models)


@app.route('/api/badges')
def api_badges():
    from flask import jsonify
    manufacturer = request.args.get('manufacturer', '')
    model        = request.args.get('model', '')
    conn = get_db()
    with conn.cursor() as cur:
        cur.execute("""
            SELECT DISTINCT badge FROM cars
            WHERE manufacturer = %s AND model = %s AND badge IS NOT NULL
            ORDER BY badge
        """, (manufacturer, model))
        badges = [r['badge'] for r in cur.fetchall()]
    conn.close()
    return jsonify(badges)


@app.route('/predict', methods=['GET', 'POST'])
def predict():
    conn = get_db()
    with conn.cursor() as cur:
        cur.execute("SELECT DISTINCT manufacturer FROM cars ORDER BY manufacturer")
        manufacturers = [r['manufacturer'] for r in cur.fetchall()]
        
        cur.execute("SELECT DISTINCT fuel_type FROM cars WHERE fuel_type IS NOT NULL ORDER BY fuel_type")
        fuel_types = [r['fuel_type'] for r in cur.fetchall()]
    conn.close()

    result = None  # 아직 예측 전

    if request.method == 'POST':
        manufacturer = request.form.get('manufacturer')
        model_name   = request.form.get('model')
        badge        = request.form.get('badge')
        fuel_type    = request.form.get('fuel_type')
        print(f"[DEBUG] mfr={manufacturer}, model={model_name}, badge={badge}, fuel={fuel_type}")
        year         = int(request.form.get('year'))
        mileage      = int(request.form.get('mileage'))

        try:
            mfr_enc   = ml_encoders['manufacturer'].transform([manufacturer])[0]
            mdl_enc   = ml_encoders['model'].transform([model_name])[0]
            badge_enc = ml_encoders['badge'].transform([badge])[0]
            fuel_enc  = ml_encoders['fuel_type'].transform([fuel_type])[0]

            X = pd.DataFrame([[mfr_enc, mdl_enc, fuel_enc, year, mileage, badge_enc]],
                              columns=['manufacturer', 'model', 'fuel_type', 'year', 'mileage', 'badge'])
            pred_log   = ml_model.predict(X)[0]
            pred_price = int(np.expm1(pred_log)) # 학습 때 log 변환 > 예측값도 역변환

            # DB에서 같은 모델의 실제 평균 시세 조회 (비교용)
            conn2 = get_db()
            with conn2.cursor() as cur:
                cur.execute("""
                    SELECT ROUND(AVG(price)) as avg_price, COUNT(*) as cnt
                    FROM cars
                    WHERE manufacturer = %s AND model = %s AND badge = %s
                      AND price > 50 AND price NOT IN (9990, 9999) AND price < 99000
                """, (manufacturer, model_name, badge))
                db_stat = cur.fetchone()
            conn2.close()

            result = {
                'price':     pred_price,
                'avg_price': int(db_stat['avg_price']) if db_stat['avg_price'] else None,
                'cnt':       db_stat['cnt'],
            }

        except (ValueError, KeyError) as e:
            print(f"[DEBUG] 예측 오류: {e}")
            result = {'error': f'예측 실패: {e}'}

    return render_template('predict.html',
                           manufacturers=manufacturers,
                           fuel_types=fuel_types,
                           result=result)


@app.route('/api/region-stats')
def api_region_stats():
    from flask import jsonify
    manufacturer = request.args.get('manufacturer', '')
    model        = request.args.get('model', '')
    conn = get_db()
    with conn.cursor() as cur:
        if manufacturer and model:
            cur.execute("""
                SELECT region, COUNT(*) as cnt, ROUND(AVG(price)) as avg_price
                FROM cars
                WHERE region IS NOT NULL
                  AND manufacturer = %s AND model = %s
                  AND price > 50 AND price NOT IN (9990, 9999) AND price < 99000
                GROUP BY region ORDER BY avg_price
            """, (manufacturer, model))
        elif manufacturer:
            cur.execute("""
                SELECT region, COUNT(*) as cnt, ROUND(AVG(price)) as avg_price
                FROM cars
                WHERE region IS NOT NULL AND manufacturer = %s
                  AND price > 50 AND price NOT IN (9990, 9999) AND price < 99000
                GROUP BY region ORDER BY avg_price
            """, (manufacturer,))
        else:
            cur.execute("""
                SELECT region, COUNT(*) as cnt, ROUND(AVG(price)) as avg_price
                FROM cars
                WHERE region IS NOT NULL
                  AND price > 50 AND price NOT IN (9990, 9999) AND price < 99000
                GROUP BY region ORDER BY avg_price
            """)
        stats = cur.fetchall()
    conn.close()
    return jsonify(stats)


@app.route('/region')
def region():
    conn = get_db()
    with conn.cursor() as cur:
        cur.execute("""
            SELECT region, COUNT(*) as cnt, ROUND(AVG(price)) as avg_price,
                   MIN(price) as min_price, MAX(price) as max_price
            FROM cars
            WHERE region IS NOT NULL
              AND price > 50 AND price NOT IN (9990, 9999) AND price < 99000
            GROUP BY region
            ORDER BY cnt DESC
        """)
        region_stats = cur.fetchall()
        cur.execute("SELECT DISTINCT manufacturer FROM cars ORDER BY manufacturer")
        manufacturers = [r['manufacturer'] for r in cur.fetchall()]
    conn.close()
    return render_template('region.html', region_stats=region_stats, manufacturers=manufacturers)


if __name__ == '__main__':
    app.run(debug=True)