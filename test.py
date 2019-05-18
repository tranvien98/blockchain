import threading
import time

def gfg():
    print("Hello\n")


timer = threading.Timer(10.0, gfg)
timer.start()
print("Exit\n")
