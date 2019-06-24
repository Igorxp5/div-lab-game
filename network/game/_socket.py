class Socket:
    def __init__(self, ip, port, connection):
        self.ip     = ip
        self.port   = port
        self.connection = connection

    def setIp(self, ip):
        self.ip = ip

    def setPort(self, port):
        self.port = port

    def getIp(self):
        return self.ip

    def getPort(self):
        return self.port