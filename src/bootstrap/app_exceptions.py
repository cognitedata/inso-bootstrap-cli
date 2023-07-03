# '''
#                                              888    d8b
#                                              888    Y8P
#                                              888
#   .d88b.  888  888  .d8888b .d88b.  88888b.  888888 888  .d88b.  88888b.  .d8888b
#  d8P  Y8b `Y8bd8P' d88P"   d8P  Y8b 888 "88b 888    888 d88""88b 888 "88b 88K
#  88888888   X88K   888     88888888 888  888 888    888 888  888 888  888 "Y8888b.
#  Y8b.     .d8""8b. Y88b.   Y8b.     888 d88P Y88b.  888 Y88..88P 888  888      X88
#   "Y8888  888  888  "Y8888P "Y8888  88888P"   "Y888 888  "Y88P"  888  888  88888P'
#                                     888
#                                     888
#                                     888
# '''
class BootstrapConfigError(Exception):
    """Exception raised for config parser

    Attributes:
        message -- explanation of the error
    """

    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


class BootstrapValidationError(Exception):
    """Exception raised for config validation

    Attributes:
        message -- explanation of the error
    """

    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)
