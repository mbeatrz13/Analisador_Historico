# Analisador de Histórico Escolar

Aplicação desktop em Python que analisa históricos escolares em PDF (padrão SIGAA/UERN), realizando análise léxica, sintática e semântica para validar a integridade dos dados.

## Funcionalidades

- **Upload de PDF** — Carrega históricos escolares em formato PDF
- **Análise Léxica** — Tokenização do texto extraído, identificando campos e valores
- **Análise Sintática** — Verifica a estrutura esperada do documento (cabeçalho, dados pessoais, componentes, etc.)
- **Análise Semântica** — Valida regras de negócio (IRA, notas, frequências, consistência de dados)
- **Matriz Curricular (opcional)** — Carrega um JSON/CSV com a matriz para verificar disciplinas
- **Tabela de Tokens** — Exibe todos os tokens gerados na análise (volátil, apenas em memória)
- **Histórico de Análises** — Salva cada análise em um arquivo JSON para consulta posterior
- **Interface Gráfica** — Abas organizadas com resumo, erros, componentes, pendências e histórico

## Estrutura do Projeto

```
Analisador_Historico/
├── analisador_historico.py   # Módulos de extração, léxico, parser e semântico
├── interface.py              # Interface gráfica (Tkinter)
├── historico_db.json         # Banco de dados local das análises (gerado automaticamente)
└── README.md
```

## Pré-requisitos

- Python 3.10+
- pip

## Instalação

```bash
# Clone o repositório
git clone https://github.com/mbeatrz13/Analisador_Historico.git
cd Analisador_Historico

# Crie e ative o ambiente virtual
python -m venv .venv

# Windows
.venv\Scripts\activate

# Linux/macOS
source .venv/bin/activate

# Instale as dependências
pip install pdfplumber
```

## Como Rodar

```bash
python interface.py
```

A interface gráfica será aberta com as seguintes abas:

| Aba | Descrição |
|-----|-----------|
| Resumo | Visão geral da análise (nome, matrícula, IRA, totais) |
| Erros Léxicos | Tokens com valores fora do esperado |
| Erros Sintáticos | Estrutura do documento com problemas |
| Erros Semânticos | Inconsistências nas regras de negócio |
| Avisos | Alertas não-críticos |
| Componentes | Tabela com todas as disciplinas cursadas |
| Pendências | Componentes obrigatórios ainda não cursados |
| Tokens | Tabela volátil com os tokens da análise atual |
| Histórico | Registro persistente de todas as análises realizadas |

## Como Usar

1. Clique em **Selecionar** ao lado de "Histórico PDF" e escolha o arquivo PDF
2. (Opcional) Selecione um arquivo de matriz curricular (JSON ou CSV)
3. Clique em **ANALISAR**
4. Navegue pelas abas para ver os resultados
5. A aba **Histórico** mantém o registro de todas as análises — clique duas vezes em um registro para ver os detalhes completos

## Formato da Matriz Curricular (opcional)

**JSON:**
```json
{
  "NCC0101": "Introdução à Computação",
  "NCC0102": "Cálculo I"
}
```

**CSV:**
```csv
codigo,nome
NCC0101,Introdução à Computação
NCC0102,Cálculo I
```

## Regras Semânticas Implementadas

| Regra | Verificação |
|-------|-------------|
| R01 | Matrícula com 11 dígitos e ano válido |
| R02 | Data de nascimento e idade plausível |
| R03 | IRA entre 0 e 10 |
| R04 | Período inicial consistente com matrícula |
| R05 | Frequência entre 0% e 100% |
| R06 | Notas entre 0 e 10 |
| R07 | APR com média ≥ 7.0 / APRN entre 6.0 e 7.0 |
| R08 | REP com média < 7.0 |
| R09 | REPF/REPMF com frequência < 75% |
| R10 | MATR sem notas preenchidas |
| R11 | nota_min ≤ média |
| R12 | CH integralizada ≤ CH exigida |
| R13 | IRA declarado próximo da média calculada |
| R14 | Período atual entre 1 e 20 |
| R15 | Disciplinas presentes na matriz curricular |
