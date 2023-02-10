from  pyedm import pyedm_main
import sys

if __name__ == "__main__":
    if len(sys.argv) <= 1:
        pyedm_main(["-h"])
    else:
        pyedm_main(sys.argv[1:])
