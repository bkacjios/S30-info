#!/usr/bin/env python3
"""Decode the PocketGo S30 (Zkswe A33) SPI-NOR dump into clean, inspectable images.

Usage: python decode_firmware.py <dump dir> <output dir>

Scrambling found in the stock firmware:
  p0 (boot0 + u-boot): boot0 (0x0000-0x5fff) is plaintext. The sunxi u-boot
      package at 0x6000 has every 32-bit word from header offset 0x2c up to its
      'length' field XORed with 0x47000000 (i.e. byte 3 of each word ^= 0x47).
      Boot0 undoes this when loading.
  p2 (boot): a legacy uImage whose first [zkswe_attr] ksize (131072) bytes are
      XORed with [zkswe_attr] kkey (-1213632971 = 0xb7a96e35, little-endian
      bytes 35 6e a9 b7). U-boot undoes this before bootm.
Everything else (env, squashfs, logo) is stored as-is.
"""
import os
import re
import struct
import sys
import zlib

KERNEL_KEY = struct.pack('<i', -1213632971)
KERNEL_KSIZE = 131072
UBOOT_KEY = 0x47
UBOOT_OFF = 0x6000
KBASE = 0xc0008000


def write(out, name, data):
    path = os.path.join(out, name)
    with open(path, 'wb') as f:
        f.write(data)
    print('  %-28s %9d bytes' % (name, len(data)))


def decode_p0(p0):
    boot0 = p0[:UBOOT_OFF]
    ub = bytearray(p0[UBOOT_OFF:])
    length = struct.unpack('<I', ub[0x14:0x18])[0]
    for i in range(0x2c + 3, min(length, len(ub)), 4):
        ub[i] ^= UBOOT_KEY
    return boot0, bytes(ub[:length])


def decode_p2(p2):
    d = bytearray(p2)
    for i in range(min(KERNEL_KSIZE, len(d))):
        d[i] ^= KERNEL_KEY[i & 3]
    magic, _, _, size, load, ep, dcrc = struct.unpack('>7I', d[:28])
    if magic != 0x27051956:
        raise SystemExit('p2: bad uImage magic after descramble')
    uimage = bytes(d[:64 + size])
    if zlib.crc32(uimage[64:]) & 0xffffffff != dcrc:
        raise SystemExit('p2: uImage data CRC mismatch')
    print('  uImage "%s" load=0x%x ep=0x%x size=%d (CRC ok)'
          % (d[32:64].split(b'\0')[0].decode(), load, ep, size))
    return uimage, bytes(d[64 + size:])


def gunzip_zimage(zimage):
    i = zimage.find(b'\x1f\x8b\x08')
    return zlib.decompressobj(31).decompress(zimage[i:])


def kallsyms(image):
    """Recover symbols from an uncompressed 3.4 ARM kernel (kallsyms tables)."""
    n = len(image) // 4
    w = struct.unpack('<%dI' % n, image[:n * 4])
    best, i = (0, 0), 0
    while i < n:
        if 0xc0000000 <= w[i] < 0xc2000000:
            j = i
            while j + 1 < n and w[j] <= w[j + 1] < 0xc2000000:
                j += 1
            if j - i > best[1] - best[0]:
                best = (i, j)
            i = j + 1
        else:
            i += 1
    k = best[1] + 1
    while w[k] == 0:
        k += 1
    num = w[k]
    addrs = w[best[1] + 1 - num:best[1] + 1]
    k += 1
    while w[k] == 0:
        k += 1
    p, names = k * 4, []
    for _ in range(num):
        names.append(image[p + 1:p + 1 + image[p]])
        p += 1 + image[p]
    p = ((p + 15) & ~15) + ((num + 255) // 256) * 4
    while image[p] == 0:
        p += 1
    tokens = []
    for _ in range(256):
        e = image.index(b'\0', p)
        tokens.append(image[p:e])
        p = e + 1
    syms = []
    for a, nm in zip(addrs, names):
        s = b''.join(tokens[c] for c in nm).decode('latin1')
        syms.append((a, s[0], s[1:]))
    return syms


def dump_panel_table(image, syms):
    """Decode the ili9488 DSI init table walked by its LCD_panel_init."""
    u32 = lambda a: struct.unpack('<I', image[a - KBASE:a - KBASE + 4])[0]
    inits = [a for a, _, s in syms if s == 'LCD_panel_init']
    lines = []
    for fn in inits:
        code = image[fn - KBASE:fn - KBASE + 0xc4]
        # The table base is the literal-pool word loaded into r4 (ldr r4, [pc, #x]).
        for off in range(0, len(code), 4):
            ins = struct.unpack('<I', code[off:off + 4])[0]
            if ins & 0xfffff000 == 0xe59f4000:
                tbl = u32(fn + off + 8 + (ins & 0xfff)) - 8
                break
        else:
            continue
        lines.append('table @ 0x%08x (from LCD_panel_init @ 0x%08x)' % (tbl, fn))
        a = tbl
        while True:
            cmd, ln = u32(a), u32(a + 4)
            if cmd == 0xfffe:
                break
            if cmd == 0xffff:
                lines.append('delay %d ms' % ln)
            else:
                p = image[a + 8 - KBASE:a + 8 - KBASE + ln]
                lines.append('dcs 0x%02x %s' % (cmd, ' '.join('%02x' % b for b in p)))
            a += 0x48
    return '\n'.join(lines) + '\n'


def main():
    src, out = sys.argv[1], sys.argv[2]
    os.makedirs(out, exist_ok=True)
    parts = os.path.join(src, 'flash', 'partitions')
    p = [open(os.path.join(parts, 'p%d' % i), 'rb').read() for i in range(5)]

    print('p0: boot0 + u-boot')
    boot0, uboot = decode_p0(p[0])
    write(out, 'p0_boot0.bin', boot0)
    write(out, 'p0_u-boot.bin', uboot)
    p0_clean = boot0 + uboot + p[0][UBOOT_OFF + len(uboot):]

    print('p1: u-boot env')
    env = p[1][4:].split(b'\0\0')[0].replace(b'\0', b'\n') + b'\n'
    write(out, 'p1_env.txt', env)

    print('p2: kernel')
    uimage, tail = decode_p2(p[2])
    zimage = uimage[64:]
    write(out, 'p2_kernel.uImage', uimage)
    write(out, 'p2_zImage', zimage)
    image = gunzip_zimage(zimage)
    write(out, 'p2_Image', image)
    syms = kallsyms(image)
    write(out, 'System.map', ''.join('%08x %s %s\n' % s for s in syms).encode())
    write(out, 'ili9488_init.txt', dump_panel_table(image, syms).encode())
    # Embedded gzip blobs: IKCONFIG (.config) and the built-in initramfs (rootfs).
    for m in re.finditer(rb'\x1f\x8b\x08', image):
        try:
            blob = zlib.decompressobj(31).decompress(image[m.start():])
        except zlib.error:
            continue
        if blob.startswith(b'#\n# Automatically generated'):
            write(out, 'kernel.config', blob)
        elif blob.startswith(b'070701'):
            write(out, 'p2_initramfs.cpio', blob)

    print('p3: squashfs')
    write(out, 'p3_squashfs.img', p[3])
    print('p4: zklogo')
    write(out, 'p4_zklogo.bin', p[4])

    print('full image (partitions concatenated in dump order, descrambled)')
    write(out, 'flash_decoded.bin', p0_clean + p[1] + uimage + tail + p[3] + p[4])


if __name__ == '__main__':
    main()
