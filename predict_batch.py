import pymysql
import pandas as pd
import numpy as np
import joblib
import os
from dotenv import load_dotenv

load_dotenv()

conn = pymysql.connect(
    host=os.getenv('DB_HOST', '127.0.0.1'),
    port=int(os.getenv('DB_PORT', 3306)),
    database=os.getenv('DB_NAME', 'UsedCar'),
    user=os.getenv('DB_USER', 'root'),
    password=os.getenv('DB_PASSWORD', ''),
    charset='utf8mb4',
    cursorclass=pymysql.cursors.DictCursor
)

model    = joblib.load('model.pkl')
encoders = joblib.load('encoders.pkl')

with conn.cursor() as cur:
    cur.execute("""
        SELECT id, manufacturer, model, badge,
               COALESCE(fuel_type, '기타') AS fuel_type,
               year, mileage
        FROM cars
        WHERE year IS NOT NULL AND mileage IS NOT NULL
    """)
    rows = cur.fetchall()

df = pd.DataFrame(rows)
print(f"예측 대상: {len(df):,}건")

# 인코딩
for col in ['manufacturer', 'model', 'badge', 'fuel_type']:
    le = encoders[col]
    df[col] = df[col].astype(str)
    known = set(le.classes_)
    df[col] = df[col].apply(lambda x: x if x in known else le.classes_[0])
    df[col] = le.transform(df[col])

feature_cols = list(model.feature_names_in_)
print(f"모델 피처 순서: {feature_cols}")
X = df[feature_cols]
preds = np.expm1(model.predict(X)).astype(int)

# DB 업데이트 (1000건씩 배치)
ids = df['id'].tolist()
batch_size = 1000
with conn.cursor() as cur:
    for i in range(0, len(ids), batch_size):
        batch_ids   = ids[i:i+batch_size]
        batch_preds = preds[i:i+batch_size]
        data = [(int(p), int(id_)) for p, id_ in zip(batch_preds, batch_ids)]
        cur.executemany("UPDATE cars SET predicted_price = %s WHERE id = %s", data)
        conn.commit()
        print(f"업데이트: {min(i+batch_size, len(ids))}/{len(ids)}")

conn.close()
print("완료!")
