from flask import Flask, render_template, request
import pymysql
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)


ml_model    = None
ml_encoders = None

def _load_model():
    global ml_model, ml_encoders
    if ml_model is None:
        import joblib
        import numpy as np
        import pandas as pd
        ml_model    = joblib.load('model.pkl')
        ml_encoders = joblib.load('encoders.pkl')

def _safe_enc(le, val):
    s = str(val) if val is not None else 'None'
    return le.transform([s if s in set(le.classes_) else le.classes_[0]])[0]

def predict_price(car):
    import numpy as np
    import pandas as pd
    _load_model()
    feature_cols = list(ml_model.feature_names_in_)
    defaults = {'fuel_type': '기타'}
    row = {}
    for col in feature_cols:
        if col in ml_encoders:
            row[col] = _safe_enc(ml_encoders[col], car.get(col) or defaults.get(col))
        else:
            row[col] = car[col]
    X = pd.DataFrame([row], columns=feature_cols)
    return int(np.expm1(ml_model.predict(X)[0]))

# DB 연결 함수
def get_db():
    ssl_config = {'ca': 'ca.pem'} if os.path.exists('ca.pem') else None
    return pymysql.connect(
        host=os.getenv('DB_HOST', '127.0.0.1'),
        port=int(os.getenv('DB_PORT', 3306)),
        database=os.getenv('DB_NAME', 'UsedCar'),
        user=os.getenv('DB_USER', 'root'),
        password=os.getenv('DB_PASSWORD', ''),
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor,
        ssl=ssl_config
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

        cur.execute("""
            SELECT c.id, c.manufacturer, c.model, c.badge, c.fuel_type,
                   c.year, c.mileage, c.price, c.region, c.photo_url
            FROM cars c
            JOIN (
                SELECT model,
                       MAX(CASE WHEN photo_url IS NOT NULL THEN id END) AS photo_id,
                       MAX(id) AS max_id,
                       COUNT(*) AS cnt
                FROM cars
                WHERE car_type = '국산'
                  AND price > 50 AND price NOT IN (9990, 9999) AND price < 99000
                GROUP BY model
                ORDER BY cnt DESC
                LIMIT 15
            ) top ON c.id = COALESCE(top.photo_id, top.max_id)
            ORDER BY top.cnt DESC
        """)
        popular_domestic = cur.fetchall()

        cur.execute("""
            SELECT c.id, c.manufacturer, c.model, c.badge, c.fuel_type,
                   c.year, c.mileage, c.price, c.region, c.photo_url
            FROM cars c
            JOIN (
                SELECT model,
                       MAX(CASE WHEN photo_url IS NOT NULL THEN id END) AS photo_id,
                       MAX(id) AS max_id,
                       COUNT(*) AS cnt
                FROM cars
                WHERE car_type = '수입'
                  AND price > 50 AND price NOT IN (9990, 9999) AND price < 99000
                GROUP BY model
                ORDER BY cnt DESC
                LIMIT 15
            ) top ON c.id = COALESCE(top.photo_id, top.max_id)
            ORDER BY top.cnt DESC
        """)
        popular_imported = cur.fetchall()
    conn.close()

    return render_template('index.html', brands=brands, car_type=car_type,
                           popular_domestic=popular_domestic, popular_imported=popular_imported)




@app.route('/list')
def car_list():
    manufacturer    = request.args.get('manufacturer', '')
    fuel_type       = request.args.get('fuel_type', '')
    year_min        = request.args.get('year_min', '')
    year_max        = request.args.get('year_max', '')
    price_min       = request.args.get('price_min', '')
    price_max       = request.args.get('price_max', '')
    mileage_min     = request.args.get('mileage_min', '')
    mileage_max     = request.args.get('mileage_max', '')
    region          = request.args.get('region', '')
    q               = request.args.get('q', '')
    favs            = request.args.get('favs', '')
    car_type_filter = request.args.get('car_type_filter', '')
    sort            = request.args.get('sort', 'recommend')
    page            = int(request.args.get('page', 1))
    per_page        = 60
    offset          = (page - 1) * per_page

    sort_map = {
        'recommend':   'year DESC, mileage ASC, price ASC',
        'price_asc':   'price ASC',
        'price_desc':  'price DESC',
        'year_desc':   'year DESC, price ASC',
        'mileage_asc': 'mileage ASC',
    }
    order_by = sort_map.get(sort, 'year DESC, mileage ASC, price ASC')

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
        if car_type_filter:
            conditions.append('car_type = %s');      params.append(car_type_filter)
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
            SELECT id, manufacturer, model, badge, fuel_type, year, mileage, price, region, photo_url, predicted_price
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
                           q=q, favs=favs, sort=sort, region=region,
                           car_type_filter=car_type_filter)



@app.route('/analysis')
def analysis():
    import numpy as np
    import pandas as pd
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

        # 브랜드별 감가율 (매물 500건 이상 브랜드, 2015년 이후)
        cur.execute("""
            SELECT manufacturer, year, ROUND(AVG(price)) as avg_price
            FROM cars
            WHERE price > 50 AND price NOT IN (9990, 9999) AND price < 99000
              AND year >= 2015
              AND manufacturer IN (
                  SELECT manufacturer FROM cars
                  WHERE price > 50 AND price NOT IN (9990, 9999) AND price < 99000
                  GROUP BY manufacturer HAVING COUNT(*) >= 500
              )
            GROUP BY manufacturer, year
            ORDER BY manufacturer, year
        """)
        depreciation_raw = cur.fetchall()

        # 상관관계 분석용 원시 데이터
        cur.execute("""
            SELECT year, mileage, price FROM cars
            WHERE price > 50 AND price NOT IN (9990, 9999) AND price < 99000
              AND year IS NOT NULL AND mileage IS NOT NULL AND year >= 2010
            LIMIT 15000
        """)
        raw_data = cur.fetchall()
    conn.close()

    # 감가율 데이터를 브랜드별로 정리
    dep_brands = {}
    for row in depreciation_raw:
        m = row['manufacturer']
        if m not in dep_brands:
            dep_brands[m] = {'years': [], 'prices': []}
        dep_brands[m]['years'].append(row['year'])
        dep_brands[m]['prices'].append(int(row['avg_price']))

    # 상관계수 및 회귀 분석
    raw_df = pd.DataFrame(raw_data)
    corr_year    = round(float(raw_df['year'].corr(raw_df['price'])), 3)
    corr_mileage = round(float(raw_df['mileage'].corr(raw_df['price'])), 3)
    coeffs_y = np.polyfit(raw_df['year'], raw_df['price'], 1)
    coeffs_m = np.polyfit(raw_df['mileage'], raw_df['price'], 1)
    price_per_year   = int(coeffs_y[0])          # 연식 1년 증가시 가격 변화 (만원)
    price_per_10k_km = int(coeffs_m[0] * 10000)  # 주행 1만km 증가시 가격 변화 (만원)

    return render_template('analysis.html',
                           brand_stats=brand_stats, year_stats=year_stats,
                           fuel_stats=fuel_stats, price_dist=price_dist,
                           type_stats=type_stats, summary=summary,
                           dep_brands=dep_brands,
                           corr_year=corr_year, corr_mileage=corr_mileage,
                           price_per_year=price_per_year,
                           price_per_10k_km=price_per_10k_km)


@app.route('/car/<car_id>')
def car_detail(car_id):
    conn = get_db()
    with conn.cursor() as cur:
        cur.execute("SELECT * FROM cars WHERE id = %s", (car_id,))
        car = cur.fetchone()

        cur.execute("""
            SELECT year, ROUND(AVG(price)) as avg_price
            FROM cars
            WHERE model = %s AND price > 50 AND price NOT IN (9990,9999) AND price < 99000
            GROUP BY year ORDER BY year
        """, (car['model'],))
        chart_data = cur.fetchall()

        # 지역 평균 시세 (같은 모델 + 지역)
        cur.execute("""
            SELECT ROUND(AVG(price)) as region_avg, COUNT(*) as region_cnt
            FROM cars
            WHERE model = %s AND region = %s
              AND price > 50 AND price NOT IN (9990,9999) AND price < 99000
        """, (car['model'], car['region']))
        region_stat = cur.fetchone()

        # 같은 연식 평균 주행거리
        cur.execute("""
            SELECT ROUND(AVG(mileage)) as avg_mileage
            FROM cars WHERE model = %s AND year = %s AND mileage IS NOT NULL
        """, (car['model'], car['year']))
        mileage_stat = cur.fetchone()

        # 전체 모델 매물 수
        cur.execute("SELECT COUNT(*) as cnt FROM cars WHERE model = %s", (car['model'],))
        model_cnt = cur.fetchone()['cnt']
    conn.close()

    # AI 예측 시세
    ai_price = None
    try:
        ai_price = predict_price(car)
    except Exception:
        pass

    # 추천 점수 계산 (0~99)
    score = 50
    avg_mileage = int(mileage_stat['avg_mileage']) if mileage_stat and mileage_stat['avg_mileage'] else None
    region_avg  = int(region_stat['region_avg'])   if region_stat and region_stat['region_avg']   else None

    if ai_price:
        diff_pct = (ai_price - car['price']) / ai_price * 100
        if diff_pct >= 20:   score += 25
        elif diff_pct >= 10: score += 15
        elif diff_pct >= 0:  score += 5
        elif diff_pct >= -10: score -= 10
        else:                 score -= 20

    if avg_mileage:
        ratio = car['mileage'] / avg_mileage
        if ratio < 0.7:   score += 20
        elif ratio < 1.0: score += 10
        elif ratio < 1.3: score -= 5
        else:              score -= 15

    score = max(5, min(99, score))

    return render_template('detail.html', car=car, chart_data=chart_data,
                           ai_price=ai_price, score=score,
                           region_avg=region_avg, region_cnt=int(region_stat['region_cnt']) if region_stat else 0,
                           avg_mileage=avg_mileage, model_cnt=model_cnt)

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
        year         = int(request.form.get('year'))
        mileage      = int(request.form.get('mileage'))

        try:
            fake_car = {'manufacturer': manufacturer, 'model': model_name,
                        'badge': badge, 'fuel_type': fuel_type,
                        'year': year, 'mileage': mileage}
            pred_price = predict_price(fake_car)

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
            result = {'error': f'예측 실패: {e}'}

    return render_template('predict.html',
                           manufacturers=manufacturers,
                           fuel_types=fuel_types,
                           result=result)


@app.route('/api/ai-insight')
def api_ai_insight():
    from flask import jsonify
    import numpy as np
    import pandas as pd
    import google.generativeai as genai

    api_key = os.getenv('GEMINI_API_KEY', '')
    if not api_key:
        return jsonify({'error': 'GEMINI_API_KEY가 .env에 없습니다.'})

    conn = get_db()
    with conn.cursor() as cur:
        cur.execute("""
            SELECT manufacturer, ROUND(AVG(price)) as avg_price, COUNT(*) as cnt
            FROM cars WHERE price > 50 AND price NOT IN (9990,9999) AND price < 99000
            GROUP BY manufacturer ORDER BY cnt DESC LIMIT 10
        """)
        brand_stats = cur.fetchall()

        cur.execute("""
            SELECT year, ROUND(AVG(price)) as avg_price
            FROM cars WHERE price > 50 AND price NOT IN (9990,9999) AND price < 99000 AND year >= 2015
            GROUP BY year ORDER BY year
        """)
        year_stats = cur.fetchall()

        cur.execute("""
            SELECT fuel_type, COUNT(*) as cnt
            FROM cars WHERE price > 50 AND price NOT IN (9990,9999) AND price < 99000 AND fuel_type IS NOT NULL
            GROUP BY fuel_type ORDER BY cnt DESC
        """)
        fuel_stats = cur.fetchall()

        cur.execute("""
            SELECT car_type, ROUND(AVG(price)) as avg_price, COUNT(*) as cnt
            FROM cars WHERE price > 50 AND price NOT IN (9990,9999) AND price < 99000
            GROUP BY car_type
        """)
        type_stats = cur.fetchall()

        cur.execute("""
            SELECT year, mileage, price FROM cars
            WHERE price > 50 AND price NOT IN (9990,9999) AND price < 99000
              AND year IS NOT NULL AND mileage IS NOT NULL AND year >= 2010
            LIMIT 15000
        """)
        raw_data = cur.fetchall()

        cur.execute("""
            SELECT COUNT(*) as total FROM cars
            WHERE price > 50 AND price NOT IN (9990,9999) AND price < 99000
        """)
        summary = cur.fetchone()
    conn.close()

    raw_df = pd.DataFrame(raw_data)
    corr_year    = round(float(raw_df['year'].corr(raw_df['price'])), 3)
    corr_mileage = round(float(raw_df['mileage'].corr(raw_df['price'])), 3)
    coeffs_y = np.polyfit(raw_df['year'], raw_df['price'], 1)
    coeffs_m = np.polyfit(raw_df['mileage'], raw_df['price'], 1)
    price_per_year   = int(coeffs_y[0])
    price_per_10k_km = int(coeffs_m[0] * 10000)

    user_q = request.args.get('q', '').strip()
    if not user_q:
        return jsonify({'error': '질문을 입력해주세요.'})

    top5 = brand_stats[:5]
    brand_text = ', '.join([f"{r['manufacturer']}(평균{int(r['avg_price'])}만/{int(r['cnt'])}대)" for r in top5])
    fuel_top3  = ', '.join([f"{r['fuel_type']}:{int(r['cnt'])}대" for r in fuel_stats[:3]])
    type_text  = ', '.join([f"{r['car_type']} 평균{int(r['avg_price'])}만원({int(r['cnt'])}대)" for r in type_stats])
    y_oldest   = year_stats[0]  if year_stats else {}
    y_newest   = year_stats[-1] if year_stats else {}

    context = (
        f"[중고차 데이터 요약 - 총 {int(summary['total']):,}대]\n"
        f"브랜드TOP5: {brand_text}\n"
        f"연료(상위3): {fuel_top3}\n"
        f"국산vs수입: {type_text}\n"
        f"연식별시세: {y_oldest.get('year','')}년 평균{int(y_oldest.get('avg_price',0))}만 → {y_newest.get('year','')}년 평균{int(y_newest.get('avg_price',0))}만\n"
        f"상관계수: 연식-가격={corr_year}, 주행거리-가격={corr_mileage}\n"
        f"회귀: 연식1년↑=+{price_per_year}만원, 주행1만km↑={price_per_10k_km}만원"
    )
    prompt = f"{context}\n\n위 데이터를 참고해서 다음 질문에 3~4문장으로 답해줘. 마크다운 없이 자연스러운 한국어로:\n{user_q}"

    try:
        import requests as req
        url = (f'https://generativelanguage.googleapis.com/v1beta/models/'
               f'gemini-flash-latest:generateContent?key={api_key}')
        payload = {'contents': [{'parts': [{'text': prompt}]}]}
        r = req.post(url, json=payload, timeout=30)
        if r.status_code == 429:
            return jsonify({'error': 'API 무료 할당량 초과. 잠시 후 다시 시도해주세요.'})
        r.raise_for_status()
        text = r.json()['candidates'][0]['content']['parts'][0]['text']
        return jsonify({'insight': text})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)})


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


@app.route('/compare')
def compare():
    from flask import redirect
    ids_raw = request.args.get('ids', '')
    id_list = [i.strip() for i in ids_raw.split(',') if i.strip()][:2]
    if len(id_list) < 2:
        return redirect('/list')

    conn = get_db()
    with conn.cursor() as cur:
        placeholders = ','.join(['%s'] * len(id_list))
        cur.execute(f"SELECT * FROM cars WHERE id IN ({placeholders})", id_list)
        cars = cur.fetchall()
    conn.close()

    # 조회 순서를 URL id 순서에 맞게 정렬
    id_order = {int(i): idx for idx, i in enumerate(id_list)}
    cars = sorted(cars, key=lambda c: id_order.get(c['id'], 99))

    ai_prices = []
    for car in cars:
        try:
            ai_prices.append(predict_price(car))
        except Exception:
            ai_prices.append(None)

    return render_template('compare.html', cars=cars, ai_prices=ai_prices)


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