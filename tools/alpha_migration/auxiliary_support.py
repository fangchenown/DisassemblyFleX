"""Shared build wiring for preserved derived shaders; never changes original84."""
from common import *
def configure(destination,entries):
    source=destination/'shaders/auxiliary';source.mkdir(exist_ok=True)
    path=source/'registry.json'
    registry=read(path) if path.exists() else [dict(name='df_BuildSpringDispatchArgs',source='SpringDispatchArgs.hlsl',label='BuildSpringDispatchArgs',kind='authored-integer-helper')]
    names={x['name'] for x in entries};registry=[x for x in registry if x['name'] not in names]+entries;write(path,registry)
    shutil.copy2(Path(__file__).parent/'templates/build_aux_registry.py',destination/'tools/build_aux_shaders.py')
    cmake=destination/'CMakeLists.txt';text=cmake.read_text(encoding='utf8');start=text.index('add_custom_command(OUTPUT "${CMAKE_BINARY_DIR}/generated/NvFlexAuxShaders.generated.cpp"');end=text.index('file(GLOB_RECURSE restored_sources',start)
    # A previous registry composition may already have this glob immediately
    # before the command. Keep only one to make repeated composition stable.
    glob='file(GLOB auxiliary_shader_sources CONFIGURE_DEPENDS "${CMAKE_CURRENT_SOURCE_DIR}/shaders/auxiliary/*.hlsl" "${CMAKE_CURRENT_SOURCE_DIR}/shaders/auxiliary/*.smasm")\n'
    if text[:start].endswith(glob):start-=len(glob)
    block=glob+'''add_custom_command(OUTPUT "${CMAKE_BINARY_DIR}/generated/NvFlexAuxShaders.generated.cpp"
  "${CMAKE_BINARY_DIR}/generated/NvFlexAuxShaders.generated.hpp" "${CMAKE_BINARY_DIR}/generated/aux_shader_manifest.json"
  COMMAND "${Python3_EXECUTABLE}" "${CMAKE_CURRENT_SOURCE_DIR}/tools/build_aux_shaders.py"
    --source "${CMAKE_CURRENT_SOURCE_DIR}/shaders/auxiliary/SpringDispatchArgs.hlsl"
    --output "${CMAKE_BINARY_DIR}/generated" --compiler "${DISASSEMBLYFLEX_SHADER_COMPILER_DLL}"
    --hash-helper "$<TARGET_FILE:DisassemblyDxbcHash>"
  DEPENDS ${auxiliary_shader_sources} shaders/auxiliary/registry.json tools/build_aux_shaders.py
    tools/dxbc_tools.py tools/dxbc_assembler.py tools/shader_lowering.py DisassemblyDxbcHash VERBATIM)
'''
    cmake.write_text(text[:start]+block+text[end:],encoding='utf8')
