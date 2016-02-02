import dis, sys, ast, types, marshal, struct, time

class Compiler():
    reverse_opcodes = {v:k for v,k in dis.opmap.iteritems()}
    reverse_opcodes[""] = reverse_opcodes["NOP"]

    def __init__(self, raw):
        self.raw = raw
        self.raw_ops = []
        self.ops = []
        self.constants = [None]
        self.names = []
        self.locals = []
        for num, line in enumerate(self.raw):
            if '#' in line:
                line = line[:line.index("#")]+ "\n"
            parts = line.split(' ')
            parts = [part.replace('%_', ' ') for part in parts]
            print num+1, " ".join(parts),
            opcode = Compiler.reverse_opcodes[parts[0].rstrip()]
            args = parts[-1].rstrip()
            op = [opcode]
            if opcode >= dis.HAVE_ARGUMENT:
                final_arg = 0
                if opcode in dis.hasconst: final_arg = self.load_const(args)
                elif opcode in dis.hasname: final_arg = self.load_name(args)
                elif opcode in dis.hasjrel: final_arg = self.load_jrel(args)
                elif opcode in dis.haslocal: final_arg = self.load_local(args)
                elif opcode in dis.hascompare: final_arg = self.load_compare(args)
                elif opcode in dis.hasjabs: final_arg = self.load_jabs(args)
                elif opcode == Compiler.reverse_opcodes["CALL_FUNCTION"]: final_arg = self.rtn_args(args)
                else: final_arg = int(args)
                op.extend([final_arg & 255, final_arg >> 8])
            self.raw_ops.append(op)
            self.ops.extend(op)
        self.func_obj = lambda: None
        self.code = types.CodeType(0,
                                  len(self.locals),
                                  3,
                                  0,
                                  "".join(map(chr, self.ops)),
                                  tuple(self.constants),
                                  tuple(self.names),
                                  tuple(self.locals), 
                                  "pyke_code",
                                  "pyke_code",
                                  1,
                                  "")
        print
        print `self.code.co_code`
        self.func = types.FunctionType(self.code, __builtins__.__dict__)

    def load_const(self, args): return self.load_generic(args, self.constants)
    def load_name(self, args): return self.load_generic(args, self.names, True)
    def load_local(self, args):  return self.load_generic(args, self.locals, True)
    def load_compare(self, args):
        return dis.cmp_op.index(args)
        
    def load_jrel(self, args):
        return self.load_jabs(args)-len(self.ops)-3
        
    def load_jabs(self, args):
        args = int(args)
        l = {True: 3, False: 1}
        return sum([
            l[
              Compiler.reverse_opcodes[line.rstrip().split(" ", 1)[0]] >= dis.HAVE_ARGUMENT
             ] for line in self.raw[:args-1]])

    def load_generic(self, args, store, literal = False):
        if literal: const = args
        else: const = ast.literal_eval(args)
        try:
            parsed_arg = store.index(const)
        except ValueError:
            parsed_arg = len(store)
            store.append(const)
        return parsed_arg

    def rtn_args(self, args):
        a,b = map(int, args.split(","))
        return a<<8 | b

file_ = open(sys.argv[1])
contents = file_.readlines()
file_.close()

c = Compiler(contents)
print len(c.code.co_code)
save_f = open(".".join(sys.argv[1].split(".")[:-1])+".pyc", "wb")
save_f.write("\x03\xf3\r\n")
save_f.write(struct.pack('I', time.time()))
marshal.dump(c.code, save_f)
print `marshal.dumps(c.code)`
save_f.close()
