from conjureup import utils
from conjureup import controllers


class BootstrapWaitController:
    def finish(self):
        controllers.use('deploystatus').render()

    def render(self):
        utils.info("Waiting for bootstrap to finish")
        self.finish()


_controller_class = BootstrapWaitController
