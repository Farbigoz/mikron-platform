import os

from typing import Union, Dict

from platformio.platform.base import PlatformBase
from platformio.platform.board import PlatformBoardConfig


# class MIKRON-npcprom
class MikronnpcpromPlatform(PlatformBase):
    def configure_default_packages(self, variables: dict, targets: str):

        return super().configure_default_packages(variables, targets)

    def get_boards(self, id_:Union[None, str, Dict[str, PlatformBoardConfig]]=None):
        result: PlatformBoardConfig = super().get_boards(id_)

        if not result:
            return result

        if isinstance(result, PlatformBoardConfig):
            self._add_default_debug_tools(result)

        else:
            for key in result:
                self._add_default_debug_tools(result[key])

        return result

    def _add_default_debug_tools(self, board: PlatformBoardConfig):
        # Package path
        sdk_path = self.get_package_dir('sdk-mikron-npcprom')
        openocd_path = self.get_package_dir('tool-openocd-riscv')

        # Resources path
        openocd_scripts_path = os.path.join(openocd_path, "share/openocd/scripts")
        openocd_target_path = os.path.join(sdk_path, "openocd/scripts/target", f"{board.get('build.mcu')}.cfg")
        openocd_include_eeprom_path = os.path.join(sdk_path, "openocd/scripts", "include_eeprom.tcl")

        # Supported upload and debug tools
        upload_tools = board.get("upload.protocols")
        debug_tools = board.get("debug.onboard_tools")

        # Init upload tools
        for targetName, tools in [("upload", upload_tools), ("debug", debug_tools)]:
            target = board.get(targetName)
            if "tools" not in target:
                target["tools"] = {}
            
            for tool in tools:
                if tool in target["tools"]:
                    continue

                # ?
                if tool in (None, ):
                    pass

                # FTDI and Jlink
                else:
                    if tool in ("m-link", ):
                        openocd_interface = os.path.join(sdk_path, f"openocd/scripts/interface/ftdi/{tool}.cfg")
                    elif tool in ("jlink", ):
                        openocd_interface = os.path.join(openocd_scripts_path, f"interface/{tool}.cfg")
                    else:
                        openocd_interface = os.path.join(openocd_scripts_path, f"interface/ftdi/{tool}.cfg")

                    if tool in ("xds100v2", ):
                        extra_args = ["-c", "ftdi_set_signal PWR_RST 1", "-c", "jtag arp_init"]
                    else:
                        extra_args = []


                    target["tools"][tool] = {
                        "server": {
                            "package": "tool-openocd-riscv",
                            "executable": "bin/openocd",
                            "arguments": [
                                "-f",
                                os.path.abspath(openocd_interface),
                                "-c",
                                f"adapter_khz {board.get('upload.speed')}",
                                "-f",
                                os.path.abspath(openocd_target_path),
                                "-f",
                                os.path.abspath(openocd_include_eeprom_path),
                                *extra_args
                            ]
                        }
                    }

        return board
        