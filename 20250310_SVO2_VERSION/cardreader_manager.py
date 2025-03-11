import utime
from machine import Pin

class CardReaderManager:
    def __init__(self):
        """初始化 CardReaderManager (先不設定 uart_manager, mqtt_manager)"""
        self.uart_manager = None
        self.mqtt_manager = None

        # 初始化 GPIO
        self.GPIO_CardReader_PAYOUT = Pin(18, Pin.IN, Pin.PULL_UP)
        self.GPO_CardReader_EPAY_EN = Pin(2, Pin.OUT)
        self.GPO_CardReader_EPAY_EN.value(0)

        # 記錄訊號變化的時間
        self.PAYOUT_falling_time = utime.ticks_ms()
        self.PAYOUT_last_rising_time = utime.ticks_ms()

    def set_dependencies(self, uart_manager, mqtt_manager):
        """設定相依物件，確保它們已經初始化完成後才設定"""
        self.uart_manager = uart_manager
        self.mqtt_manager = mqtt_manager

    def GPI_interrupt_handler(self, pin):
        """悠遊卡付款 GPIO 中斷處理函式"""
        PAYOUT_value = self.GPIO_CardReader_PAYOUT.value()
        PAYOUT_now_time = utime.ticks_ms()

        if PAYOUT_value == 0:  # 下降緣 (付款開始)
            self.PAYOUT_falling_time = PAYOUT_now_time
        elif PAYOUT_value == 1:  # 上升緣 (付款完成)
            PAYOUT_rising_time = PAYOUT_now_time
            PAYOUT_hipulse_time = self.PAYOUT_falling_time - self.PAYOUT_last_rising_time
            PAYOUT_lowpulse_time = PAYOUT_rising_time - self.PAYOUT_falling_time

            print(f"[CardReader] Hi Pulse: {PAYOUT_hipulse_time} ms, Low Pulse: {PAYOUT_lowpulse_time} ms")

            # 判斷是否為有效的付款訊號
            if PAYOUT_hipulse_time >= 100 and 50 <= PAYOUT_lowpulse_time <= 200:
                print("[CardReader] 付款成功，啟動娃娃機遊戲！")
                if self.uart_manager:
                    self.uart_manager.send_packet(KindFEILOLIcmd.Send_Starting_once_game)
            else:
                print("[CardReader] 訊號異常，不啟動遊戲")

            self.PAYOUT_last_rising_time = PAYOUT_rising_time

    def setup_gpio_interrupt(self):
        """設置 GPIO PAYOUT 付款中斷"""
        self.GPIO_CardReader_PAYOUT.irq(trigger=(Pin.IRQ_FALLING | Pin.IRQ_RISING), handler=self.GPI_interrupt_handler)
        print("[CardReader] 中斷綁定完成")
