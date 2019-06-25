class Socket:
    def __init__(self, ip, port, connection):
        self.ip     = ip
        self.port   = port
        self.connection = connection

    def __str__(self):
        return f'{self.__class__.__name__}({self.ip}, {self.port})'

    def setIp(self, ip):
        self.ip = ip

    def setPort(self, port):
        self.port = port

    def getIp(self):
        return self.ip

    def getPort(self):
        return self.port