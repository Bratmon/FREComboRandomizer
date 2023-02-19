#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Usage:
    python-ips [options] PATCH TARGET

Options:
    -h --help    Display this message.
    -b --backup  Create a backup of target named TARGET.bak
"""


import shutil
import struct

from os.path import getsize
from argparse import ArgumentParser

parser = ArgumentParser()
parser.add_argument('PATCH', type=str)
parser.add_argument('TARGET', type=str)
parser.add_argument('-b')


def unpack_int(string):
    """Read an n-byte big-endian integer from a byte string."""
    (ret,) = struct.unpack_from('>I', b'\x00' * (4 - len(string)) + string)
    return ret

def apply(patchpath, filepath):
    patch_size = getsize(patchpath)
    patchfile = open(patchpath, 'rb')
    target = open(filepath, 'r+b')

    if patchfile.read(5) != b'PATCH':
        raise Exception('Invalid patch header.')

    # Read First Record
    r = patchfile.read(3)
    while patchfile.tell() not in [patch_size, patch_size - 3]:
        # Unpack 3-byte pointers.
        offset = unpack_int(r)
        # Read size of data chunk
        r = patchfile.read(2)
        size = unpack_int(r)

        if not size:  # RLE Record
            r = patchfile.read(2)
            rle_size = unpack_int(r)
            data = patchfile.read(1) * rle_size
        else:
            data = patchfile.read(size)

        # Write to file
        target.seek(offset)
        target.write(data)
        # Read Next Record
        r = patchfile.read(3)

    if patch_size - 3 == patchfile.tell():
        trim_size = unpack_int(patchfile.read(3))
        target.truncate(trim_size)

    # Cleanup
    target.close()
    patchfile.close()


def main():
    args = parser.parse_args()
    if args.b:
        shutil.copyfile(args.TARGET, args.TARGET + ".bak")
    apply(args.PATCH, args.TARGET)

if __name__ == "__main__":
    main()
