"""Restore original driver refactoring policy after precise frontend lowering.

Only the precise component mask of instruction tokens is changed. All opcodes,
operands, constants and resource declarations remain compiler-generated.
Token mask source: Microsoft DirectX-Headers D3D12TokenizedProgramFormat.hpp.
"""
import ctypes as C
import struct
from dxbc_tools import disassemble
MASK=0x00780000

def repair_checksum(data,helper_path):
    helper=C.CDLL(str(helper_path));fn=helper.RepairDxbc;fn.argtypes=[C.c_void_p,C.c_uint];fn.restype=C.c_int
    blob=C.create_string_buffer(bytes(data));assert fn(blob,len(data))==1
    return blob.raw[:len(data)]

def restore_driver_refactoring(code,helper_path):
    original=disassemble(code);expected=original.count('[precise')
    data=bytearray(code);count=struct.unpack_from('<I',data,28)[0];changed=0
    for i in range(count):
        offset=struct.unpack_from('<I',data,32+4*i)[0]
        if data[offset:offset+4] not in (b'SHEX',b'SHDR'):continue
        length=struct.unpack_from('<I',data,offset+4)[0];begin=offset+8
        words=struct.unpack_from('<I',data,begin+4)[0];assert words*4==length
        position=2
        while position<words:
            token=struct.unpack_from('<I',data,begin+4*position)[0];opcode=token&0x7ff
            size=struct.unpack_from('<I',data,begin+4*(position+1))[0] if opcode==53 else ((token>>24)&0x7f)
            assert size>0 and position+size<=words
            if opcode!=53 and token&MASK:
                struct.pack_into('<I',data,begin+4*position,token&~MASK);changed+=1
            position+=size
        assert position==words
    assert changed==expected,(changed,expected)
    result=repair_checksum(data,helper_path)
    assert '[precise' not in disassemble(result)
    return result,changed
