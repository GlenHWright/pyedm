# Copyright 2023 Canadian Light Source, Inc. See The file COPYRIGHT in this distribution for further information.
#
# when called by 'python -m pyedm', execute from here.
#
# MODULE LEVEL: top
#
from pyedm import pyedm_main
import sys

if __name__ == "__main__":
    if len(sys.argv) <= 1:
        pyedm_main(["-h"])
    else:
        pyedm_main(sys.argv[1:])

