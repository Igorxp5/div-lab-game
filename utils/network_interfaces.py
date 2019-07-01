import netifaces

def getAllIpAddress():
	interfaces = [netifaces.ifaddresses(i) for i in netifaces.interfaces()]
	interfaces = [ifaddress for ifaddress in interfaces if netifaces.AF_INET in ifaddress]
	interfaces = [address for ifaddress in interfaces for address in ifaddress[netifaces.AF_INET]]
	interfaces = [address['addr'] for address in interfaces]
	return interfaces