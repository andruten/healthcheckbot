from backends import SocketBackend, RequestBackend


class Service:
    BACKENDS = {
        'socket': SocketBackend,
        'request': RequestBackend,
    }

    def __init__(self, service_type: str, name: str, domain: str, port: int, enabled: bool = True) -> None:
        self.service_type = service_type
        self.name = name
        self.domain = domain
        self.port = port
        self.enabled = enabled

    @property
    def backend(self):
        return self.BACKENDS[self.service_type](self)

    def __repr__(self) -> str:
        return f'{self.name} <{self.domain}:{self.port}>'
