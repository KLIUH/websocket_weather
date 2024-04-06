import asyncio
import websockets
import json
import requests
import matplotlib.pyplot as plt
import io
import base64
import numpy as np

def fetch_forecast(api_key, location):
    forecast_url = f"http://api.openweathermap.org/data/2.5/forecast?q={location}&appid={api_key}&units=metric"
    response = requests.get(forecast_url)
    return response.json()

# Hàm lấy thông tin thời tiết hiện tại
def fetch_current_weather(api_key, location):
    current_weather_url = f"http://api.openweathermap.org/data/2.5/weather?q={location}&appid={api_key}&units=metric"
    response = requests.get(current_weather_url)
    return response.json()

# Hàm tạo biểu đồ và chuyển thành chuỗi base64
def plot_to_base64(dates, temperatures):
    # Tạo biểu đồ
    plt.figure(figsize=(10, 5))
    plt.plot(dates, temperatures, marker='o')
    plt.title('Dự báo nhiệt độ 5 ngày')
    plt.xlabel('Ngày')
    plt.ylabel('Nhiệt độ (°C)')
    plt.tight_layout()

    # Chuyển biểu đồ thành định dạng PNG và lưu vào buffer
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png')
    plt.close()
    
    # Chuyển buffer thành chuỗi base64
    buffer.seek(0)
    image_png = buffer.getvalue()
    buffer.close()
    base64_encoded = base64.b64encode(image_png).decode('utf-8')
    
    return base64_encoded

# Hàm vẽ biểu đồ và chuyển đổi thành base64
def draw_chart_and_encode(dates, temperatures):
    chart_base64 = plot_to_base64(dates, temperatures)
    return chart_base64

# Hàm trích xuất nhiệt độ cho mỗi ngày từ dữ liệu dự báo
# Hàm trích xuất nhiệt độ cho 6 ngày tiếp theo từ dữ liệu dự báo
from datetime import datetime, timedelta

def extract_next_six_days_temperatures(forecast_data):
    temperatures = {}
    current_date = datetime.now().date()
    for i, item in enumerate(forecast_data.get('list', [])[:40:8], 1):  # Lấy dữ liệu cho 6 ngày tiếp theo, mỗi ngày 8 lần ghi nhận
        day = current_date + timedelta(days=i)  # Tính ngày tháng năm cho mỗi ngày
        day_string = day.strftime('%d/%m/%Y')  # Chuyển đổi sang chuỗi ngày tháng năm
        temperature = item['main']['temp']  # Lấy nhiệt độ
        temperatures[day_string] = temperature
    return temperatures



async def weather_server(websocket, path):
    api_key = 'b6dedfe7447312efb73077384941aa06'  # Thay thế bằng API key của bạn
    while True:
        try:
            location = await websocket.recv()
            if not location:  # Kiểm tra nếu location rỗng
                location = "Gia Lai"  # Thay thế thành phố mặc định ở đây
            # Lấy dữ liệu thời tiết hiện tại
            current_weather_data = fetch_current_weather(api_key, location)
            # Lấy dữ liệu dự báo thời tiết
            forecast_data = fetch_forecast(api_key, location)

            # Xác định giá trị mặc định cho các trường thông tin thời tiết
            temperature = 'N/A'
            weather = 'N/A'
            humidity = 'N/A'
            wind_speed = 'N/A'
            clouds = 'N/A'
            pressure = 'N/A'
            wind_direction = 'N/A'

            # Kiểm tra và gán giá trị thực cho các trường thông tin thời tiết nếu chúng tồn tại
            if 'main' in current_weather_data:
                temperature = current_weather_data['main'].get('temp', 'N/A')
                humidity = current_weather_data['main'].get('humidity', 'N/A')
                pressure = current_weather_data['main'].get('pressure', 'N/A')
            if 'weather' in current_weather_data:
                weather = current_weather_data['weather'][0].get('main', 'N/A')
            if 'wind' in current_weather_data:
                wind_speed = current_weather_data['wind'].get('speed', 'N/A')
                wind_direction = current_weather_data['wind'].get('deg', 'N/A')
            if 'clouds' in current_weather_data:
                clouds = current_weather_data['clouds'].get('all', 'N/A')

            # Xử lý dữ liệu và tạo biểu đồ
            temperatures = extract_next_six_days_temperatures(forecast_data)

            # Đóng gói dữ liệu thời tiết hiện tại và biểu đồ vào JSON
            payload = {
                'location': location,
                'temperatures': temperatures,
                'current': {
                    'temperature': temperature,
                    'weather': weather,
                    'humidity': humidity,
                    'wind_speed': wind_speed,
                    'clouds': clouds,
                    'pressure': pressure,
                    'wind_direction': wind_direction,


                }
            }
            await websocket.send(json.dumps(payload))
        except websockets.exceptions.ConnectionClosed:
            break

start_server = websockets.serve(weather_server, 'localhost', 8000)
asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()
