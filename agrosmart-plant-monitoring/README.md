# AgroSmart — Connected Plant & Soil Monitoring

A precision-agriculture prototype: an ESP32 monitors air temperature and **soil moisture**, decides locally whether the plant needs water (**edge computing**), and publishes its data to a remote **Node-RED** dashboard over **MQTT**.

> Academic project — IoT module, ENSA Fez (GSCSI). Simulated on Wokwi.

![ESP32](https://img.shields.io/badge/ESP32-MicroPython-blue) ![MQTT](https://img.shields.io/badge/MQTT-HiveMQ-660066) ![Node-RED](https://img.shields.io/badge/Node--RED-dashboard-8F0000)

---

## Data flow

```
Sensors ──► ESP32 (local decision, LEDs) ──► JSON over MQTT ──► HiveMQ ──► Node-RED dashboard
                                             topic: ensi/iot/agro/sensors
```

## Hardware

| Component | Pin | Role |
|---|---|---|
| ESP32 | — | Built-in Wi-Fi, enough power for MQTT + JSON |
| DHT22 | GPIO 15 | Air temperature & humidity (more precise than the DHT11) |
| Potentiometer | GPIO 34 (ADC) | Simulates a soil-moisture sensor |
| Blue LED | GPIO 12 | Network status (blinking = searching Wi-Fi, steady = connected) |
| Green / yellow / red LEDs | GPIO 2, 4, 5 | Immediate plant diagnosis |

## Firmware logic (MicroPython)

1. Reads the sensors every 5 seconds.
2. **ADC tuning:** `adc.atten(ADC.ATTN_11DB)` so the 12-bit ADC (0–4095) covers the full voltage range — without it the reading saturates around 1 V.
3. Converts the raw value to a moisture percentage: `(1 - raw / 4095) * 100` (soil sensors work inversely: wetter soil → lower voltage).
4. **Local decision (edge computing):**
   - moisture > 60 % → **green** (all good)
   - 30 – 60 % → **yellow** (the plant starts to need water)
   - < 30 % → **red** (urgent watering)
5. Serialises `{"temp": t, "sol": h}` to JSON and publishes it to HiveMQ.
6. `try / except` around network operations: if Wi-Fi or the broker fails, the LEDs keep protecting the plant locally.

## Dashboard (Node-RED)

`mqtt in` (same topic) → `json` → `change` nodes that route temperature and soil moisture to separate **gauges**, coloured according to the thresholds.

## Design choices

| Choice | Why | Instead of |
|---|---|---|
| MicroPython | Readable, fast prototyping | C++ (Arduino) |
| MQTT | Lightweight, works on unstable networks | HTTP polling |
| JSON | Standard, easy to parse in Node-RED | Raw text |
| HiveMQ public broker | Free, nothing to install | AWS IoT / Azure (heavier setup) |
| Node-RED | Dashboard built visually in minutes | Python/Flask + HTML/CSS/JS |

## Next steps

Store history in InfluxDB and use ESP32 deep sleep to run for months on a battery.
