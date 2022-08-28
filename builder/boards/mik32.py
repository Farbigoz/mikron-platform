import os

from SCons.Script import Import, DefaultEnvironment

Import("env")
env: DefaultEnvironment

platform = env.PioPlatform()
board_config = env.BoardConfig()

env.Replace(
    ASFLAGS=[
        "-x", "assembler-with-cpp",
        "-Wa,-march=%s" % board_config.get("build.march")
    ],

    CCFLAGS=[
        "-Os",
        "-Wall",  # show warnings
        "-march=%s" % board_config.get("build.march"),
        "-mabi=%s" % board_config.get("build.mabi"),
        "-mcmodel=%s" % board_config.get("build.mcmodel")
    ],

    LINKFLAGS=[
        "-Os",
        "-ffunction-sections",
        "-fdata-sections",
        "-nostartfiles",
        "-march=%s" % board_config.get("build.march"),
        "-mabi=%s" % board_config.get("build.mabi"),
        "-mcmodel=%s" % board_config.get("build.mcmodel"),
        "-nostdlib",
        # "--specs=nano.specs",
        "-Wl,--gc-sections"
    ],

    LIBS=["c"],
)

# copy CCFLAGS to ASFLAGS (-x assembler-with-cpp mode)
env.Append(ASFLAGS=env.get("CCFLAGS", [])[:])


sdk_path = platform.get_package_dir("sdk-mikron-npcprom")
sdk_mcu_path = os.path.join(sdk_path, "mik32")
sdk_ldscripts_path = os.path.join(sdk_mcu_path, "ldscripts")
sdk_runtime_path = os.path.join(sdk_mcu_path, "runtime")


if not os.path.isfile(os.path.join(sdk_runtime_path, 'build', 'core_startup.o')):
    env.BuildSources(
        os.path.join(sdk_runtime_path, 'build'),
        src_dir=sdk_runtime_path
    )

if not os.path.isfile(os.path.join(sdk_runtime_path, 'build', 'core_irq.o')):
    env.BuildSources(
        os.path.join(sdk_runtime_path, 'build'),
        src_dir=sdk_runtime_path
    )


debug = board_config.get('debug')

ldscript = board_config.get("build.ldscript")
ldscript_path = os.path.join(sdk_ldscripts_path, f"{ldscript}.ld")


env.Replace(LDSCRIPT_PATH=ldscript_path)


env.AppendUnique(
    CPPPATH=[
        '-v',
        "$PROJECT_SRC_DIR",
        os.path.join(sdk_mcu_path, "include"),
        os.path.join(sdk_mcu_path, "periphery"),
    ],
    LINKFLAGS=[
        "-nostartfiles",
        os.path.join(sdk_runtime_path, 'build', 'core_startup.o'),
        os.path.join(sdk_runtime_path, 'build', 'core_irq.o'),
        '-v'
    ],
    LIBSOURCE_DIRS=[
    ]
)