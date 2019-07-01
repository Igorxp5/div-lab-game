import json


class JsonSerializable:
	def toJson(self, *args, **kwargs):
		return json.dumps(
			self.toJsonDict(), default=JsonSerializable._defaultSerialize, *args, **kwargs
		)

	def toJsonDict(self):
		try:
			keyProperty = self._dictKeyProperty().items()
			return {key: JsonSerializable._propertyToJsonDict(value) for key, value in keyProperty}
		except NotImplementedError:
			return JsonSerializable._defaultSerialize(self)

	def _dictKeyProperty(self):
		raise NotImplementedError

	def _basicValue(self):
		raise NotImplementedError

	@classmethod
	def parseJson(cls, jsonData, *args, **kwargs):
		jsonDict = json.loads(jsonData)
		return cls._parseJson(jsonDict, *args, **kwargs)

	@staticmethod
	def _parseJson(jsonDict, *args, **kwargs):
		raise NotImplementedError

	@staticmethod
	def _defaultSerialize(obj):
		try:
			return obj._basicValue()
		except NotImplementedError:
			return self

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
			return property_.toJsonDict()
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
