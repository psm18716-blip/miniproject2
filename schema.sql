CREATE DATABASE IF NOT EXISTS UsedCar DEFAULT CHARACTER SET utf8mb4;
USE UsedCar;

CREATE TABLE IF NOT EXISTS cars (
    id           VARCHAR(20)  NOT NULL,
    car_type     VARCHAR(10)  NOT NULL COMMENT '국산/수입',
    manufacturer VARCHAR(50)  NOT NULL,
    model        VARCHAR(100) NOT NULL,
    badge        VARCHAR(100),
    fuel_type    VARCHAR(30),
    year         INT,
    mileage      INT,
    price        INT          COMMENT '단위: 만원',
    region       VARCHAR(20),
    photo_url    VARCHAR(255),
    created_at   TIMESTAMP    DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
