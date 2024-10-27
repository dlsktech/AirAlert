import os
import requests
import schedule
import time
from dotenv import load_dotenv

load_dotenv()
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
DATA_URL = os.getenv("DATA_URL")

THRESHOLDS = {
    "PM2.5": [30, 100, 150],  # µg/m3
    "PM10": [50, 100, 150],
    "PM1": [30, 60, 90]
}

EMOJIS = {
    1: ":warning:",
    2: ":exclamation:",
    3: ":skull_and_crossbones:"
}

current_alert_level = 0

def check_air_quality():
    global current_alert_level
    response = requests.get(DATA_URL)
    if response.status_code != 200:
        print("Błąd podczas pobierania danych.")
        return

    data = response.json()
    total_pm25 = total_pm10 = total_pm1 = 0
    sensor_count = len(data)

    for sensor in data:
        for var in sensor["vars"]:
            if var["var_name"] == "PM2.5":
                total_pm25 += var["var_value"]
            elif var["var_name"] == "PM10":
                total_pm10 += var["var_value"]
            elif var["var_name"] == "PM1":
                total_pm1 += var["var_value"]

    avg_pm25 = total_pm25 / sensor_count if sensor_count > 0 else 0
    avg_pm10 = total_pm10 / sensor_count if sensor_count > 0 else 0
    avg_pm1 = total_pm1 / sensor_count if sensor_count > 0 else 0

    new_alert_level = determine_alert_level(avg_pm25, avg_pm10, avg_pm1)

    if new_alert_level != current_alert_level:
        send_notification(new_alert_level, avg_pm25, avg_pm10, avg_pm1)
        current_alert_level = new_alert_level

def determine_alert_level(avg_pm25, avg_pm10, avg_pm1):
    levels = [0, 0, 0]

    if avg_pm25 >= THRESHOLDS["PM2.5"][2]:
        levels[0] = 3
    elif avg_pm25 >= THRESHOLDS["PM2.5"][1]:
        levels[0] = 2
    elif avg_pm25 >= THRESHOLDS["PM2.5"][0]:
        levels[0] = 1

    if avg_pm10 >= THRESHOLDS["PM10"][2]:
        levels[1] = 3
    elif avg_pm10 >= THRESHOLDS["PM10"][1]:
        levels[1] = 2
    elif avg_pm10 >= THRESHOLDS["PM10"][0]:
        levels[1] = 1

    if avg_pm1 >= THRESHOLDS["PM1"][2]:
        levels[2] = 3
    elif avg_pm1 >= THRESHOLDS["PM1"][1]:
        levels[2] = 2
    elif avg_pm1 >= THRESHOLDS["PM1"][0]:
        levels[2] = 1

    return max(levels)

def send_notification(alert_level, avg_pm25, avg_pm10, avg_pm1):
    if alert_level == 0:
        message = (
            "Powietrze wróciło do normy. :white_check_mark:\n"
            "Jakość powietrza jest teraz w bezpiecznych granicach.\n"
            "Więcej informacji znajdziesz tutaj: <https://czystybialystok.pl|CzystyBialystok.pl>\n"
            "powered by <https://airalert.dlsk.tech/|AirAlert>"
        )
    else:
        emoji = EMOJIS[alert_level]
        alert_text = "podwyższony" if alert_level == 1 else "wysoki"
        message = (
            f"{emoji} Uwaga! {alert_text.capitalize()} poziom zanieczyszczeń:\n"
            f"PM2.5: {avg_pm25:.2f} µg/m3\n"
            f"PM10: {avg_pm10:.2f} µg/m3\n"
            f"PM1: {avg_pm1:.2f} µg/m3\n"
            f"Poziom zagrożenia: {alert_level}\n"
            f"Więcej informacji znajdziesz tutaj: <https://czystybialystok.pl|CzystyBialystok.pl>\n"
            "powered by <https://airalert.dlsk.tech/|AirAlert>"
        )

    payload = {"text": message}
    headers = {"Content-Type": "application/json"}
    response = requests.post(WEBHOOK_URL, json=payload, headers=headers)
    
    if response.status_code == 200:
        print("Powiadomienie wysłane.")
    else:
        print("Błąd podczas wysyłania powiadomienia.")

check_air_quality()

schedule.every(1).minute.do(check_air_quality)

if __name__ == "__main__":
    while True:
        schedule.run_pending()
        time.sleep(1)