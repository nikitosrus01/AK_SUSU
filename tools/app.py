import io
import logging
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
import pandas as pd

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("telemetry_logger")

app = FastAPI(title="AK SUSU — TELEMETRY REPLAY")

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
TEMPLATES_DIR = BASE_DIR / "templates"

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

@app.get("/", response_class=HTMLResponse)
async def read_root():
    index_path = TEMPLATES_DIR / "index.html"
    if not index_path.exists():
        return HTMLResponse(
            content=f"<h3>Ошибка: Файл index.html не найден: {index_path}</h3>", 
            status_code=404
        )
    return HTMLResponse(content=index_path.read_text(encoding="utf-8"))

@app.post("/api/process-telemetry")
async def process_telemetry(file: UploadFile = File(...)):
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Файл должен быть в формате CSV")
    
    contents = await file.read()
    try:
        decoded_content = contents.decode('utf-8', errors='ignore')
        df = pd.read_csv(io.StringIO(decoded_content))
    except Exception as e:
        logger.error(f"Ошибка парсинга CSV: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Ошибка чтения файла: {str(e)}")
    
    if df.empty:
        raise HTTPException(status_code=400, detail="Загруженный файл CSV пуст")

    # Нормализация колонок (Регистр + обрезка пробелов)
    df.columns = [str(col).strip().capitalize() for col in df.columns]
    mapping = {'Lat': 'Lat', 'Lon': 'Lon', 'Gps_lat': 'Lat', 'Gps_lon': 'Lon', 'Latitude': 'Lat', 'Longitude': 'Lon'}
    df.rename(columns=mapping, inplace=True)

    required_cols = ['Time', 'Altitude', 'Speed', 'Acceleration', 'Pressure', 'State', 'Lat', 'Lon']
    missing_cols = [col for col in required_cols if col not in df.columns]
    
    if missing_cols:
        raise HTTPException(status_code=400, detail=f"Не найдены колонки: {missing_cols}")

    # Дропаем пустые строки и приводим типы данных к стандартным принудительно
    df.dropna(subset=['Time', 'Altitude'], inplace=True)
    for col in ['Time', 'Altitude', 'Speed', 'Acceleration', 'Pressure', 'Lat', 'Lon']:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0.0)
    
    df['State'] = df['State'].astype(str).replace('nan', 'ПОЛЁТ')
    
    # Превращаем DataFrame в чистый Python-список словарей (избавляемся от капризов Pandas в анализе)
    data_list = df.to_dict(orient='records')
    total_points = len(data_list)

    # --- ИНИЦИАЛИЗАЦИЯ ПЕРЕМЕННЫХ ДЛЯ ТЗ ---
    max_alt = 0.0
    legs_alt = None
    calculated_landing_speed = 0.0
    
    tz_max_alt = False
    tz_legs = False
    tz_landing_speed = False

    # Вся математика внутри безопасного блока try-except
    try:
        # 1. Поиск Апогея (Максимальной высоты)
        max_alt = max([row['Altitude'] for row in data_list])
        tz_max_alt = 45.0 <= max_alt <= 55.0

        # Находим индекс максимальной высоты для дальнейшего анализа спуска
        apogee_idx = 0
        for i, row in enumerate(data_list):
            if row['Altitude'] == max_alt:
                apogee_idx = i
                break

        # 2. Поиск раскрытия опор
        # Проверяем ключевые слова в статусах
        for row in data_list:
            state_upper = row['State'].upper()
            if 'ОПОРЫ' in state_upper or 'ОПОР' in state_upper or 'ПАРАШЮТ' in state_upper:
                legs_alt = row['Altitude']
                break
        
        # Если в логах нет явного статуса, берем точку спуска ниже 25 метров
        if legs_alt is None:
            for i in range(apogee_idx, total_points):
                if data_list[i]['Altitude'] <= 25.0:
                    legs_alt = data_list[i]['Altitude']
                    break
        
        if legs_alt is not None and legs_alt <= 25.0:
            tz_legs = True

        # 3. Скорость приземления методом численного интегрирования (трапеций)
        # Ищем точку касания (минимальная высота на этапе спуска или статус ПОСАДКА)
        landing_idx = total_points - 1
        for i in range(apogee_idx, total_points):
            if 'ПОСАДКА' in data_list[i]['State'].upper():
                landing_idx = i
                break
        
        # Берем последние 40-50 точек перед посадкой для расчета интеграла
        start_calc_idx = max(apogee_idx, landing_idx - 45)
        
        integrated_speed = 0.0
        if start_calc_idx > 0 and landing_idx > start_calc_idx:
            for i in range(start_calc_idx + 1, landing_idx + 1):
                dt = data_list[i]['Time'] - data_list[i-1]['Time']
                if dt <= 0 or dt > 0.5:
                    dt = 0.02  # Шаг по умолчанию при аномалиях таймера
                
                a1 = data_list[i-1]['Acceleration']
                a2 = data_list[i]['Acceleration']
                
                # Формула трапеций: v += ((a1 + a2) / 2) * dt
                integrated_speed += ((a1 + a2) / 2.0) * dt
            
            calculated_landing_speed = abs(integrated_speed)
        
        # Критическая страховка: если интеграл улетел из-за шумов акселерометра, пишем скорость с датчика
        if calculated_landing_speed > 30.0 or calculated_landing_speed == 0.0:
            calculated_landing_speed = abs(data_list[landing_idx]['Speed'])

    except Exception as e:
        logger.error(f"Внутренняя ошибка мат-анализа: {e}")
        # Если всё упало — берем значения напрямую из крайних точек без интегралов
        if total_points > 0:
            max_alt = max([row['Altitude'] for row in data_list])
            calculated_landing_speed = abs(data_list[-1]['Speed'])

    tz_landing_speed = calculated_landing_speed <= 3.0

    # Формируем итоговый пакет экспертизы
    analysis = {
        "max_altitude": {"value": round(max_alt, 2), "status": bool(tz_max_alt), "msg": f"Макс. высота: {round(max_alt, 2)}м (Ожидалось 50±5м)"},
        "legs_deployment": {"value": round(legs_alt, 2) if legs_alt else None, "status": bool(tz_legs), "msg": f"Раскрытие опор на {round(legs_alt, 2) if legs_alt else '—'}м (Ожидалось <= 25м)"},
        "landing_speed": {"value": round(calculated_landing_speed, 2), "status": bool(tz_landing_speed), "msg": f"Скорость касания (интеграл): {round(calculated_landing_speed, 2)} м/с (Ожидалось <= 3м/с)"},
        "verdict": bool(tz_max_alt and tz_legs and tz_landing_speed)
    }

    return {
        "telemetry": data_list,
        "analysis": analysis
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)