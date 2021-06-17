#!/usr/bin/python
from subprocess import Popen
import sys

device = filename = sys.argv[1]
while True:
    print("\nStarting Meater connection to " + device + ".....................")
    p = Popen("python ./readMeater.py " + device, shell=True)
    p.wait()
