# PocketGo S30 stock firmware and hardware notes

A dump of the PocketGo S30's stock firmware (16 MB SPI-NOR), the board's
`script.bin`/`script.fex`, a few stock binaries, and decoded images with the
findings from reverse engineering them. These notes were the basis for a
mainline Linux + U-Boot firmware for the device:
[pocketgo-s30-cfw](https://github.com/bkacjios/pocketgo-s30-cfw).

## Contents

```
dump/                         The original dump, as taken from the device:
  flash/partitions/p0-p5        Raw SPI-NOR partitions (scrambled)
  flash/root/                   Stock root filesystem (the kernel's initramfs)
  script.bin, script.fex        Allwinner board configuration (fex)
  gmenu2x/, zkjoycalib/         Stock SD card binaries (game menu, joystick calibration)
  zktest/                       Stock test tool (with source)
decoded/                      Descrambled and extracted images (see below)
tools/                        The decoders that produce decoded/
```

Regenerate `decoded/` (needs Python 3; `zklogo.py` needs liblzo2):

```
python3 tools/decode_firmware.py dump decoded
python3 tools/zklogo.py decoded/p4_zklogo.bin decoded/zklogo.bmp
```

| File | Content |
|---|---|
| `flash_decoded.bin` | All partitions concatenated in dump order, descrambled |
| `p0_boot0.bin` | boot0 (eGON.BT0), plaintext in the dump |
| `p0_u-boot.bin` | Allwinner U-Boot 2011.09 package, descrambled |
| `p1_env.txt` | U-Boot environment |
| `p2_kernel.uImage` | Kernel uImage "ARM Zkswe Linux-3.4.39", descrambled |
| `p2_zImage`, `p2_Image` | The gzip zImage and the decompressed kernel (load address 0xc0008000) |
| `System.map` | Kernel symbols, recovered from kallsyms |
| `kernel.config` | Stock kernel config (IKCONFIG) |
| `p2_initramfs.cpio` | Built-in initramfs (the root filesystem) |
| `ili9488_init.txt` | LCD panel init sequence, extracted from the kernel |
| `p3_squashfs.img` | Squashfs partition (nearly empty) |
| `p4_zklogo.bin`, `zklogo.bmp` | Boot logo partition and the decoded 320x480 BMP |

## Hardware

| Item | Detail |
|---|---|
| SoC | Allwinner A33 (sun8iw5p1), stock board name `zkswe_a33` |
| DRAM | DDR3, 552 MHz, zq 0x3bfb, odt_en 1, tpr0 0x47214f, tpr1 0x1c2294b, tpr2 0x61043, tpr12 0xa8, tpr13 0x901 |
| PMIC | AXP223 on RSB (address 0x3a3). dcdc1 3.0 V, dcdc2 1.1 V, dcdc3 1.2 V, dcdc5 1.5 V, aldo2 2.5 V, aldo3 3.0 V |
| Boot flash | 16 MB SPI-NOR w25q128 on SPI0 (PC0-PC3) |
| SD card | mmc0 on PF0-PF5, card detect PB1 (active low) |
| Debug UART | UART1 on PG6 (TX) / PG7 (RX), 115200 |
| Display | ILI9488 320x480 MIPI-DSI panel, mounted landscape (see below) |
| Backlight | PWM0 on PH0, 50 kHz, active high |
| Audio | Internal codec, speaker amp enable PH9, headphone detect PL5 (low = plugged) |
| USB | OTG, ID pin PL7, VBUS via the AXP |
| LEDs | Blue: PL10, active low. Red (on while USB power is connected) and green: not software controlled as far as found, probably driven by the charger |
| Buttons | GPIO, active low (stock: `gpio-keys-polled`, 40 ms) |

### Buttons

Mapped by probing the pins on the stock system (fex gpkey1-17):

| Button | Pin | Button | Pin |
|---|---|---|---|
| Up | PG9 | A | PG12 |
| Down | PG8 | B | PG10 |
| Left | PL8 | X | PG13 |
| Right | PL9 | Y | PG11 |
| Select | PL11 | Start | PG4 |
| L1 | PB6 | R1 | PG3 |
| L2 | PB7 | R2 | PG2 |
| Vol+ | PG1 | Vol- | PG0 |
| Stick click | PG5? | | |

- The face buttons are in the Nintendo layout: X top, Y left, A right, B bottom.
- The stick click showed no change anywhere on the test unit (no GPIO change,
  nothing in the MCU data), so PG5 is a guess.
- gpkey18-21 (PB5-PB2) read as pressed at rest and match no button.
- Stock reports the keys as codes 0x3a-0x4e in fex order.

### Analog stick

A microcontroller on I2C0 (PH2/PH3) at address 0x60 (stock driver `mcu_ts`).

- A plain 4-byte read returns `A, ~A, B, ~B`. Further bytes repeat the last
  one with bit 7 set.
- Drop samples whose byte pairs don't add up to 0xff: those are torn reads.
- Byte 0 is the vertical axis (up = low) and byte 2 the horizontal axis
  (right = high).
- Measured range: X 30-235, Y 47-218, centre about 0x8f/0x85, noise ±1.

### Display

- Ilitek ILI9488, 320x480 portrait, mounted landscape.
- MIPI DSI, 1 lane, video mode, RGB888 (fex `lcd_if = 4`, `lcd_dsi_lane = 1`,
  `lcd_dsi_format = 0`, `lcd_dsi_if = 0`, `lcd_dsi_eotp = 0`).
- Timing: pixel clock 12 MHz, htotal 382, hbp 40 (including hspw 12),
  vtotal 524, vbp 22 (including vspw 4): 59.95 Hz. As a DRM mode: hfp 22 /
  hsync 12 / hbp 28, vfp 22 / vsync 4 / vbp 18.
- Power: AXP `dc1sw` (fex `lcd_power`), plus `dldo1` at 3.3 V set by the
  stock driver.
- Reset: PD26 (fex `lcd_gpio_0`). Stock sequence: pin config, 10 ms, high,
  50 ms, low, 20 ms, high, 100 ms, DSI HS clock on, 100 ms, init table.
- Init table, from the stock kernel's `LCD_panel_init` (0xc01d3e9c, table at
  0xc09888ec):

```
dcs 0xe0 00 10 14 01 0e 04 33 56 48 03 0c 0b 2b 34 0f   positive gamma
dcs 0xe1 00 12 18 05 12 06 40 34 57 06 10 0c 3b 3f 0f   negative gamma
dcs 0xc0 0f 0c                                          power control 1
dcs 0xc1 41                                             power control 2
dcs 0xc5 00 26 80                                       VCOM
dcs 0x36 48                                             MADCTL
dcs 0x3a 66                                             COLMOD 18 bpp
dcs 0xb0 00
dcs 0xb1 a0                                             frame rate
dcs 0xb4 02                                             inversion control
dcs 0xb6 02 02                                          display function
dcs 0xe9 00
dcs 0x21                                                inversion on
dcs 0xf7 a9 51 2c 82                                    adjust control 3
dcs 0x11                                                sleep out
delay 120 ms
dcs 0x29                                                display on
delay 20 ms
```

- Bring-up note: the A33's TCON0 must be clocked from PLL-MIPI. Fed from
  PLL3 at the same rate, low-power DCS writes work but HS video never starts.

### Audio

- Speaker: a mono amp (enable PH9) bridged across the codec's HPL/HPR.
  Stock unmutes the left headphone PA and drives the right with the inverted
  left (PAEN_HP_CTRL bit 1, LTRNMUTE), with HPCOM on.
- Stock mixer defaults: AIF1 DA0 160, DAC 160, AIF1 slot 0 DAC switch on.
- The headphone jack has left and right swapped.
- The jack detect (PL5) only reads correctly while the headphone amp is
  powered.
- Stock `tinyplay` plays nothing; `aplay` works.

### Power key (AXP223)

- Holding power for 6 s is a hardware power-off by the AXP (register 0x36 =
  0x5d).
- Stock sets bit 2 of register 0x36, "restart after long-press power-off"
  (fex `pmu_pekoff_func = 1`). The AXP keeps that bit while the battery is
  connected, so a long press turns the device off and straight back on.
  Clearing it (0x36 = 0x59) makes a long press stay off.
- Plugging in USB while the device is off powers the AXP on.

## Stock firmware

### SPI-NOR partitions

| Part | Size | Content |
|---|---|---|
| p0 | 384 KiB | boot0 (eGON.BT0, plaintext) at 0x0; Allwinner U-Boot 2011.09 package at 0x6000 (scrambled) |
| p1 | 128 KiB | U-Boot environment |
| p2 | 7.1 MiB | uImage "ARM Zkswe Linux-3.4.39" (scrambled), gzip zImage with built-in initramfs |
| p3 | 128 KiB | squashfs, nearly empty (`/dev/console`) |
| p4 | 256 KiB | "ZksweLogo" boot logo |
| p5 | 0 | empty |

### Scrambling

- **Kernel (p2):** the first 131072 bytes (fex `[zkswe_attr] ksize`) are XORed
  with the 4-byte key `35 6e a9 b7` (fex `kkey = -1213632971`). Stock U-Boot
  undoes it before `bootm`.
- **U-Boot (p0 at 0x6000):** each 32-bit word from header offset 0x2c up to
  the header's `length` field is XORed with `0x47000000` (byte 3 of each word
  XOR 0x47). boot0 undoes it when loading U-Boot.
- Everything else (environment, squashfs, logo) is stored as-is.

### Boot logo (p4)

"ZksweLogo" magic at 0x04, compressed and uncompressed sizes (little-endian
u32) at 0x14 and 0x18, LZO1X data at 0x40. It decompresses to a 320x480
24-bit BMP in the panel's native (portrait) orientation.

### Boot flow

BROM -> boot0 -> U-Boot -> kernel with built-in initramfs:

- U-Boot runs `bootcmd = run setargs_nor boot_normal`, i.e.
  `sunxi_flash read 40007fc0 boot; bootm 40007fc0`.
- The root filesystem is the initramfs (no `root=`).
- An Android-style `/init` + `init.rc` starts `vold`, `MtpDaemon` and `daemon`.
- The game UI is `gmenu2x`, launched from the SD card
  (`/mnt/extsd/bin/gmenu2x`).
- The A33 BROM tries the SD card before SPI-NOR, so a card with a bootloader
  at 8 KiB boots instead of the stock firmware. The flash is never touched;
  remove the card to get the stock system back.

### Debug access on stock

- `adbd` runs as root (`persist.sys.zkdebug=1` on the test unit).
- Stock ships `/bin/io`, which reads and writes physical memory through
  `/dev/mem` (`CONFIG_STRICT_DEVMEM` off). Useful for dumping SoC registers
  from the running stock system.

### FEL (USB recovery) mode

There is no button combination for FEL:

- boot0 never reads the keys.
- Stock U-Boot's `fel_key` check needs a fex `[fel_key]` section (absent) and
  an LRADC key (all buttons are GPIO).

What works: boot0 (`p0_boot0.bin` around 0x2374) jumps to the BROM's FEL
handler (0xffff0020) if RTC general-purpose register `0x01f00108` holds
`0x5aa5a55a`. It clears the register first, so this is one-shot. From the
stock system:

```
adb shell '/bin/io -4 0x01f00108 0x5aa5a55a; /bin/reboot'
sudo sunxi-fel ver   # AWUSBFEX soc=00001667(A33), USB 1f3a:efe8
```

This only works with no bootable SD card inserted, since the BROM tries the
card first. Alternatively, write `fel-sdboot.sunxi` at 8 KiB on a card for a
cold FEL boot.
