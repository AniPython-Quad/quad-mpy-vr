import ubluetooth
import time
from micropython import const

device_name = "LOOKBON"
is_find = False
mac_str = ""

# BLE 事件常量
_IRQ_SCAN_RESULT = const(5)
_IRQ_SCAN_DONE = const(6)
_IRQ_GATTC_NOTIFY = const(18)

KEY_MAP = {
    # 按键映射
    "A1": "按键@: 单击",
    "B1": "按键@: 长按",
    "C1": "按键@: 长按释放",

    "A2": "按键A: 单击",
    "B2": "按键A: 长按",
    "C2": "按键A: 长按释放",

    "A3": "按键B: 单击",
    "B3": "按键B: 长按",
    "C3": "按键B: 长按释放",

    "A4": "按键C: 单击",
    "B4": "按键C: 长按",
    "C4": "按键C: 长按释放",

    "A5": "按键D: 单击",
    "B5": "按键D: 长按",
    "C5": "按键D: 长按释放",

    "A6": "按键R: 单击",  # 侧键下
    "B6": "按键R: 长按",
    "C6": "按键R: 长按释放",

    "A7": "按键L: 单击",  # 侧键上
    "B7": "按键L: 长按",
    "C7": "按键L: 长按释放",

    # 遥杆方向
    "D0": "方向: 无",
    "D1": "方向: 上",
    "D2": "方向: 下",
    "D3": "方向: 左",
    "D4": "方向: 右",
    "D5": "方向: 左上",
    "D6": "方向: 左下",
    "D7": "方向: 右上",
    "D8": "方向: 右下",
}


def decode_name(adv_data):
    """解析广播数据中的设备名"""
    adv_data = bytes(adv_data)
    n = 0
    while n + 1 < len(adv_data):
        length = adv_data[n]
        if length == 0:
            break
        type = adv_data[n + 1]
        if type == 0x09:  # Complete Local Name
            try:
                return adv_data[n + 2:n + 1 + length].decode("utf-8")
            except UnicodeError:
                return None
        n += 1 + length
    return None


def decode_mac(addr):
    """将 addr 转换为标准 MAC 地址字符串"""
    return ":".join("{:02X}".format(b) for b in bytes(addr)).upper()


def bt_irq(event, data):
    global device_name, is_find, mac_str

    if event == _IRQ_SCAN_RESULT:
        if is_find:
            return
        addr_type, addr, adv_type, rssi, adv_data = data
        mac_str = decode_mac(addr)
        name = decode_name(adv_data)
        print("发现设备:", mac_str, "名称:", name)
        if name and name.upper() == device_name.upper():
            device_name = name
            print("找到目标设备")
            print("*" * 20)
            print(mac_str)
            print("*" * 20)
            is_find = True
            ble.gap_scan(None)  # 停止扫描
            ble.gap_connect(addr_type, addr)

    elif event == _IRQ_SCAN_DONE:
        if not is_find:
            ble.gap_scan(3000, 30000, 30000)

    elif event == _IRQ_GATTC_NOTIFY:
        conn_handle, value_handle, notify_data = data
        key_hex = notify_data.hex().upper()
        print("*" * 30)
        print(mac_str, "\n收到通知数据:", key_hex)

        # 如果有映射表，打印解析结果
        if key_hex in KEY_MAP:
            print("解析结果:", KEY_MAP[key_hex])
        else:
            print("未知按键:", key_hex)


ble = ubluetooth.BLE()
ble.active(True)
ble.irq(bt_irq)

ble.gap_scan(5000, 30000, 30000)

while True:
    time.sleep(5)
