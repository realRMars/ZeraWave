class Renderer:
    def initialize(self):
        raise NotImplementedError

    def render(self, parameters):
        raise NotImplementedError

    def shutdown(self):
        raise NotImplementedError