import os
import json

from SCons.Script import (
    AlwaysBuild,
    ARGUMENTS,
    Builder, 
    COMMAND_LINE_TARGETS, 
    Default, 
    DefaultEnvironment
)

env = DefaultEnvironment()
platform = env.PioPlatform()
board_config = env.BoardConfig()


env.Replace(
    AR="riscv64-unknown-elf-gcc-ar",
    AS="riscv64-unknown-elf-as",
    CC="riscv64-unknown-elf-gcc",
    GDB="riscv64-unknown-elf-gdb",
    CXX="riscv64-unknown-elf-g++",
    OBJCOPY="riscv64-unknown-elf-objcopy",
    RANLIB="riscv64-unknown-elf-gcc-ranlib",
    SIZETOOL="riscv64-unknown-elf-size",

    ARFLAGS=["rc"],

    SIZEPRINTCMD='$SIZETOOL -d $SOURCES',

    PROGSUFFIX=".elf"
)

if env.get("PROGNAME", "program") == "program":
    env.Replace(PROGNAME="firmware")

env.Append(
    BUILDERS=dict(
        ElfToHex=Builder(
            action=env.VerboseAction(" ".join([
                "$OBJCOPY",
                "-O",
                "ihex",
                "$SOURCES",
                "$TARGET"
            ]), "Building $TARGET"),
            suffix=".hex"
        )
    )
)


#
# Target: Build executable and linkable firmware
#
#for framework in board_config.get("frameworks", []):
#    framework_handler_path: str = platform.frameworks[framework]["script"]
#    env.SConscript(os.path.join(platform.get_dir(), framework_handler_path), exports={"env": env})
env.SConscript(f"boards/{board_config.get('build.mcu')}.py", exports={"env": env})


target_elf = None
if "nobuild" in COMMAND_LINE_TARGETS:
    target_elf = os.path.join("$BUILD_DIR", "${PROGNAME}.elf")
    target_hex = os.path.join("$BUILD_DIR", "${PROGNAME}.hex")
else:
    target_elf = env.BuildProgram()
    target_hex = env.ElfToHex(os.path.join("$BUILD_DIR", "${PROGNAME}"), target_elf)

    env.Depends(target_hex, "checkprogsize")


AlwaysBuild(env.Alias("nobuild", target_hex))
target_buildprog = env.Alias("buildprog", target_hex, target_hex)


#
# Target: Print binary size
#

target_size = env.Alias(
    "size", target_elf,
    env.VerboseAction("$SIZEPRINTCMD", "Calculating size $SOURCE"))
AlwaysBuild(target_size)


#
# Target: Upload by default .bin file
#

if set(["debug", "__debug"]) & set(COMMAND_LINE_TARGETS):
    upload_tools = board_config.get("debug.tools", {})
else:
    upload_tools = board_config.get("upload.tools", {})

upload_protocol = env.subst("$UPLOAD_PROTOCOL")
upload_actions = []
upload_target = target_hex


# Upload server args
uploader = "openocd"
tool_args = [
    "-c",
    "debug_level %d" % (2 if int(ARGUMENTS.get("PIOVERBOSE", 2)) else 1)
]
tool_args.extend(
    upload_tools.get(upload_protocol).get("server").get("arguments", []))


# Set upload speed
if env.GetProjectOption("upload_speed"):
    old_adapter_speed = f"adapter_khz {board_config.get('upload.speed')}"
    if old_adapter_speed in tool_args:
        tool_args[tool_args.index(old_adapter_speed)] = f"adapter_khz {env.GetProjectOption('upload_speed')}"


# Upload programm path
if isinstance(target_hex, str):
    hex_path = target_hex.replace('\\', '/')
else:
    hex_path = target_hex[0].rstr().replace('\\', '/')

image_offset = board_config.get("upload.image_offset", "0x0")


# upload method
ldscript = board_config.get("build.ldscript")
if ldscript == "eeprom":
    flash_command = f"eeprom_write_file {hex_path}"
else:
    flash_command = f"load_image {hex_path} {image_offset} ihex"

tool_args.extend(
    [
        "-c", "reset halt",
        "-c", flash_command,
        "-c", f"resume {image_offset}",
        "-c", "shutdown"
    ]
)

env.Replace(
    UPLOADER=uploader,
    UPLOADERFLAGS=tool_args,
    UPLOADCMD="$UPLOADER $UPLOADERFLAGS"
)
upload_actions = [env.VerboseAction("$UPLOADCMD", "Uploading $SOURCE")]

AlwaysBuild(env.Alias("upload", upload_target, upload_actions))

#
# Setup default targets
#

Default([target_buildprog, target_size])
