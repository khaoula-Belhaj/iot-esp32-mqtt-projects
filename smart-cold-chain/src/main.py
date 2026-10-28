import network
import time
from machine import Pin, I2C, WDT, ADC, RTC
import dht
import ujson
from umqtt.simple import MQTTClient
import mpu6050

# --- 1. CONFIGURATION ---
WIFI_SSID, WIFI_PASSWORD = "Wokwi-GUEST", ""
MQTT_BROKER = "broker.hivemq.com"
MQTT_TOPIC  = "ensaf/coldchain/data"

# --- 2. INITIALISATION MATÉRIEL ---
sensor_dht = dht.DHT22(Pin(15))
i2c = I2C(0, scl=Pin(22), sda=Pin(21))
accel = mpu6050.accel(i2c)
led_alerte = Pin(14, Pin.OUT)
wdt = WDT(timeout=15000)
rtc = RTC()
# Initialisation de l'heure (Année, Mois, Jour, JourSemaine, Heure, Min, Sec, Microsec)
rtc.datetime((2024, 5, 20, 1, 10, 0, 0, 0))

# ADC pour la batterie (Module 5)
adc_bat = ADC(Pin(34))
adc_bat.atten(ADC.ATTN_11DB) # Pour lire jusqu'à 3.6V

# Interruption pour "Colis Ouvert" (Module 7)
colis_ouvert = 0
def alerte_ouverture(pin):
    global colis_ouvert
    colis_ouvert = 1
    print("!!! ALERTE : Le colis a été ouvert !!!")

btn_tamper = Pin(12, Pin.IN, Pin.PULL_UP)
btn_tamper.irq(trigger=Pin.IRQ_FALLING, handler=alerte_ouverture)

# --- 3. LOGIQUE ---
def connect_wifi():
    sta_if = network.WLAN(network.STA_IF)
    sta_if.active(True)
    sta_if.connect(WIFI_SSID, WIFI_PASSWORD)
    while not sta_if.isconnected():
        wdt.feed()
        time.sleep(0.5)
    print("WiFi OK")

connect_wifi()
client = MQTTClient("esp32-expert-A", MQTT_BROKER)
client.connect()

while True:
    try:
        wdt.feed()

        # Lecture Capteurs
        sensor_dht.measure()
        t, h = sensor_dht.temperature(), sensor_dht.humidity()

        # Lecture Batterie (ADC) - Conversion 0-4095 vers 0-100%
        niveau_bat = int((adc_bat.read() / 4095) * 100)

        # Lecture Choc
        val_accel = accel.get_values()
        choc = 1 if abs(val_accel['AcX']) > 15000 else 0

        # Récupération de l'heure (RTC)
        now = rtc.datetime()
        timestamp = "{:02d}:{:02d}:{:02d}".format(now[4], now[5], now[6])

        # Alerte LED
        if t > 8 or choc == 1 or colis_ouvert == 1:
            led_alerte.on()

        # Création du JSON final
        payload = ujson.dumps({
            "time": timestamp,
            "temp": t,
            "hum": h,
            "choc": choc,
            "open": colis_ouvert,
            "battery": niveau_bat
        })

        client.publish(MQTT_TOPIC, payload)
        print("Data envoyée :", payload)

        time.sleep(5)

    except Exception as e:
        print("Erreur réseau")
        time.sleep(2)
