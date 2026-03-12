"""
Motor control for WallPi using TB6612 dual motor driver.
Controls the 2WD chassis movement via Raspberry Pi GPIO.
"""

import logging
import time

logger = logging.getLogger(__name__)

# Try to import RPi.GPIO, mock it if not on Pi
try:
    import RPi.GPIO as GPIO
    ON_PI = True
except ImportError:
    ON_PI = False
    logger.warning("RPi.GPIO not available - running in simulation mode")


class Motors:
    def __init__(
        self,
        left_in1: int, left_in2: int, left_pwm: int,
        right_in1: int, right_in2: int, right_pwm: int,
        pwm_freq: int = 100
    ):
        self.left_in1 = left_in1
        self.left_in2 = left_in2
        self.left_pwm_pin = left_pwm
        self.right_in1 = right_in1
        self.right_in2 = right_in2
        self.right_pwm_pin = right_pwm
        self.pwm_freq = pwm_freq

        self.left_pwm = None
        self.right_pwm = None

        if ON_PI:
            self._setup_gpio()

    def _setup_gpio(self):
        """Initialize GPIO pins"""
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)

        pins = [
            self.left_in1, self.left_in2, self.left_pwm_pin,
            self.right_in1, self.right_in2, self.right_pwm_pin
        ]
        for pin in pins:
            GPIO.setup(pin, GPIO.OUT)
            GPIO.output(pin, GPIO.LOW)

        self.left_pwm = GPIO.PWM(self.left_pwm_pin, self.pwm_freq)
        self.right_pwm = GPIO.PWM(self.right_pwm_pin, self.pwm_freq)
        self.left_pwm.start(0)
        self.right_pwm.start(0)

        logger.info("GPIO motors initialized ✅")

    def _set_motor(self, in1, in2, pwm, speed: float):
        """
        Set a single motor.
        speed: -100 to 100 (negative = reverse)
        """
        if not ON_PI:
            direction = "FWD" if speed > 0 else "REV" if speed < 0 else "STOP"
            logger.info(f"[SIM] Motor IN1={in1} IN2={in2} → {direction} {abs(speed):.0f}%")
            return

        if speed > 0:
            GPIO.output(in1, GPIO.HIGH)
            GPIO.output(in2, GPIO.LOW)
        elif speed < 0:
            GPIO.output(in1, GPIO.LOW)
            GPIO.output(in2, GPIO.HIGH)
        else:
            GPIO.output(in1, GPIO.LOW)
            GPIO.output(in2, GPIO.LOW)

        pwm.ChangeDutyCycle(abs(speed))

    def forward(self, speed: float = 70, duration: float = 1.0):
        """Move forward"""
        logger.info(f"⬆️ Forward {speed}% for {duration}s")
        self._set_motor(self.left_in1, self.left_in2, self.left_pwm, speed)
        self._set_motor(self.right_in1, self.right_in2, self.right_pwm, speed)
        time.sleep(duration)
        self.stop()

    def backward(self, speed: float = 70, duration: float = 1.0):
        """Move backward"""
        logger.info(f"⬇️ Backward {speed}% for {duration}s")
        self._set_motor(self.left_in1, self.left_in2, self.left_pwm, -speed)
        self._set_motor(self.right_in1, self.right_in2, self.right_pwm, -speed)
        time.sleep(duration)
        self.stop()

    def turn_left(self, speed: float = 60, duration: float = 0.5):
        """Turn left"""
        logger.info(f"⬅️ Turn left {speed}% for {duration}s")
        self._set_motor(self.left_in1, self.left_in2, self.left_pwm, -speed)
        self._set_motor(self.right_in1, self.right_in2, self.right_pwm, speed)
        time.sleep(duration)
        self.stop()

    def turn_right(self, speed: float = 60, duration: float = 0.5):
        """Turn right"""
        logger.info(f"➡️ Turn right {speed}% for {duration}s")
        self._set_motor(self.left_in1, self.left_in2, self.left_pwm, speed)
        self._set_motor(self.right_in1, self.right_in2, self.right_pwm, -speed)
        time.sleep(duration)
        self.stop()

    def happy_dance(self):
        """Wall-E style happy wiggle when greeted"""
        logger.info("💃 Happy dance!")
        for _ in range(3):
            self.turn_left(speed=50, duration=0.2)
            self.turn_right(speed=50, duration=0.2)
        self.stop()

    def stop(self):
        """Stop all motors"""
        self._set_motor(self.left_in1, self.left_in2, self.left_pwm, 0)
        self._set_motor(self.right_in1, self.right_in2, self.right_pwm, 0)

    def cleanup(self):
        """Release GPIO resources"""
        self.stop()
        if ON_PI:
            if self.left_pwm:
                self.left_pwm.stop()
            if self.right_pwm:
                self.right_pwm.stop()
            GPIO.cleanup()
        logger.info("Motors cleaned up")
