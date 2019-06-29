import json

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

class JsonSerializable:
	def toJson(self, *args, **kwargs):
		return json.dumps(
			self._toJsonDict(), default=JsonSerializable._defaultSerialize, *args, **kwargs
		)

	def _toJsonDict(self):
		try:
			keyProperty = self._dictKeyProperty().items()
			return {key: JsonSerializable._propertyToJsonDict(value) for key, value in keyProperty}
		except NotImplementedError:
			return self

	def _dictKeyProperty(self):
		raise NotImplementedError

	def _basicValue(self):
		raise NotImplementedError		

	@staticmethod
	def _defaultSerialize(obj):
		return obj._basicValue()

	@staticmethod
	def _propertyToJsonDict(property_):
		if property_ is None:
			return None

		if isinstance(property_, dict):
			result = {}
			for key, value in property_.items():
				result[key] = JsonSerializable._propertyToJsonDict(value)
			return result
		
		elif isinstance(property_, JsonSerializable):
			return property_._toJsonDict()
		elif (isinstance(property_, bool) or 
				isinstance(property_, str) or 
				isinstance(property_, int) or
				isinstance(property_, complex)):
			return property_
		else:
			try:
				result = []
				for subProperty in property_:
					result.append(JsonSerializable._propertyToJsonDict(subProperty))
				return result
			except:
				return property_
