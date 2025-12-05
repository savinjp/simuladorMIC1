import tkinter as tk
from tkinter import ttk, font, filedialog, messagebox

# 1. BACKEND 

class StackOverflow(Exception): pass
class StackUnderflow(Exception): pass

class MIC1Simulator:
    def __init__(self):
        self.tamanhoDaMemoria = 4096
        self.memoria = [0] * self.tamanhoDaMemoria

        # Registradores
        self.pc = 0 
        self.ac = 0 
        self.sp = self.tamanhoDaMemoria - 1 
        self.mar = 0 
        self.mbr = 0 
        self.ir = 0 
        
        # Flags
        self.zero_flag = False
        self.negative_flag = False

        # Instruções
        self.instructions = {
            0x00: ("HALT", self.halt),
            0x01: ("LODD", self.load),   # Load Direct (Lê da memória)
            0x02: ("STOD", self.store),  # Store Direct (Grava na memória)
            0x03: ("ADDD", self.add),    # Add Direct
            0x04: ("SUBD", self.sub),    # Sub Direct
            0x05: ("JPOS", self.jpos),
            0x06: ("STODL", self.stodl),
            0x07: ("LOCO", self.lodcons), # Load Constant (Imediato)
            0x08: ("JUMP", self.jump),
            0x09: ("JZER", self.jumpZERO),
            0x0A: ("JNEG", self.jneg),
            0x0B: ("ADDL", self.addl),
            0x0C: ("INSP", self.insp),
            0x0D: ("PUSH", self.push),
            0x0E: ("POP", self.pop),
            0x0F: ("INS", self.ins_dummy),
            0x10: ("OUT", self.out_dummy),
        }

        self.rodando = False 

    # --- Métodos de Memória ---
    def lerMemoria(self, endereco):
        if 0 <= endereco < self.tamanhoDaMemoria: return self.memoria[endereco]
        raise ValueError(f"Endereço inválido: {endereco}")

    def escreveNaMemoria(self, endereco, valor):
        if 0 <= endereco < self.tamanhoDaMemoria: self.memoria[endereco] = valor & 0xFFFF
        else: raise ValueError(f"Endereço inválido: {endereco}")

    def operacaoPUSH(self, valor):
        self.escreveNaMemoria(self.sp, valor)
        self.sp -= 1
        if self.sp < 0: raise StackOverflow("Estouro de pilha")

    def operacaoPOP(self):
        self.sp += 1
        if self.sp >= self.tamanhoDaMemoria: raise StackUnderflow("Underflow de pilha")
        return self.lerMemoria(self.sp)

    # --- INSTRUÇÕES CORRIGIDAS ---

    def halt(self): self.rodando = False

    def load(self): # LODD: Carrega o valor que está no endereço X
        end_operando = self.lerMemoria(self.pc) # Lê o endereço (ex: 50)
        self.mar = end_operando
        self.mbr = self.lerMemoria(self.mar)    # Vai na memória[50] pegar o valor
        self.ac = self.mbr
        self.pc += 1
        self.atualizaFlag(self.ac)

    def store(self): # STOD: Salva AC no endereço X
        end_operando = self.lerMemoria(self.pc) # Lê o endereço alvo
        self.mar = end_operando
        self.mbr = self.ac
        self.escreveNaMemoria(self.mar, self.mbr) # Grava AC na memória
        self.pc += 1

    def add(self): # ADDD: Soma ao AC o valor que está no endereço X
        end_operando = self.lerMemoria(self.pc) # Lê o endereço
        self.mar = end_operando
        val = self.lerMemoria(self.mar)         # Busca o valor real
        self.ac += val
        self.pc += 1
        self.atualizaFlag(self.ac)

    def sub(self): # SUBD: Subtrai do AC o valor que está no endereço X
        end_operando = self.lerMemoria(self.pc)
        self.mar = end_operando
        val = self.lerMemoria(self.mar)
        self.ac -= val
        self.pc += 1
        self.atualizaFlag(self.ac)

    def lodcons(self): # LOCO: Carrega a constante (Imediato) - MANTIDA
        val_imediato = self.lerMemoria(self.pc)
        self.ac = val_imediato
        self.pc += 1
        self.atualizaFlag(self.ac)

    # --- Demais instruções (Pulos e Pilha) ---
    def jpos(self):
        dest = self.lerMemoria(self.pc)
        if not self.negative_flag and not self.zero_flag: self.pc = dest
        else: self.pc += 1

    def jump(self):
        dest = self.lerMemoria(self.pc)
        self.pc = dest

    def jumpZERO(self):
        dest = self.lerMemoria(self.pc)
        if self.zero_flag: self.pc = dest
        else: self.pc += 1

    def jneg(self):
        dest = self.lerMemoria(self.pc)
        if self.negative_flag: self.pc = dest
        else: self.pc += 1

    def stodl(self): # STODL (Lógica mantida do original: OR bitwise?)
        end_operando = self.lerMemoria(self.pc)
        self.mar = end_operando
        val = self.lerMemoria(self.mar)
        self.ac |= val
        self.pc += 1
        self.atualizaFlag(self.ac)

    def addl(self):
        self.mar = self.sp; self.mbr = self.lerMemoria(self.mar); self.ac += self.mbr; self.pc += 1; self.atualizaFlag(self.ac)
    def insp(self):
        self.sp += 1; self.pc += 1; self.atualizaFlag(self.sp)
    def push(self):
        self.operacaoPUSH(self.ac); self.pc += 1
    def pop(self):
        self.ac = self.operacaoPOP(); self.pc += 1; self.atualizaFlag(self.ac)
    def ins_dummy(self): pass
    def out_dummy(self): pass

    # --- Ciclo de Execução ---
    def atualizaFlag(self, valor):
        self.zero_flag = (valor == 0)
        self.negative_flag = (valor < 0)

    def fetch(self):
        if self.pc >= self.tamanhoDaMemoria:
            self.rodando = False; return
        # Pega a instrução
        self.ir = self.lerMemoria(self.pc)
        self.pc += 1

    def decode(self):
        return self.instructions.get(self.ir, None)

    def execute(self, instrucao):
        if instrucao: instrucao[1]()

    def run_step(self):
        if not self.rodando: return False
        try:
            self.fetch()
            instrucao = self.decode()
            if instrucao:
                self.execute(instrucao)
                return True
            else:
                # Se for 0 (HALT implicito ou memória vazia) para
                if self.ir == 0: 
                    self.rodando = False
                    return False
                raise ValueError(f"Opcode desconhecido: {self.ir}")
        except Exception as e:
            raise e

    def get_next_instruction_name(self):
        if self.pc < self.tamanhoDaMemoria:
            opcode = self.lerMemoria(self.pc)
            if opcode in self.instructions:
                return self.instructions[opcode][0]
        return "---"

    def load_program(self, programa):
        self.memoria = [0] * self.tamanhoDaMemoria
        for addr, valor in enumerate(programa):
            self.escreveNaMemoria(addr, valor)
        self.reset()
        
    def reset(self):
        self.pc = 0
        self.ac = 0
        self.sp = self.tamanhoDaMemoria - 1
        self.mar = 0
        self.mbr = 0
        self.ir = 0
        self.zero_flag = False
        self.negative_flag = False
        self.rodando = True



class Mic1ViewerRunner:
    def __init__(self, root):
        self.root = root
        self.root.title("Simulador MIC-1 - Final")
        self.root.geometry("1100x720") 
        
        self.backend = MIC1Simulator()
        self.is_running = False

        self.code_font = font.Font(family="Consolas", size=11)
        self.ui_style = ttk.Style(); self.ui_style.theme_use('clam')

        # TOPO
        top_frame = tk.Frame(root, bg="#ddd", pady=10)
        top_frame.pack(fill=tk.X)
        tk.Button(top_frame, text="📂 Carregar Arquivo", font=("Arial", 11, "bold"), bg="#4a90e2", fg="white", command=self.load_file).pack(side=tk.LEFT, padx=20)
        self.lbl_filename = tk.Label(top_frame, text="...", bg="#ddd", font=("Arial", 10, "italic"))
        self.lbl_filename.pack(side=tk.LEFT, padx=10)

        # CENTRO
        self.main_pane = tk.PanedWindow(root, orient=tk.HORIZONTAL, sashrelief=tk.RAISED)
        self.main_pane.pack(fill=tk.BOTH, expand=True)

        # Esquerda (Código)
        self.left_frame = tk.Frame(self.main_pane, bg="white")
        self.main_pane.add(self.left_frame, width=500)
        self.line_numbers = tk.Text(self.left_frame, width=4, padx=5, takefocus=0, border=0, background="#f0f0f0", state='disabled', font=self.code_font)
        self.line_numbers.pack(side=tk.LEFT, fill=tk.Y)
        self.code_view = tk.Text(self.left_frame, font=self.code_font, wrap="none", state='disabled', cursor="arrow")
        self.code_view.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.setup_syntax_highlighting()

        # Direita (Registradores)
        self.right_frame = tk.Frame(self.main_pane, bg="#f5f5f5")
        self.main_pane.add(self.right_frame)
        tk.Label(self.right_frame, text="Estado da CPU", font=("Arial", 12, "bold"), bg="#f5f5f5").pack(pady=15)
        self.setup_registers_display()

        # RODAPÉ
        self.bottom_frame = tk.Frame(root, height=100, bg="#e0e0e0", pady=10)
        self.bottom_frame.pack(side=tk.BOTTOM, fill=tk.X)
        self.setup_controls()
        self.console_label = tk.Label(root, text="Status: Aguardando...", bg="#ccc", anchor="w", font=("Consolas", 9))
        self.console_label.pack(side=tk.BOTTOM, fill=tk.X)

    # --- Montador (Texto -> Números) ---
    def montar_e_carregar(self, texto):
        mnemonics = {dados[0]: opcode for opcode, dados in self.backend.instructions.items()}
        programa_binario = []
        try:
            for linha in texto.split('\n'):
                if '/' in linha: linha = linha.split('/')[0]
                linha = linha.strip()
                if not linha: continue
                if ':' in linha: linha = linha.split(':')[1].strip()
                
                partes = linha.split()
                if not partes: continue
                
                instr = partes[0].upper()
                if instr in mnemonics:
                    programa_binario.append(mnemonics[instr])
                    if len(partes) > 1:
                        try: programa_binario.append(int(partes[1]))
                        except: programa_binario.append(0) 
            
            self.backend.load_program(programa_binario)
            self.atualizar_interface()
            self.log("Programa carregado com sucesso.")
        except Exception as e:
            messagebox.showerror("Erro", str(e))

    def load_file(self):
        path = filedialog.askopenfilename(filetypes=[("Texto", "*.txt"), ("Assembly", "*.asm")])
        if path:
            with open(path, "r", encoding="utf-8") as f: content = f.read()
            self.code_view.config(state='normal')
            self.code_view.delete("1.0", tk.END)
            self.code_view.insert("1.0", content)
            self.highlight_syntax()
            self.update_line_numbers()
            self.code_view.config(state='disabled')
            self.lbl_filename.config(text=path)
            self.montar_e_carregar(content)

    # --- Atualização Visual ---
    def setup_registers_display(self):
        frame = tk.Frame(self.right_frame, bg="#f5f5f5")
        frame.pack(padx=20)
        self.reg_labels = {}
        # Lista atualizada sem TOS, com Next Instruction
        campos = ["PC", "AC", "SP", "MAR", "MBR", "IR", "Next Inst.", "Flags"]
        
        for i, campo in enumerate(campos):
            tk.Label(frame, text=f"{campo}:", font=("Arial", 11, "bold"), bg="#f5f5f5").grid(row=i, column=0, sticky="e", padx=10, pady=8)
            val = tk.Label(frame, text="---", font=("Consolas", 12), bg="white", width=18, relief="sunken")
            val.grid(row=i, column=1, sticky="w", padx=10, pady=8)
            self.reg_labels[campo] = val

    def atualizar_interface(self):
        b = self.backend
        self.reg_labels["PC"].config(text=f"0x{b.pc:04X}")
        self.reg_labels["AC"].config(text=f"0x{b.ac:04X} ({b.ac})")
        self.reg_labels["SP"].config(text=f"0x{b.sp:04X}")
        self.reg_labels["MAR"].config(text=f"0x{b.mar:04X}")
        self.reg_labels["MBR"].config(text=f"0x{b.mbr:04X}")
        self.reg_labels["IR"].config(text=f"0x{b.ir:02X}")
        self.reg_labels["Flags"].config(text=f"Z={b.zero_flag} N={b.negative_flag}")
        
        # Pega a próxima instrução
        next_inst = b.get_next_instruction_name()
        self.reg_labels["Next Inst."].config(text=next_inst, fg="blue" if next_inst != "---" else "gray")

    # --- Controles Corrigidos ---
    def action_step(self):
        if not self.backend.rodando:
            self.log("Fim do programa. Resete para reiniciar.")
            return
        try:
            self.backend.run_step()
            self.atualizar_interface()
            self.log(f"Passo executado. PC={self.backend.pc}")
        except Exception as e:
            self.log(f"Erro: {e}")

    def action_reset(self):
        self.is_running = False
        self.backend.reset() # Agora define rodando = True
        self.atualizar_interface()
        self.log("Sistema resetado. Pronto.")

    def action_play(self):
        if self.is_running: return
        if not self.backend.rodando:
            self.log("Precisa resetar antes de iniciar.")
            return
        self.is_running = True
        self.log("Executando...")
        self.run_loop()

    def run_loop(self):
        if self.is_running:
            try:
                rodou = self.backend.run_step()
                self.atualizar_interface()
                if rodou:
                    self.root.after(self.slider.get(), self.run_loop)
                else:
                    self.log("Fim da execução (HALT).")
                    self.is_running = False
            except Exception as e:
                self.log(f"Erro: {e}")
                self.is_running = False

    def action_pause(self):
        self.is_running = False
        self.log("Pausado.")

    def setup_controls(self):
        c_frame = tk.Frame(self.bottom_frame, bg="#e0e0e0"); c_frame.pack()
        opts = {'padx': 10, 'pady': 5, 'font': ('Arial', 10, 'bold'), 'relief': 'raised'}
        tk.Button(c_frame, text="⏹ Reset", bg="#ffcccc", command=self.action_reset, **opts).pack(side=tk.LEFT, padx=5)
        tk.Button(c_frame, text="⏭ Passo", bg="#fff4cc", command=self.action_step, **opts).pack(side=tk.LEFT, padx=5)
        tk.Button(c_frame, text="▶ Executar", bg="#ccffcc", command=self.action_play, **opts).pack(side=tk.LEFT, padx=5)
        tk.Button(c_frame, text="⏸ Pausar", bg="#e0e0e0", command=self.action_pause, **opts).pack(side=tk.LEFT, padx=5)
        tk.Label(c_frame, text="Delay (ms):", bg="#e0e0e0").pack(side=tk.LEFT, padx=10)
        self.slider = tk.Scale(c_frame, from_=1000, to=50, orient=tk.HORIZONTAL, showvalue=1, length=100)
        self.slider.set(500); self.slider.pack(side=tk.LEFT)

    def log(self, msg): self.console_label.config(text=f"Status: {msg}")

    # Syntax e Linhas (Padrão)
    def setup_syntax_highlighting(self):
        self.code_view.tag_configure("instruction", foreground="blue", font=(self.code_font, 11, "bold"))
        self.code_view.tag_configure("label", foreground="#cc0000")
        self.code_view.tag_configure("comment", foreground="#008800")
        self.code_view.tag_configure("number", foreground="#e67e22")
    def highlight_syntax(self):
        mnemonics = ['LOCO', 'LODD', 'STOD', 'ADDD', 'SUBD', 'JUMP', 'JZ', 'JPOS', 'JN', 'DESV', 'CALL', 'RETN', 'HALT', 'INS', 'OUT']
        text = self.code_view.get("1.0", tk.END); lines = text.split('\n')
        for i, line in enumerate(lines):
            line_idx = i + 1
            if "/" in line:
                slash = line.find("/"); self.code_view.tag_add("comment", f"{line_idx}.{slash}", f"{line_idx}.end"); line = line[:slash]
            words = line.replace(':', ' :').split(); start_char = 0
            for w in words:
                ws = line.find(w, start_char); start = f"{line_idx}.{ws}"; end = f"{line_idx}.{ws+len(w)}"
                if w.upper() in mnemonics: self.code_view.tag_add("instruction", start, end)
                elif w.endswith(":"): self.code_view.tag_add("label", start, end)
                elif w.isdigit(): self.code_view.tag_add("number", start, end)
                start_char = ws + len(w)
    def update_line_numbers(self):
        self.line_numbers.config(state='normal'); self.line_numbers.delete('1.0', tk.END)
        lines = self.code_view.get('1.0', tk.END).split('\n'); lines.pop() if lines[-1] == '' else None
        self.line_numbers.insert('1.0', "\n".join(str(i) for i in range(1, len(lines) + 1)))
        self.line_numbers.config(state='disabled')

if __name__ == "__main__":
    root = tk.Tk()
    app = Mic1ViewerRunner(root)
    root.mainloop()