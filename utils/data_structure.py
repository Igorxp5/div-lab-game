class IdTable:
	def __init__(self, get_id=None):
		self._data = {}
		self._sort_id = []
		self._size = 0
		if get_id is None:
			self._get_id = lambda item: item.id

	def __contains__(self, id_):
		return self._data in id_

	def __iter__(self):
		return iter((self._data[id_] for id_ in self._sort_id))

	def add(self, value):
		id_ = self._get_id(value)
		self._data[id_] = value
		self._sort_id[self._size]
		self._size += 1

	def get(self, id_):
		return self._data[id_]

	def index(self, id_):
		return self._sort_id.index(id_)

	def remove(self, id_):
		del self._data[id_]
		self._sort_id.remove(id_)
		self._size -= 1
