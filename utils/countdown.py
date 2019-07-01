import time
from datetime import datetime
from threading import Thread

class Countdown(Thread):
	def __init__(self, coutdownTime, callback, daemon=False):
		super().__init__(daemon=daemon)
		self._countdownTime = coutdownTime
		self._callback = callback

	def run(self):
		time.sleep(self._countdownTime)
		self._callback()

def isUp():
	print('Countdown is up!')

if __name__ == '__main__':
	Countdown(3, isUp).start()
