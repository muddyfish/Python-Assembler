#!/usr/bin/env python
import sys, dis, marshal, json
from opcode import *

class Opcode(object):
    def __init__(self, id, arg, kwargs):
        self.id = id
        self.opname = opname[self.id]
        self.arg = arg
        self.kwargs = kwargs
        
    def __repr__(self):
        return self.opname+repr(self.kwargs)

class TupleAssembler(object):
    def __init__(self, disassembly):
        self.disassembly = disassembly
        consts = self.disassembly.consts
        names = self.disassembly.names
        varnames = self.disassembly.varnames
        opcodes = tuple([(opcode.id, opcode.arg)for opcode in self.disassembly.opcodes])
        code = (consts, names, varnames, opcodes)
        print code

class JsonAssembler(object):
    def __init__(self, disassembly):
        self.disassembly = disassembly
        consts = map(repr, self.disassembly.consts)
        names = self.disassembly.names
        varnames = self.disassembly.varnames
        opcodes = [{"name": opcode.opname, "arg": opcode.arg}for opcode in self.disassembly.opcodes]
        code = {"consts": consts, "names": names, "varnames": varnames, "opcodes": opcodes}
        print json.dumps(code, indent = 2)

class PykeAssembler(object):
    def __init__(self, disassembly):
        self.disassembly = disassembly
        consts = map(repr, self.disassembly.consts)
        names = self.disassembly.names
        varnames = self.disassembly.varnames
        for opcode in self.disassembly.opcodes:
            print opcode.opname.ljust(19),
            if "const" in opcode.kwargs:
                print repr(opcode.kwargs["const"])
            elif "name" in opcode.kwargs:
                print opcode.kwargs["name"]
            elif "local" in opcode.kwargs:
                print opcode.kwargs["local"]
            elif "compare" in opcode.kwargs:
                print opcode.kwargs["compare"]
            elif opcode.id in hasjabs:
                oplens = [1+(op.arg != None)*2 for op in self.disassembly.opcodes]
                totlens = [sum(oplens[:i])for i in range(len(oplens))]
                print totlens.index(opcode.arg)+1
            else:
                if opcode.arg is not None: print opcode.arg
                else: print


class CodeDissasembler(object):
    def __init__(self, code_obj):
        self.code_obj = code_obj
        self.consts = self.code_obj.co_consts
        self.names = self.code_obj.co_names
        self.varnames = self.code_obj.co_varnames
        self.opcodes = self.get_opcodes()
        self.optimise_consts()

    def get_opcodes(self):
        opcodes = []
        i = 0
        code_str = self.code_obj.co_code
        while i!=len(code_str):
            op = ord(code_str[i])
            i+=1
            arg = None
            kwargs = {}
            if op >= HAVE_ARGUMENT:
                arg = ord(code_str[i]) + ord(code_str[i+1])*256
                i+=2
                if op in hasconst:
                    kwargs["const"] = self.consts[arg]
                if op in hasname:
                    kwargs["name"] = self.names[arg]
                if op in haslocal:
                    kwargs["local"] = self.varnames[arg]
                if op in hascompare:
                    kwargs["compare"] = cmp_op[arg]
            opcodes.append(Opcode(op, arg, kwargs))
        return opcodes
    
    def optimise_consts(self):
        const_map = []
        for opcode in self.opcodes:
            if opcode.id in hasconst:
                const = opcode.kwargs["const"]
                if const not in const_map:
                    const_map.append(const)
                opcode.arg = const_map.index(const)
        self.consts = tuple(const_map)

with open(sys.argv[1], "rb") as code_f:
    code_f.read(8) # Magic number and modification time
    code = marshal.load(code_f)
    PykeAssembler(CodeDissasembler(code))