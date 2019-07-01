from datetime import datetime
from threading import Thread, Event

class Countdown(Thread):
	def __init__(self, coutdownTime, callback, daemon=False):
		super().__init__(daemon=daemon)
		self._countdownTime = coutdownTime
		self._callback = callback
		self._cancelFlag = Event()
		self._finishFlag = Event()

	def run(self):
		startTime = datetime.now()
		while (not self._cancelFlag.is_set() and not self._finishFlag.is_set() and 
					(datetime.now() - startTime).seconds < self._countdownTime):
			pass
		if not self._cancelFlag.is_set():
			self._callback()

	def finish(self):
		self._finishFlag.set()

	def cancel(self):
		self._cancelFlag.set()

if __name__ == '__main__':
	def isUp():
		print('Countdown is up!')

	Countdown(3, isUp).start()
