import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
from tkinter import messagebox

from analisador_historico import analisar_historico_gui


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

        frame = ttk.LabelFrame(
            self.root,
            text="Arquivos"
        )

        frame.pack(
            fill="x",
            padx=10,
            pady=10
        )

        ttk.Label(
            frame,
            text="Histórico PDF:"
        ).grid(
            row=0,
            column=0,
            padx=5,
            pady=5,
            sticky="w"
        )

        ttk.Entry(
            frame,
            textvariable=self.pdf_path,
            width=90
        ).grid(
            row=0,
            column=1,
            padx=5,
            pady=5
        )

        ttk.Button(
            frame,
            text="Selecionar",
            command=self.selecionar_pdf
        ).grid(
            row=0,
            column=2,
            padx=5
        )

        ttk.Label(
            frame,
            text="Matriz (CSV/JSON)*opcional:"
        ).grid(
            row=1,
            column=0,
            padx=5,
            pady=5,
            sticky="w"
        )

        ttk.Entry(
            frame,
            textvariable=self.matriz_path,
            width=90
        ).grid(
            row=1,
            column=1,
            padx=5,
            pady=5
        )

        ttk.Button(
            frame,
            text="Selecionar",
            command=self.selecionar_matriz
        ).grid(
            row=1,
            column=2,
            padx=5
        )

        ttk.Button(
            frame,
            text="ANALISAR",
            command=self.executar_analise
        ).grid(
            row=2,
            column=1,
            pady=10
        )

    def criar_abas(self):

        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(
            fill="both",
            expand=True,
            padx=10,
            pady=10
        )

        self.aba_resumo = ttk.Frame(self.notebook)
        self.aba_lexico = ttk.Frame(self.notebook)
        self.aba_sintatico = ttk.Frame(self.notebook)
        self.aba_semantico = ttk.Frame(self.notebook)
        self.aba_avisos = ttk.Frame(self.notebook)
        self.aba_componentes = ttk.Frame(self.notebook)
        self.aba_pendentes = ttk.Frame(self.notebook)

        self.notebook.add(self.aba_resumo, text="Resumo")
        self.notebook.add(self.aba_lexico, text="Erros Léxicos")
        self.notebook.add(self.aba_sintatico, text="Erros Sintáticos")
        self.notebook.add(self.aba_semantico, text="Erros Semânticos")
        self.notebook.add(self.aba_avisos, text="Avisos")
        self.notebook.add(self.aba_componentes, text="Componentes")
        self.notebook.add(self.aba_pendentes, text="Pendências")

        self.txt_resumo = self.criar_texto(self.aba_resumo)
        self.txt_lexico = self.criar_texto(self.aba_lexico)
        self.txt_sintatico = self.criar_texto(self.aba_sintatico)
        self.txt_semantico = self.criar_texto(self.aba_semantico)
        self.txt_avisos = self.criar_texto(self.aba_avisos)

        self.criar_tabela_componentes()
        self.criar_tabela_pendentes()

    def criar_texto(self, parent):

        txt = tk.Text(
            parent,
            wrap="word"
        )

        txt.pack(
            fill="both",
            expand=True
        )

        return txt

    def criar_tabela_componentes(self):

        colunas = (
            "Periodo",
            "Codigo",
            "Turma",
            "CH",
            "Freq",
            "Media",
            "Situacao"
        )

        self.tree_componentes = ttk.Treeview(
            self.aba_componentes,
            columns=colunas,
            show="headings"
        )

        for col in colunas:
            self.tree_componentes.heading(
                col,
                text=col
            )

        self.tree_componentes.pack(
            fill="both",
            expand=True
        )

    def criar_tabela_pendentes(self):

        colunas = (
            "Codigo",
            "Nome",
            "CH"
        )

        self.tree_pendentes = ttk.Treeview(
            self.aba_pendentes,
            columns=colunas,
            show="headings"
        )

        for col in colunas:
            self.tree_pendentes.heading(
                col,
                text=col
            )

        self.tree_pendentes.pack(
            fill="both",
            expand=True
        )

    def selecionar_pdf(self):

        arquivo = filedialog.askopenfilename(
            title="Selecionar Histórico",
            filetypes=[
                ("PDF", "*.pdf")
            ]
        )

        if arquivo:
            self.pdf_path.set(arquivo)

    def selecionar_matriz(self):

        arquivo = filedialog.askopenfilename(
            title="Selecionar Matriz",
            filetypes=[
                ("JSON", "*.json"),
                ("CSV", "*.csv")
            ]
        )

        if arquivo:
            self.matriz_path.set(arquivo)

    def executar_analise(self):

        if not self.pdf_path.get():

            messagebox.showerror(
                "Erro",
                "Selecione um histórico PDF."
            )

            return

        resultado = analisar_historico_gui(
            self.pdf_path.get(),
            self.matriz_path.get() or None
        )

        if "erro_fatal" in resultado:

            messagebox.showerror(
                "Erro",
                "\n".join(resultado["erro_fatal"])
            )

            return

        self.preencher_resumo(resultado)

        self.preencher_erros(
            self.txt_lexico,
            resultado["erros_lexicos"]
        )

        self.preencher_erros(
            self.txt_sintatico,
            resultado["erros_sintaticos"]
        )

        self.preencher_erros(
            self.txt_semantico,
            resultado["erros_semanticos"]
        )

        self.preencher_erros(
            self.txt_avisos,
            resultado["avisos"]
        )

        self.preencher_componentes(
            resultado["historico"]
        )

        self.preencher_pendentes(
            resultado["historico"]
        )

    def preencher_resumo(self, resultado):

        hist = resultado["historico"]

        self.txt_resumo.delete(
            "1.0",
            tk.END
        )

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

        self.txt_resumo.insert(
            tk.END,
            texto
        )

    def preencher_erros(self, widget, lista):

        widget.delete(
            "1.0",
            tk.END
        )

        if not lista:

            widget.insert(
                tk.END,
                "Nenhum registro encontrado."
            )

            return

        for item in lista:

            widget.insert(
                tk.END,
                item + "\n"
            )

    def preencher_componentes(self, hist):

        for item in self.tree_componentes.get_children():
            self.tree_componentes.delete(item)

        for c in hist.componentes:

            self.tree_componentes.insert(
                "",
                "end",
                values=(
                    c.periodo,
                    c.codigo,
                    c.cod_turma,
                    c.ch,
                    c.frequencia,
                    c.media,
                    c.situacao
                )
            )

    def preencher_pendentes(self, hist):

        for item in self.tree_pendentes.get_children():
            self.tree_pendentes.delete(item)

        for p in hist.pendentes:

            self.tree_pendentes.insert(
                "",
                "end",
                values=(
                    p["codigo"],
                    p["nome"],
                    p["ch"]
                )
            )


if __name__ == "__main__":

    root = tk.Tk()

    app = InterfaceHistorico(root)

    root.mainloop()