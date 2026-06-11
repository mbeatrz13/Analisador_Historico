import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
from tkinter import messagebox
import json
import os
from datetime import datetime

from analisador_historico import analisar_historico_gui

HISTORICO_DB = os.path.join(os.path.dirname(__file__), "historico_db.json")


def carregar_historico_db():
    if os.path.exists(HISTORICO_DB):
        with open(HISTORICO_DB, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def salvar_historico_db(registros):
    with open(HISTORICO_DB, "w", encoding="utf-8") as f:
        json.dump(registros, f, ensure_ascii=False, indent=2)


class InterfaceHistorico:

    def __init__(self, root):

        self.root = root

        self.root.title("Analisador de Histórico Escolar")
        self.root.geometry("1200x750")

        self.pdf_path = tk.StringVar()
        self.matriz_path = tk.StringVar()

        self.criar_topo()
        self.criar_abas()

    def criar_topo(self):

        frame = ttk.LabelFrame(self.root, text="Arquivos")
        frame.pack(fill="x", padx=10, pady=10)

        ttk.Label(frame, text="Histórico PDF:").grid(
            row=0, column=0, padx=5, pady=5, sticky="w"
        )
        ttk.Entry(frame, textvariable=self.pdf_path, width=90).grid(
            row=0, column=1, padx=5, pady=5
        )
        ttk.Button(frame, text="Selecionar", command=self.selecionar_pdf).grid(
            row=0, column=2, padx=5
        )

        ttk.Label(frame, text="Matriz (CSV/JSON)*opcional:").grid(
            row=1, column=0, padx=5, pady=5, sticky="w"
        )
        ttk.Entry(frame, textvariable=self.matriz_path, width=90).grid(
            row=1, column=1, padx=5, pady=5
        )
        ttk.Button(frame, text="Selecionar", command=self.selecionar_matriz).grid(
            row=1, column=2, padx=5
        )

        ttk.Button(frame, text="ANALISAR", command=self.executar_analise).grid(
            row=2, column=1, pady=10
        )

    def criar_abas(self):

        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)

        self.aba_resumo = ttk.Frame(self.notebook)
        self.aba_lexico = ttk.Frame(self.notebook)
        self.aba_sintatico = ttk.Frame(self.notebook)
        self.aba_semantico = ttk.Frame(self.notebook)
        self.aba_avisos = ttk.Frame(self.notebook)
        self.aba_componentes = ttk.Frame(self.notebook)
        self.aba_pendentes = ttk.Frame(self.notebook)
        self.aba_tokens = ttk.Frame(self.notebook)
        self.aba_historico = ttk.Frame(self.notebook)

        self.notebook.add(self.aba_resumo, text="Resumo")
        self.notebook.add(self.aba_lexico, text="Erros Léxicos")
        self.notebook.add(self.aba_sintatico, text="Erros Sintáticos")
        self.notebook.add(self.aba_semantico, text="Erros Semânticos")
        self.notebook.add(self.aba_avisos, text="Avisos")
        self.notebook.add(self.aba_componentes, text="Componentes")
        self.notebook.add(self.aba_pendentes, text="Pendências")
        self.notebook.add(self.aba_tokens, text="Tokens")
        self.notebook.add(self.aba_historico, text="Histórico")

        self.txt_resumo = self.criar_texto(self.aba_resumo)
        self.txt_lexico = self.criar_texto(self.aba_lexico)
        self.txt_sintatico = self.criar_texto(self.aba_sintatico)
        self.txt_semantico = self.criar_texto(self.aba_semantico)
        self.txt_avisos = self.criar_texto(self.aba_avisos)

        self.criar_tabela_componentes()
        self.criar_tabela_pendentes()
        self.criar_tabela_tokens()
        self.criar_aba_historico()

    def criar_texto(self, parent):

        txt = tk.Text(parent, wrap="word")
        txt.pack(fill="both", expand=True)
        return txt

    def criar_tabela_componentes(self):

        colunas = ("Periodo", "Codigo", "Turma", "CH", "Freq", "Media", "Situacao")

        self.tree_componentes = ttk.Treeview(
            self.aba_componentes, columns=colunas, show="headings"
        )

        for col in colunas:
            self.tree_componentes.heading(col, text=col)

        self.tree_componentes.pack(fill="both", expand=True)

    def criar_tabela_pendentes(self):

        colunas = ("Codigo", "Nome", "CH")

        self.tree_pendentes = ttk.Treeview(
            self.aba_pendentes, columns=colunas, show="headings"
        )

        for col in colunas:
            self.tree_pendentes.heading(col, text=col)

        self.tree_pendentes.pack(fill="both", expand=True)

    def criar_tabela_tokens(self):

        colunas = ("Linha", "Tipo", "Valor")

        self.tree_tokens = ttk.Treeview(
            self.aba_tokens, columns=colunas, show="headings"
        )

        self.tree_tokens.heading("Linha", text="Linha")
        self.tree_tokens.heading("Tipo", text="Tipo")
        self.tree_tokens.heading("Valor", text="Valor")

        self.tree_tokens.column("Linha", width=60)
        self.tree_tokens.column("Tipo", width=200)
        self.tree_tokens.column("Valor", width=500)

        scroll = ttk.Scrollbar(self.aba_tokens, orient="vertical", command=self.tree_tokens.yview)
        self.tree_tokens.configure(yscrollcommand=scroll.set)

        self.tree_tokens.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

    def preencher_tokens(self, tokens):

        for item in self.tree_tokens.get_children():
            self.tree_tokens.delete(item)

        for t in tokens:
            self.tree_tokens.insert(
                "", "end",
                values=(t.linha, t.tipo, t.valor[:80])
            )

    def criar_aba_historico(self):

        frame_topo = ttk.Frame(self.aba_historico)
        frame_topo.pack(fill="x", padx=5, pady=5)

        ttk.Button(
            frame_topo, text="Atualizar", command=self.carregar_lista_historico
        ).pack(side="left", padx=5)

        ttk.Button(
            frame_topo, text="Excluir Selecionado", command=self.excluir_registro
        ).pack(side="left", padx=5)

        colunas = ("Data", "Nome", "Matricula", "Curso", "IRA", "Valido", "Erros")

        self.tree_historico = ttk.Treeview(
            self.aba_historico, columns=colunas, show="headings"
        )

        self.tree_historico.heading("Data", text="Data da Análise")
        self.tree_historico.heading("Nome", text="Nome")
        self.tree_historico.heading("Matricula", text="Matrícula")
        self.tree_historico.heading("Curso", text="Curso")
        self.tree_historico.heading("IRA", text="IRA")
        self.tree_historico.heading("Valido", text="Válido")
        self.tree_historico.heading("Erros", text="Total Erros")

        self.tree_historico.column("Data", width=140)
        self.tree_historico.column("Nome", width=200)
        self.tree_historico.column("Matricula", width=110)
        self.tree_historico.column("Curso", width=250)
        self.tree_historico.column("IRA", width=60)
        self.tree_historico.column("Valido", width=60)
        self.tree_historico.column("Erros", width=80)

        self.tree_historico.pack(fill="both", expand=True, padx=5, pady=5)
        self.tree_historico.bind("<Double-1>", self.ver_detalhes_historico)

        self.carregar_lista_historico()

    def carregar_lista_historico(self):

        for item in self.tree_historico.get_children():
            self.tree_historico.delete(item)

        registros = carregar_historico_db()

        for reg in registros:
            self.tree_historico.insert(
                "", "end",
                values=(
                    reg.get("data_analise", ""),
                    reg.get("nome", ""),
                    reg.get("matricula", ""),
                    reg.get("curso", ""),
                    reg.get("ira", ""),
                    "Sim" if reg.get("valido") else "Não",
                    reg.get("total_erros", 0)
                )
            )

    def excluir_registro(self):

        sel = self.tree_historico.selection()
        if not sel:
            messagebox.showwarning("Aviso", "Selecione um registro para excluir.")
            return

        idx = self.tree_historico.index(sel[0])
        registros = carregar_historico_db()

        if 0 <= idx < len(registros):
            registros.pop(idx)
            salvar_historico_db(registros)
            self.carregar_lista_historico()

    def ver_detalhes_historico(self, event):

        sel = self.tree_historico.selection()
        if not sel:
            return

        idx = self.tree_historico.index(sel[0])
        registros = carregar_historico_db()

        if idx >= len(registros):
            return

        reg = registros[idx]

        janela = tk.Toplevel(self.root)
        janela.title(f"Detalhes — {reg.get('nome', 'N/A')}")
        janela.geometry("700x500")

        txt = tk.Text(janela, wrap="word")
        txt.pack(fill="both", expand=True, padx=10, pady=10)

        detalhes = f"""Data da Análise: {reg.get('data_analise', '')}
Arquivo: {reg.get('arquivo', '')}

Nome: {reg.get('nome', '')}
Matrícula: {reg.get('matricula', '')}
Curso: {reg.get('curso', '')}
Status: {reg.get('status', '')}
IRA: {reg.get('ira', '')}
Período Inicial: {reg.get('periodo_inicial', '')}
Período Atual: {reg.get('periodo_atual', '')}

Válido: {'Sim' if reg.get('valido') else 'Não'}
Total de Erros: {reg.get('total_erros', 0)}

--- Erros Léxicos ---
{chr(10).join(reg.get('erros_lexicos', [])) or 'Nenhum'}

--- Erros Sintáticos ---
{chr(10).join(reg.get('erros_sintaticos', [])) or 'Nenhum'}

--- Erros Semânticos ---
{chr(10).join(reg.get('erros_semanticos', [])) or 'Nenhum'}

--- Avisos ---
{chr(10).join(reg.get('avisos', [])) or 'Nenhum'}

--- Componentes ({len(reg.get('componentes', []))}) ---
"""
        for c in reg.get("componentes", []):
            detalhes += f"  {c['periodo']} | {c['codigo']} | {c['turma']} | CH:{c['ch']} | Freq:{c['freq']} | Média:{c['media']} | {c['situacao']}\n"

        detalhes += f"\n--- Pendências ({len(reg.get('pendentes', []))}) ---\n"
        for p in reg.get("pendentes", []):
            detalhes += f"  {p['codigo']} | {p['nome']} | {p['ch']}\n"

        txt.insert(tk.END, detalhes)
        txt.config(state="disabled")

    def salvar_no_historico(self, resultado):

        hist = resultado["historico"]

        registro = {
            "data_analise": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "arquivo": self.pdf_path.get(),
            "nome": hist.nome,
            "matricula": hist.matricula,
            "curso": hist.curso,
            "status": hist.status,
            "ira": hist.ira,
            "periodo_inicial": hist.periodo_inicial,
            "periodo_atual": hist.periodo_atual,
            "valido": resultado["valido"],
            "total_erros": (
                len(resultado["erros_lexicos"])
                + len(resultado["erros_sintaticos"])
                + len(resultado["erros_semanticos"])
            ),
            "erros_lexicos": resultado["erros_lexicos"],
            "erros_sintaticos": resultado["erros_sintaticos"],
            "erros_semanticos": resultado["erros_semanticos"],
            "avisos": resultado["avisos"],
            "componentes": [
                {
                    "periodo": c.periodo,
                    "codigo": c.codigo,
                    "turma": c.cod_turma,
                    "ch": c.ch,
                    "freq": c.frequencia,
                    "media": c.media,
                    "situacao": c.situacao,
                }
                for c in hist.componentes
            ],
            "pendentes": hist.pendentes,
        }

        registros = carregar_historico_db()
        registros.append(registro)
        salvar_historico_db(registros)
        self.carregar_lista_historico()

    def selecionar_pdf(self):

        arquivo = filedialog.askopenfilename(
            title="Selecionar Histórico",
            filetypes=[("PDF", "*.pdf")]
        )

        if arquivo:
            self.pdf_path.set(arquivo)

    def selecionar_matriz(self):

        arquivo = filedialog.askopenfilename(
            title="Selecionar Matriz",
            filetypes=[("JSON", "*.json"), ("CSV", "*.csv")]
        )

        if arquivo:
            self.matriz_path.set(arquivo)

    def executar_analise(self):

        if not self.pdf_path.get():
            messagebox.showerror("Erro", "Selecione um histórico PDF.")
            return

        resultado = analisar_historico_gui(
            self.pdf_path.get(),
            self.matriz_path.get() or None
        )

        if "erro_fatal" in resultado:
            messagebox.showerror("Erro", "\n".join(resultado["erro_fatal"]))
            return

        self.preencher_resumo(resultado)
        self.preencher_erros(self.txt_lexico, resultado["erros_lexicos"])
        self.preencher_erros(self.txt_sintatico, resultado["erros_sintaticos"])
        self.preencher_erros(self.txt_semantico, resultado["erros_semanticos"])
        self.preencher_erros(self.txt_avisos, resultado["avisos"])
        self.preencher_componentes(resultado["historico"])
        self.preencher_pendentes(resultado["historico"])
        self.preencher_tokens(resultado["tokens"])

        self.salvar_no_historico(resultado)

    def preencher_resumo(self, resultado):

        hist = resultado["historico"]

        self.txt_resumo.delete("1.0", tk.END)

        texto = f"""
VALIDO: {resultado['valido']}

Nome: {hist.nome}
Matrícula: {hist.matricula}
Curso: {hist.curso}
Status: {hist.status}
IRA: {hist.ira}

Período Inicial: {hist.periodo_inicial}
Período Atual: {hist.periodo_atual}

Componentes: {len(hist.componentes)}
Pendências: {len(hist.pendentes)}

Erros Léxicos: {len(resultado['erros_lexicos'])}
Erros Sintáticos: {len(resultado['erros_sintaticos'])}
Erros Semânticos: {len(resultado['erros_semanticos'])}
Avisos: {len(resultado['avisos'])}
"""

        self.txt_resumo.insert(tk.END, texto)

    def preencher_erros(self, widget, lista):

        widget.delete("1.0", tk.END)

        if not lista:
            widget.insert(tk.END, "Nenhum registro encontrado.")
            return

        for item in lista:
            widget.insert(tk.END, item + "\n")

    def preencher_componentes(self, hist):

        for item in self.tree_componentes.get_children():
            self.tree_componentes.delete(item)

        for c in hist.componentes:
            self.tree_componentes.insert(
                "", "end",
                values=(
                    c.periodo, c.codigo, c.cod_turma,
                    c.ch, c.frequencia, c.media, c.situacao
                )
            )

    def preencher_pendentes(self, hist):

        for item in self.tree_pendentes.get_children():
            self.tree_pendentes.delete(item)

        for p in hist.pendentes:
            self.tree_pendentes.insert(
                "", "end",
                values=(p["codigo"], p["nome"], p["ch"])
            )


if __name__ == "__main__":

    root = tk.Tk()
    app = InterfaceHistorico(root)
    root.mainloop()
