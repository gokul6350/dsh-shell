from distutils.core import setup, Extension
import os

def main():
    setup(name="terminal_backend",
          version="1.0",
          ext_modules=[Extension("terminal_backend",
                               sources=["terminal_backend.c"],
                               libraries=["kernel32"])])

if __name__ == "__main__":
    main() 