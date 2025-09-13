# ble_controller.py
from machine import Pin, Timer
import ubluetooth
import time
from micropython import const
from ble_keymap import KEY_MAP
from settings import LED_PIN, BOARD, NO_NOTIFY_TIMEOUT

_IRQ_SCAN_RESULT = const(5)
_IRQ_SCAN_DONE = const(6)
_IRQ_PERIPHERAL_CONNECT = const(7)
_IRQ_PERIPHERAL_DISCONNECT = const(8)
_IRQ_GATTC_NOTIFY = const(18)


class BLEController:
    # BLE 事件常量

    def __init__(self, target_mac, scan_timeout=20, notify_callback=None):
        """
        target_mac: 目标设备的 MAC 地址
        notify_callback: 回调函数，格式 func(key_hex:str)
        """
        self.led = Pin(LED_PIN, Pin.OUT)
        self.timer = Timer(0)

        self.target_mac = target_mac.upper()
        self.device_name = None
        self.conn_handle = None
        self.target_to_connect = None
        self.notify_callback = notify_callback  # 保存回调函数
        self.scan_start_time = time.time()  # 添加扫描开始时间属性
        self.scan_time_over = scan_timeout  # 设置扫描超时时间(秒)

        if BOARD == "ESP32":
            self.boot_key = Pin(0, Pin.IN, pull=Pin.PULL_UP)
        elif BOARD == "ESP32-C3":
            self.boot_key = Pin(9, Pin.IN, pull=Pin.PULL_UP)
        else:
            raise Exception("Unknown board")

        self.boot_key.irq(trigger=Pin.IRQ_FALLING, handler=self.boot_key_interrupt_handler)

        self.ble = ubluetooth.BLE()
        self.ble.active(True)
        self.ble.irq(self._bt_irq)

        self.connected = False
        self.last_activity_time = time.time()


    def boot_key_interrupt_handler(self, pin):
        """
        BOOT按键中断处理函数
        当Pin9从高电平(1)变为低电平(0)时触发
        """
        # 停止BLE扫描
        self.ble.gap_scan(None)
        self.led_off()
        print("BOOT按键触发，已停止BLE扫描")
        raise RuntimeError(f"BOOT按键中断")

    def led_off(self):
        self.timer.deinit()
        if LED_PIN == 8:
            self.led.value(1)
        else:
            self.led.value(0)


    def led_on(self):
        self.timer.deinit()
        if LED_PIN == 8:
            self.led.value(0)
        else:
            self.led.value(1)


    def led_blink(self):
        self.timer.init(period=100, mode=Timer.PERIODIC, callback=lambda t: self.led.value(not self.led.value()))

    def set_notify_callback(self, callback):
        """设置回调函数"""
        self.notify_callback = callback

    def decode_name(self, adv_data):
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

    def decode_mac(self, addr):
        return ":".join("{:02X}".format(b) for b in bytes(addr))

    def start_scan(self):
        print("开始扫描目标设备...")
        try:
            self.ble.gap_scan(5000, 30000, 30000)
        except OSError:
            print("蓝牙已关闭")
        self.led_blink()

    def _bt_irq(self, event, data):
        if event == _IRQ_SCAN_RESULT:
            addr_type, addr, adv_type, rssi, adv_data = data
            mac_str = self.decode_mac(addr)
            name = self.decode_name(adv_data)
            print("发现设备:", mac_str, "名称:", name)
            if mac_str == self.target_mac:
                self.device_name = name
                print("找到目标设备:", mac_str, "名称:", self.device_name)
                self.target_to_connect = (addr_type, bytes(addr))
                self.ble.gap_scan(None)  # 停止扫描

        elif event == _IRQ_SCAN_DONE:
            print("扫描完成")
            if (self.conn_handle is None and
                    self.target_to_connect is None and
                    time.time() - self.scan_start_time < self.scan_time_over):
                self.start_scan()

        elif event == _IRQ_PERIPHERAL_CONNECT:
            self.conn_handle, addr_type, addr = data
            print("连接成功:", self.decode_mac(addr))
            print("设备名称:", self.device_name)
            self.connected = True
            self.led_on()

        elif event == _IRQ_PERIPHERAL_DISCONNECT:

            self.connected = False
            self.conn_handle, addr_type, addr = data
            print("连接断开:", self.decode_mac(addr))
            self.scan_start_time = time.time()
            self.device_name = None
            self.conn_handle = None
            self.target_to_connect = None
            self.start_scan()

        elif event == _IRQ_GATTC_NOTIFY:
            conn_handle, value_handle, notify_data = data
            key_hex = notify_data.hex().upper()
            self.last_activity_time = time.time()
            # print("收到通知数据:", key_hex)

            # 如果有映射表，打印解析结果
            if key_hex in KEY_MAP:
                # print("解析结果:", KEY_MAP[key_hex])
                # 调用用户自定义回调
                if self.notify_callback:
                    self.notify_callback(key_hex)
            else:
                print("未知按键:", key_hex)

    def ble_quit(self):
        self.led_off()
        self.connected = False
        self.ble.gap_scan(None)
        self.ble.active(False)

    # def run(self):
    #     self.start_scan()
    #     while True:
    #
    #         if time.time() - self.last_activity_time > NO_NOTIFY_TIMEOUT * 60:
    #             print(NO_NOTIFY_TIMEOUT, "分钟无手柄操作，自动退出")
    #             self.ble_quit()
    #             break
    #
    #         if self.boot_key.value() == 0:
    #             print("已按下BOOT按键，停止扫描")
    #             self.ble_quit()
    #             break
    #
    #         if self.connected:
    #             time.sleep(0.1)
    #             self.led_on()
    #             continue
    #
    #         else:
    #             if not self.target_to_connect:
    #                 if time.time() - self.scan_start_time < self.scan_time_over:
    #                     continue
    #                 else:
    #                     print("扫描超时，停止扫描, 超时时间:", self.scan_time_over)
    #                     self.ble_quit()
    #                     break
    #             else:
    #                 addr_type, addr = self.target_to_connect
    #                 print("尝试连接设备:", self.decode_mac(addr))
    #                 self.ble.gap_connect(addr_type, addr)
    #                 self.target_to_connect = None

    def run(self):
        """启动扫描但不阻塞"""
        self.start_scan()

    def update(self):
        """在主循环中定期调用此方法处理蓝牙事件"""
        if not self.connected:
            if not self.target_to_connect:
                if time.time() - self.scan_start_time < self.scan_time_over:
                    # 继续扫描逻辑
                    pass
                else:
                    print("扫描超时，停止扫描, 超时时间:", self.scan_time_over)
                    self.ble_quit()
                    return False
            else:
                addr_type, addr = self.target_to_connect
                print("尝试连接设备:", self.decode_mac(addr))
                self.ble.gap_connect(addr_type, addr)
                self.target_to_connect = None

        # 检查超时
        if time.time() - self.last_activity_time > NO_NOTIFY_TIMEOUT * 60:
            print(NO_NOTIFY_TIMEOUT, "分钟无手柄操作，自动退出")
            self.ble_quit()
            return False

        if self.boot_key.value() == 0:
            print("已按下BOOT按键，停止扫描")
            self.ble_quit()
            return False

        return True


if __name__ == "__main__":
    def handle_notify(key_hex):
        print("===> 回调函数触发，按键值:", key_hex)

    TARGET_MAC  = "D5:51:FA:B6:09:71"  # 替换为目标设备的 MAC 地址
    ble_controller = BLEController(TARGET_MAC, notify_callback=handle_notify)
    ble_controller.run()
