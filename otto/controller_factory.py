from otto.ryu.ryu_environment import RyuEnvironment


class ControllerFactory:

    @staticmethod
    def get_controller(controller: str):

        match controller:
            case "ryu":
                return RyuEnvironment()

            case _:
                pass
