class Service:

    def __init__(self, service_type: str, name: str, domain: str, port: int, enabled: bool = True) -> None:
        self.service_type = service_type
        self.name = name
        self.domain = domain
        self.port = port
        self.enabled = enabled
