#/usr/bin/env python

# Sked. (c) 2006 Alexandre Erwin Ittner <aittner@netuno.com.br>
# Distributed under the GNU GPL v2 or later. WITHOUT ANY WARRANTY.

# Prints the hashes/IVs from Sked database entries as hexadecimal strings
# for out of box decryption with OpenSSL utilities.


import sys
import struct

if __name__ == "__main__":
    if len(sys.argv) > 1:
        fname = sys.argv[0]
        fp = open(fname, "rb")
        binhash = fp.read(16)
        fp.close()
        if len(binhash) == 16:
            str = fname + ": "
            for i in range(0, 16):
                str += "%x" % struct.unpack("B", binhash[i])
            print str
            sys.exit(0)
        else:
            print "Error! Bad data found."
    else:
        print "Usage: printhash <filename>"
    sys.exit(1)
