import ubluetooth
import time
from micropython import const

mac_str = "40:78:25:87:41:7D"  # 替换为目标设备的 MAC 地址, 不区分大小写

addr = bytes.fromhex(mac_str.upper().replace(':', ''))
is_connect = False

# BLE 事件常量
_IRQ_PERIPHERAL_CONNECT = const(7)
_IRQ_GATTC_NOTIFY = const(18)

def bt_irq(event, data):
    global is_connect

    if event == _IRQ_GATTC_NOTIFY:
        conn_handle, value_handle, notify_data = data
        key_hex = notify_data.hex().upper()
        print("*" * 30)
        print(mac_str, "\n收到通知数据:", key_hex)

    elif event == _IRQ_PERIPHERAL_CONNECT:
        print("*" * 30)
        print(mac_str, "\n已连接设备:", mac_str)
        is_connect = True


ble = ubluetooth.BLE()
ble.active(True)
ble.irq(bt_irq)


while True:
    if not is_connect:
        print(time.time(), "尝试连接到:", mac_str)
        ble.gap_connect(0, addr)
    time.sleep(5)
