import pymysql
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import mean_absolute_error, r2_score
import joblib
import os
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    "host": os.getenv('DB_HOST', '127.0.0.1'),
    "port": int(os.getenv('DB_PORT', 3306)),
    "database": os.getenv('DB_NAME', 'UsedCar'),
    "user": os.getenv('DB_USER', 'root'),
    "password": os.getenv('DB_PASSWORD', ''),
    "charset": "utf8mb4",
}

def load_data():
    conn = pymysql.connect(**DB_CONFIG, cursorclass=pymysql.cursors.DictCursor)
    with conn.cursor() as cur:
        # NULL인 연료타입은 '기타'로 채워서 데이터 최대한 활용
        cur.execute("""
            SELECT manufacturer, model, badge, car_type,
                   COALESCE(fuel_type, '기타') AS fuel_type,
                   year, mileage, price
            FROM cars
            WHERE price > 50
              AND price NOT IN (9990, 9999) AND price < 99000
              AND year IS NOT NULL
              AND mileage IS NOT NULL
        """)
        rows = cur.fetchall()
    conn.close()

    df = pd.DataFrame(rows)
    print(f"학습 데이터: {len(df):,}건")
    return df


def preprocess(df):
    # 문자열 컬럼을 숫자로 변환 (LabelEncoder)
    # 예: '현대' → 3, '기아' → 1 처럼 내부 숫자로 매핑
    encoders = {}
    for col in ['manufacturer', 'model', 'badge' ,'car_type','fuel_type']:
        le = LabelEncoder()
        df[col] = le.fit_transform(df[col].astype(str))
        encoders[col] = le  # 나중에 예측할 때 동일한 매핑 필요

    return df, encoders


def train():
    # 1. 데이터 로드
    df = load_data()

    # 2. 전처리
    df, encoders = preprocess(df)

    # 3. 입력(X)과 정답(y) 분리
    X = df[['manufacturer', 'model','badge','car_type','fuel_type', 'year', 'mileage']]
    # 가격을 로그 변환: 100만~1억 넓은 범위를 균등하게 만들어 정확도 향상
    y = np.log1p(df['price'])

    # 4. 학습용 80% / 검증용 20% 분리
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    # 5. 모델 학습
    print("모델 학습 중... (1~2분 소요)")
    model = RandomForestRegressor(n_estimators=200, n_jobs=-1, random_state=42)
    model.fit(X_train, y_train)

    # 6. 성능 평가 (로그 역변환해서 실제 만원 단위로 오차 계산)
    y_pred_log = model.predict(X_test)
    y_pred = np.expm1(y_pred_log)       # log 역변환
    y_true = np.expm1(y_test)
    mae = mean_absolute_error(y_true, y_pred)
    r2  = r2_score(y_test, y_pred_log)  # log 공간에서의 R²
    print(f"MAE (평균 오차): {mae:.1f}만원")
    print(f"R² (정확도):     {r2:.3f}")

    # 7. 모델과 인코더를 파일로 저장 (Flask에서 불러다 씀)
    joblib.dump(model,    'model.pkl')
    joblib.dump(encoders, 'encoders.pkl')
    print("저장 완료 → model.pkl / encoders.pkl")


if __name__ == "__main__":
    train()
