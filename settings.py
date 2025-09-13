
# VR 手柄(LOOKBON) MAC 地址
# 获取方式:
#   1. 查看外包装或手柄机身获取
#   2. 使用 test_get_mac_by_name.py 获取

BLE_MAC = "D5:51:FA:B6:09:71"  # 需要修改

# 设置开发板
BOARD = "ESP32"  # ESP32-C3 或者 ESP32
if BOARD == "ESP32-C3":
    LED_PIN = 8
elif BOARD == "ESP32":
    LED_PIN = 2  # ESP32
else:
    raise Exception("请设置开发板, ESP32 或者 ESP32-C3")

# 设置手柄无通知超时, 自动关机
NO_NOTIFY_TIMEOUT = 5 # 分钟
