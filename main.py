# 修改 main.py 文件
"""
舵机与 esp32 引脚接线图, 数据口方向为后 (tail)

    前 (head)
        -----               -----
        |  2  |             |  3  |
        |pin25|             |Pin18|
        ----- -----   ----- -----
            |  0  | |  1  |
            |Pin12| |Pin16|
             -----   -----
            |  4  | |  5  |
            |Pin13| |Pin17|
        ----- -----   ----- -----
        |  6  |             |  7  |
        |Pin26|             |Pin19|
        -----               -----
    后 (tail)
"""

from quad import Quad
import machine
import time
from ble_controller import BLEController
from settings import BLE_MAC

robot = Quad()
robot.init(12, 16, 25, 18, 13, 17, 26, 19)
robot.setTrims(0, 0, 0, 0, 0, 0, 0, 0)

# 动作队列
current_key_hex = ""


def handle_notify(key_hex):
    global current_key_hex
    print("===> 回调函数触发，按键值:", key_hex)
    # 方向键
    current_key_hex = key_hex


# 创建蓝牙控制器实例
ble_controller = BLEController(BLE_MAC, notify_callback=handle_notify)
ble_controller.run()  # 启动扫描

# 主循环
while True:
    # 处理蓝牙事件
    if not ble_controller.update():
        break

    # 处理动作队列
    if current_key_hex:

        # 根据动作名称调用相应的方法
        if current_key_hex == "D1":
            print("forward")
            robot.forward(steps=1, t=800)
        elif current_key_hex == "D2":
            print("backward")
            robot.backward(steps=1, t=800)
        elif current_key_hex == "D3":
            print("turn_L")
            robot.turn_L(steps=1, t=800)
        elif current_key_hex == "D4":
            print("turn_R")
            robot.turn_R(steps=1, t=800)
        elif current_key_hex == "D0":
            print("stop")
            current_key_hex = ""
        elif current_key_hex == "A1":
            print("home")
            robot.home()
            current_key_hex = ""
        elif current_key_hex == "A2":
            print("hello")
            robot.hello()
            current_key_hex = ""
        elif current_key_hex == "A3":
            print("moonwalk_L")
            robot.moonwalk_L(steps=2, t=2000)
            current_key_hex = ""

    # 短暂休眠以允许系统处理其他任务
    time.sleep_ms(10)

print("未找到蓝牙手柄, 进入深度睡眠模式")
machine.deepsleep()
