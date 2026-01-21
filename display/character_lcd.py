"""Character LCD display driver using RPLCD library."""

from typing import List, Optional, Dict, Any
from .base import DisplayDriver

try:
    from RPLCD import CharLCD
    from RPLCD.gpio import GpioCharLCD
    from RPLCD.i2c import I2CCharLCD
    RPLCD_AVAILABLE = True
except ImportError:
    RPLCD_AVAILABLE = False
    CharLCD = None
    GpioCharLCD = None
    I2CCharLCD = None


class CharacterLCDDisplay(DisplayDriver):
    """Display driver for character LCD displays using RPLCD."""
    
    def __init__(
        self,
        width: int = 20,
        height: int = 4,
        display_settings: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize character LCD display.
        
        Args:
            width: LCD width in characters (default: 20)
            height: LCD height in lines (default: 4)
            display_settings: Dictionary with display configuration:
                - mode: 'i2c' or 'gpio'
                - For I2C: 'i2c_address' (default: 0x27), 'i2c_port' (default: 1)
                - For GPIO: 'pin_rs', 'pin_e', 'pins_data' (list), 'numbering_mode'
        """
        super().__init__(width, height)
        
        if not RPLCD_AVAILABLE:
            raise ImportError(
                "RPLCD library not available. Install with: pip install RPLCD"
            )
        
        display_settings = display_settings or {}
        mode = display_settings.get("mode", "i2c").lower()
        
        if mode == "i2c":
            # I2C mode
            i2c_address = display_settings.get("i2c_address", 0x27)
            i2c_port = display_settings.get("i2c_port", 1)
            self.lcd = I2CCharLCD(
                i2c_expander="PCF8574",
                address=i2c_address,
                port=i2c_port,
                cols=width,
                rows=height
            )
        elif mode == "gpio":
            # GPIO mode
            try:
                import RPi.GPIO as GPIO
            except ImportError:
                raise ImportError(
                    "RPi.GPIO not available. Install with: pip install RPi.GPIO"
                )
            
            pin_rs = display_settings.get("pin_rs", 15)
            pin_e = display_settings.get("pin_e", 16)
            pins_data = display_settings.get("pins_data", [21, 22, 23, 24])
            numbering_mode = display_settings.get("numbering_mode", "BCM")
            
            GPIO.setmode(GPIO.BCM if numbering_mode == "BCM" else GPIO.BOARD)
            
            self.lcd = GpioCharLCD(
                pin_rs=pin_rs,
                pin_e=pin_e,
                pins_data=pins_data,
                numbering_mode=GPIO.BCM if numbering_mode == "BCM" else GPIO.BOARD,
                cols=width,
                rows=height
            )
        else:
            raise ValueError(f"Unknown display mode: {mode}. Use 'i2c' or 'gpio'")
    
    def clear(self) -> None:
        """Clear the LCD display."""
        self.lcd.clear()
    
    def write_line(self, line: int, text: str) -> None:
        """Write text to a specific line."""
        if 0 <= line < self.height:
            # Truncate to width
            truncated = text[:self.width].ljust(self.width)
            self.lcd.cursor_pos = (line, 0)
            self.lcd.write_string(truncated)
    
    def update(self, lines: List[str]) -> None:
        """Update the entire display."""
        self.clear()
        for i, line in enumerate(lines[:self.height]):
            truncated = line[:self.width].ljust(self.width)
            self.lcd.cursor_pos = (i, 0)
            self.lcd.write_string(truncated)
    
    def close(self) -> None:
        """Clean up LCD resources."""
        try:
            self.lcd.close(clear=True)
        except Exception:
            pass
