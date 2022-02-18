from  pyedm import pyedm_main
import sys

if __name__ == "__main__":
    del sys.argv[0]
    if len(sys.argv) == 0:
        sys.argv = [ "-h" ]
    pyedm_main(sys.argv)
