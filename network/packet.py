import uuid
import json

from .action import Action, ActionParam, InvalidActionParams

from enum import Enum

class InvalidPacketError(RuntimeError):
    def __init__(self, message=''):
        super().__init__(message)

class PacketType(Enum):
    REQUEST = 'DIVLABGAME-ACTION-REQUEST'
    RESPONSE = 'DIVLABGAME-ACTION-RESPONSE'

    def __str__(self):
        return self.value

    @staticmethod
    def getByValue(value):
        for packetType in PacketType:
            if value == packetType.value:
                return packetType
        raise NotImplementedError

class Packet:
    ENCODING = 'utf-8'

    def __init__(self, packetType, action, uuid=None):
        self.packetType = packetType
        self.action = action
        self.uuid = uuid

        if self.uuid is None:
            self.uuid = Packet.generateUUID()

    def __str__(self):
        data = f'{self.packetType}\r\n'
        data += f'REQUEST-UUID: {self.uuid}\r\n'
        data += f'ACTION-ID: {self.action.id}\r\n'
        return data

    def toBytes(self):
        return str(self).encode(Packet.ENCODING)

    @staticmethod
    def parse(data):
        packet = None

        message = data.decode(Packet.ENCODING)
        headers_content = message.split('\r\n\r\n')
        headers_lines = headers_content[0].split('\r\n')
        headers = headers_lines[1:]
        headers = [header for header in headers if header]
        headers = [header.split(': ') for header in headers]
        headers = {header: value for header, value in headers}
        packetType = PacketType.getByValue(headers_lines[0])

        try:
            action = Action.getById(int(headers['ACTION-ID']))

            uuid = headers['REQUEST-UUID']

            content = None
            if headers_content[1]:
                content = json.loads(headers_content[1])
                content = {ActionParam.getByValue(key): value for key, value in content.items()}
                content = {key: key(value) for key, value in content.items()}
            
            if packetType == PacketType.REQUEST:
                packet = PacketRequest(action, content, uuid=uuid)

                if not all([param in content for param in action.params]):
                    raise InvalidActionParams

            if packetType == PacketType.RESPONSE:
                approved = headers['APPROVED'] == 'True'
                packet = PacketResponse(action, approved, content, uuid=uuid)

        except NotImplementedError:
            raise InvalidPacketError

        return packet

    @staticmethod
    def generateUUID():
        return str(uuid.uuid1())

class PacketRequest(Packet):
    def __init__(self, action, params=None, uuid=None):
        super().__init__(PacketType.REQUEST, action, uuid)
        self.params = params

    def __str__(self):
        base = super().__str__()
        if self.params:
            params = {str(param): param(self.params[param]) for param in self.params.keys()}
            data = f'\r\n{json.dumps(params)}\r\n\r\n'
            return base + data
        return base + '\r\n'

class PacketResponse(Packet):
    def __init__(self, action, approved, content=None, uuid=None):
        super().__init__(PacketType.RESPONSE, action, uuid)
        self.approved = str(bool(approved))
        self.content = content

    def __str__(self):
        base = super().__str__()
        data = f'APPROVED: {self.approved}\r\n\r\n'
        if self.content:
            data += f'{json.dumps(self.content)}\r\n\r\n'
        return base + data
