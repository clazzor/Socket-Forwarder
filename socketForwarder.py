#!/usr/bin/env python3
import sys, socket, time, logging
from threading import Thread

logging.getLogger('').setLevel(logging.DEBUG) 

class HostConvertor:
    def __init__(self, host: str) -> None:
        self.host = host
        self.isValid = True
        self.port = self.address = None

        self.hostSeperate()
        if self.isValid: 
            self.isValidAddress()
            self.isValidPort()

    def isValidPort(self) -> None:
        if(0 < self.port and self.port <= 65535): return
        logging.error(f' Port is out of bounds - "{self.host}"!')
        self.isValid = False

    def isValidAddress(self) -> None:
        try:
            socket.gethostbyname(self.address)
            return
        except:
            logging.error(f' Invalid address - "{self.host}"!')
            self.isValid = False

    def hostSeperate(self) -> None:
        try:
            _host = self.host.split(':')
            if len(_host) != 2: raise Exception
            self.port = int(_host[1])
            self.address = _host[0]
        except:
            logging.error(f' Invalid format of host - "{self.host}"!')
            self.isValid = False


class Sessioner:
    def __init__(self, role: str, address: str, port: int) -> None:
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.isConnect = False
        self.role = role
        self.textHost = f"{address}:{port}"
        self.host = (address, port)

    def _close(self) -> None:
        self.socket.close()
        logging.info(f' {self.role} target {self.textHost} is shutting down.')
        sys.exit(0)

    def _connect(self) -> None:
        try:
            self.socket.connect(self.host)
            self.isConnect = True
        except KeyboardInterrupt:
            self._close()
        except:
            self.isConnect = False

    def _reconnect(self) -> None:
        self.isConnect = False
        self.socket.close()
        self.socket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        
        logging.warning(f' {self.role} target {self.textHost} disconnect, trying reconnecting.')
        while not self.isConnect:
            self._connect()
            time.sleep(1.5)
        logging.info(f' {self.role} target {self.textHost} is back online!')
        
    def connect(self) -> None:
        self._connect()
        if self.isConnect:
            logging.info(f' {self.role} target {self.textHost} is connected.')
        else:
            logging.error(f' Could connect to {self.role.lower()} {self.textHost}')
            self.reconnect() 
    
    def reconnect(self) -> None:
        if(self.role == "Source"):
            self._reconnect()
        else:
            Thread(target=self._reconnect).start()

    def sendData(self, data: bytes) -> None:
        try:
            self.socket.sendall(data)
        except KeyboardInterrupt:
            self._close()
        except:
            self.reconnect()

    def recvData(self, size: int) -> bytes:
        try:
            data = self.socket.recv(size)
            if not data: raise Exception
            return data
        except KeyboardInterrupt:
            self._close()
        except:
            self.reconnect()        


class DataForwarder:
    def __init__(self, hosts: list[str]) -> None:
        isWithourErr = True
        self.hosts = []

        for i, host in enumerate(hosts):
            _host = HostConvertor(host)
            if not _host.isValid:
                isWithourErr = False
                continue
            self.hosts.append(Sessioner("Source" if i == 0 else "Destination", _host.address, _host.port))
        if not isWithourErr: sys.exit(1)

    def makeConnections(self) -> None:
        logging.info(' Everything ready, starting . .')
        for host in self.hosts:
            host.connect()

    def forwarding(self) -> None:
        while True:
            data = self.hosts[0].recvData(1024)
            for host in self.hosts[1:]:
                if host.isConnect:
                    host.sendData(data)
            

def info():
    if len(sys.argv) < 3:
        if len(sys.argv) > 1: logging.error(f' Not enough arguments!')
        print(f'Usage: {sys.argv[0]} <source:port> <destination:port> [other destination . .]\n' +
                '       Source & Destination must be IPv4 or domain, with define port.\n' +
                '       Number of destination is not limited.')
        sys.exit(0)

def main():
    forwarder = DataForwarder(sys.argv[1:])
    forwarder.makeConnections()
    forwarder.forwarding()

if __name__ == '__main__':
    info()
    main()
