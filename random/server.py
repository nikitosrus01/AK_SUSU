import asyncio
import serial
import json
import websockets

# НАСТРОЙКА: Укажи порт, к которому подключена приемная плата на ПК
SERIAL_PORT = 'COM3'  
BAUD_RATE = 115200

connected_clients = set()

# Функция чтения из COM-порта
async def read_serial():
    try:
        # Открываем порт
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
        print(f" Успешно подключено к {SERIAL_PORT}")
        
        while True:
            if ser.in_waiting > 0:
                # Читаем строку от ESP
                raw_data = ser.readline().decode('utf-8').strip()
                print(f"Получено с бортика: {raw_data}")
                
                # Проверяем, что это валидный JSON
                try:
                    json.loads(raw_data)
                    # Вещаем данные всем открытым вкладкам браузера
                    if connected_clients:
                        await asyncio.gather(*[client.send(raw_data) for client in connected_clients])
                except json.JSONDecodeError:
                    pass # Игнорируем мусор в порту при запуске
                    
            await asyncio.sleep(0.01) # Защита от перегрузки процессора
    except Exception as e:
        print(f"Ошибка чтения порта: {e}")

# Логика работы с веб-страницей
async def handle_client(websocket):
    connected_clients.add(websocket)
    try:
        await websocket.wait_closed()
    finally:
        connected_clients.remove(websocket)

async def main():
    # Запускаем сервер WebSockets на порту 8765
    server = await websockets.serve(handle_client, "localhost", 8765)
    print("Websocket-сервер запущен на ws://localhost:8765")
    
    # Запускаем параллельное чтение порта
    await read_serial()

if __name__ == "__main__":
    asyncio.run(main())