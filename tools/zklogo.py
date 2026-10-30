#!/usr/bin/env python3
"""Decode the stock "ZksweLogo" boot logo partition (SPI-NOR p4) to a BMP.

Usage: zklogo.py <p4_zklogo.bin> <out.bmp>

Layout: "ZksweLogo" magic at 0x04, compressed and uncompressed sizes
(little-endian u32) at 0x14/0x18, LZO1X data at 0x40. The result is a
320x480 24-bit BMP in panel-native orientation. Needs liblzo2.
"""

import ctypes
import struct
import sys


def main():
    src, dst = sys.argv[1:]
    d = open(src, "rb").read()
    if d[4:13] != b"ZksweLogo":
        sys.exit("not a ZksweLogo partition")
    csize, usize = struct.unpack_from("<II", d, 0x14)
    lzo = ctypes.CDLL("liblzo2.so.2")
    out = ctypes.create_string_buffer(usize)
    n = ctypes.c_ulong(usize)
    ret = lzo.lzo1x_decompress_safe(d[0x40:0x40 + csize], ctypes.c_ulong(csize),
                                    out, ctypes.byref(n), None)
    if ret != 0 or n.value != usize:
        sys.exit(f"lzo1x decompression failed ({ret})")
    open(dst, "wb").write(out.raw)


if __name__ == "__main__":
    main()
