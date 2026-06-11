
import re
import sys
import pdfplumber
import json
import csv
from collections import namedtuple
from dataclasses import dataclass, field
from typing import Optional, List
from datetime import datetime

_RUIDO = [
    r'SIGAA\s*-\s*Sistema Integrado',
    r'UERN\s*-\s*Universidade do Estado',
    r'PROEG\s*-\s*Pró-Reitoria',
    r'DIRCA\s*-\s*Diretoria',
    r'Campus Universitário Central',
    r'Recredenciada conforme Decreto',
    r'Diário Oficial do Estado',
    r'Para verificar a autenticidade',
    r'Página\s+\d+\s+de\s+\d+',
    r'^Ano/Período\s+Componente Curricular',
    r'^Letivo\s+Aula',
]
_RE_RUIDO = re.compile('|'.join(_RUIDO), re.IGNORECASE)

def extrair_texto(caminho_pdf: str):
    avisos = []
    try:
        with pdfplumber.open(caminho_pdf) as pdf:
            if len(pdf.pages) == 0:
                return '', ['[Extração] PDF sem páginas legíveis.']
            blocos = []
            for i, pagina in enumerate(pdf.pages, 1):
                texto_pagina = pagina.extract_text()
                if not texto_pagina:
                    avisos.append(f'[Extração] Página {i} sem texto.')
                    continue
                blocos.append(texto_pagina)
    except FileNotFoundError:
        return '', [f'[Extração] Arquivo não encontrado: {caminho_pdf}']
    except Exception as e:
        return '', [f'[Extração] Erro: {e}']

    texto_bruto = '\n'.join(blocos)
    linhas_limpas = [l for l in texto_bruto.splitlines() if not _RE_RUIDO.search(l)]
    return '\n'.join(linhas_limpas), avisos

def carregar_matriz(caminho_matriz):
  
  if not caminho_matriz:
    return None
  matriz = {}
  
  try:
    
    if caminho_matriz.lower().endswith('.json'):
      with open(caminho_matriz, 'r', encoding='utf-8') as arq:
        dados = json.load(arq)
        
        for codigo, nome in dados.items():
          matriz[str(codigo)] = str(nome)
          
    elif caminho_matriz.lower().endswith('.csv'):
      with open(caminho_matriz, 'r', encoding='utf-8') as arq:
        leitor = csv.DictReader(arq)
        for linha in leitor:
          if len(linha) >= 2:
            codigo = linha["codigo"].strip()
            nome = linha["nome"].strip()
            
            matriz[codigo] = nome
    return matriz
  
  except Exception:
    
    return None


Token = namedtuple('Token', ['tipo', 'valor', 'linha'])

RE_LINHA_COMP = re.compile(
    r'^(?P<periodo>\d{4}\.[12])\s+'
    r'(?P<flag>[*@&#§%e])?\s*'
    r'(?P<turma>[A-Z]{2,5}\d{4})\s+'
    r'(?P<ha>\d+)\s+'
    r'(?P<ch>\d+)\s+'
    r'(?P<num_turma>\d+)\s+'
    r'(?P<freq>[\d]+,\d|--)\s+'
    r'(?P<nota_min>[\d]+\.\d|--)\s+'
    r'(?P<media>[\d]+\.\d|--)\s+'
    r'(?P<situacao>APR|APRN|MATR|REP|REPF|REPMF|REPN|REPNF|CANC|DISP|REC|TRANC|TRANS|INCORP|CUMP)'
    r'\s*$'
)

RE_LINHA_CH = re.compile(
    r'^(Exigido|Integralizado|Pendente)\s+'
    r'(\d+)\s*h\s+(\d+)\s*h\s+(\d+)\s*h\s+(\d+)\s*h'
)

RE_LINHA_PEND = re.compile(
    r'^([A-Z]{2,5}\d{4}|ENADE)\s+(.+?)\s+(Matriculado\s+)?(\d+)\s*h\s*$'
)

RE_CABECALHO   = re.compile(r'Histórico\s+Escolar\s+-\s+Emitido\s+em:\s*(\d{2}/\d{2}/\d{4})\s+às\s+(\d{2}:\d{2})')
RE_NOME        = re.compile(r'Nome:\s+(.+?)\s+Matr[íi]cula:\s+(\d{11})')
RE_NASC        = re.compile(r'Data de Nascimento:\s+(\d{2}/\d{2}/\d{4})')
RE_CPF         = re.compile(r'Nº do CPF:\s+(\d{3}\.\d{3}\.\d{3}-\d{2})')
RE_CURSO       = re.compile(r'Curso:\s+(.+)')
RE_STATUS      = re.compile(r'Status:\s+(ATIVO|INATIVO|CONCLU[ÍI]DO|CANCELADO|TRANCADO)')
RE_IRA         = re.compile(r'IRA:\s+(\d+\.\d+)')
RE_CURRICULO   = re.compile(r'Currículo:\s+([A-Z]+\d{4})')
RE_PER_INICIAL = re.compile(r'Período Letivo Inicial:\s+(\d{4}\.[12])')
RE_INGRESSO    = re.compile(r'Forma de Ingresso:\s+(SiSU|ENEM|Vestibular|Transferência|Reingresso)')
RE_PER_ATUAL   = re.compile(r'Período Letivo Atual:\s+(\d+)')
RE_SECAO_COMP  = re.compile(r'Componentes\s+Curriculares\s+Cursados/Cursando')
RE_SECAO_CH    = re.compile(r'Carga\s+Horária\s+Integralizada/Pendente')
RE_SECAO_PEND  = re.compile(r'Componentes\s+Curriculares\s+Obrigatórios\s+Pendentes:(\d+)')
RE_EQUIVALENCIA= re.compile(r'Equivalências:')
RE_NOME_DISC   = re.compile(r'^(.+?)\s+\((\d{8})\)\s*$')
RE_PROFESSOR   = re.compile(r'^(Dr[a]?\.|MSc\.|Me\.|Esp\.)\s+[A-Z]')

def tokenizar(texto: str):
    tokens, erros = [], []
    for num_linha, linha in enumerate(texto.splitlines(), 1):
        s = linha.strip()
        if not s:
            continue

        m = RE_CABECALHO.search(s)
        if m:
            tokens += [Token('TOKEN_HISTORICO', 'Histórico Escolar', num_linha),
                       Token('TOKEN_DATA_EMISSAO', m.group(1), num_linha),
                       Token('TOKEN_HORA_EMISSAO', m.group(2), num_linha)]
            continue

        m = RE_NOME.search(s)
        if m:
            tokens += [Token('TOKEN_NOME', m.group(1), num_linha),
                       Token('TOKEN_MATRICULA', m.group(2), num_linha)]
            continue

        m = RE_NASC.search(s)
        if m:
            tokens.append(Token('TOKEN_DATA_NASC', m.group(1), num_linha))
            continue

        m = RE_CPF.search(s)
        if m:
            tokens.append(Token('TOKEN_CPF', m.group(1), num_linha))
            continue

        m = RE_CURSO.match(s)
        if m:
            tokens.append(Token('TOKEN_CURSO', m.group(1).strip(), num_linha))
            continue

        m_s = RE_STATUS.search(s)
        m_i = RE_IRA.search(s)
        if m_s:
            tokens.append(Token('TOKEN_STATUS', m_s.group(1), num_linha))
        if m_i:
            ira = float(m_i.group(1))
            if not (0.0 <= ira <= 10.0):
                erros.append(f'[Léxico] Linha {num_linha}: IRA "{ira}" fora de [0,10].')
            else:
                tokens.append(Token('TOKEN_IRA', m_i.group(1), num_linha))
            continue
        if m_s:
            continue

        m = RE_CURRICULO.search(s)
        if m and 'Currículo' in s:
            tokens.append(Token('TOKEN_CURRICULO', m.group(1), num_linha))
            continue

        emitiu = False
        m = RE_PER_INICIAL.search(s)
        if m:
            tokens.append(Token('TOKEN_PERIODO_INICIAL', m.group(1), num_linha))
            emitiu = True
        m = RE_INGRESSO.search(s)
        if m:
            tokens.append(Token('TOKEN_INGRESSO', m.group(1), num_linha))
            emitiu = True
        if emitiu:
            continue

        m = RE_PER_ATUAL.search(s)
        if m and 'Período Letivo Atual' in s:
            tokens.append(Token('TOKEN_PERIODO_ATUAL', m.group(1), num_linha))
            continue

        if RE_SECAO_COMP.search(s):
            tokens.append(Token('TOKEN_SECAO_COMP', s, num_linha))
            continue
        if RE_SECAO_CH.search(s):
            tokens.append(Token('TOKEN_SECAO_CH', s, num_linha))
            continue
        m = RE_SECAO_PEND.search(s)
        if m:
            tokens.append(Token('TOKEN_SECAO_PEND', m.group(1), num_linha))
            continue
        if RE_EQUIVALENCIA.search(s):
            tokens.append(Token('TOKEN_EQUIVALENCIA', s, num_linha))
            continue

        m = RE_NOME_DISC.match(s)
        if m:
            tokens.append(Token('TOKEN_NOME_DISC', m.group(1).strip(), num_linha))
            tokens.append(Token('TOKEN_COD_DISC',  m.group(2),          num_linha))
            continue

        m = RE_LINHA_COMP.match(s)
        if m:
            freq_s = m.group('freq')
            if freq_s != '--':
                freq = float(freq_s.replace(',', '.'))
                if not (0.0 <= freq <= 100.0):
                    erros.append(f'[Léxico] Linha {num_linha}: frequência "{freq_s}" fora de [0,100].')
            for campo in ('nota_min', 'media'):
                val = m.group(campo)
                if val != '--':
                    n = float(val)
                    if not (0.0 <= n <= 10.0):
                        erros.append(f'[Léxico] Linha {num_linha}: {campo} "{val}" fora de [0,10].')
            tokens.append(Token('TOKEN_LINHA_COMP', s, num_linha))
            continue

        if RE_PROFESSOR.match(s) or s.startswith('JONATHA') or s.startswith('MSc'):
            continue

        m = RE_LINHA_CH.match(s)
        if m:
            tokens.append(Token('TOKEN_LINHA_CH', s, num_linha))
            continue

        m = RE_LINHA_PEND.match(s)
        if m and any(s.startswith(p) for p in ('NCC', 'CAN', 'UCE', 'ENADE')):
            tokens.append(Token('TOKEN_LINHA_PEND', s, num_linha))
            continue

    return tokens, erros

print('✓ Módulo Lexer carregado')

"""## 🌳 Módulo 3 — Parser (análise sintática)"""



@dataclass
class Componente:
    nome:str=''; codigo:str=''; periodo:str=''; flag:str=''
    cod_turma:str=''; hora_aula:str=''; ch:str=''; num_turma:str=''
    frequencia:str=''; nota_min:str=''; media:str=''; situacao:str=''
    linha_num:int=0

@dataclass
class LinhasCH:
    exigido_obrig:str=''; exigido_opt:str=''; exigido_comp:str=''; exigido_total:str=''
    integr_obrig:str='';  integr_opt:str='';  integr_comp:str='';  integr_total:str=''
    pend_obrig:str='';    pend_opt:str='';    pend_comp:str='';    pend_total:str=''

@dataclass
class HistoricoEscolar:
    data_emissao:str=''; hora_emissao:str=''
    nome:str=''; matricula:str=''; data_nasc:str=''; cpf:str=''
    curso:str=''; status:str=''; ira:str=''; curriculo:str=''
    periodo_inicial:str=''; ingresso:str=''; periodo_atual:str=''
    componentes: List[Componente] = field(default_factory=list)
    ch: LinhasCH = field(default_factory=LinhasCH)
    pendentes: list = field(default_factory=list)

class Parser:
    def __init__(self, tokens):
        self.toks = tokens; self.pos = 0
        self.erros = []; self.h = HistoricoEscolar()

    def _t(self): return self.toks[self.pos] if self.pos < len(self.toks) else None
    def _tipo(self): t = self._t(); return t.tipo if t else None

    def _eat(self, tipo):
        t = self._t()
        if t and t.tipo == tipo:
            self.pos += 1; return t
        loc = f'linha {t.linha}' if t else 'fim'
        self.erros.append(
            f'[Sintático] {loc}: esperado {tipo}, '
            f'encontrado "{(t.valor[:40] if t else "EOF")}" ({t.tipo if t else "-"})'
        )
        return None

    def _eat_opt(self, tipo):
        t = self._t()
        if t and t.tipo == tipo:
            self.pos += 1; return t
        return None

    def parse(self):
        self._cabecalho(); self._dados_pessoais()
        self._dados_vinculo(); self._tabela_componentes(); self._sumario()
        return self.h

    def _cabecalho(self):
        if not self._eat('TOKEN_HISTORICO'):
            self.erros.insert(0, "[Sintático] Documento não inicia com 'Histórico Escolar'.")
        t_d = self._eat('TOKEN_DATA_EMISSAO'); t_h = self._eat('TOKEN_HORA_EMISSAO')
        if t_d: self.h.data_emissao = t_d.valor
        if t_h: self.h.hora_emissao = t_h.valor

    def _dados_pessoais(self):
        t = self._eat('TOKEN_NOME')
        if t: self.h.nome = t.valor
        else: self.erros.append("[Sintático] Campo 'Nome' não encontrado.")
        t = self._eat('TOKEN_MATRICULA')
        if t: self.h.matricula = t.valor
        else: self.erros.append("[Sintático] Campo 'Matrícula' não encontrado.")
        t = self._eat_opt('TOKEN_DATA_NASC')
        if t: self.h.data_nasc = t.valor
        t = self._eat_opt('TOKEN_CPF')
        if t: self.h.cpf = t.valor

    def _dados_vinculo(self):
        t = self._eat('TOKEN_CURSO')
        if t: self.h.curso = t.valor
        else: self.erros.append("[Sintático] Campo 'Curso' não encontrado.")
        t = self._eat('TOKEN_STATUS')
        if t: self.h.status = t.valor
        else: self.erros.append("[Sintático] Campo 'Status' não encontrado.")
        t = self._eat('TOKEN_IRA')
        if t: self.h.ira = t.valor
        else: self.erros.append("[Sintático] Campo 'IRA' não encontrado.")
        t = self._eat_opt('TOKEN_CURRICULO')
        if t: self.h.curriculo = t.valor
        t = self._eat_opt('TOKEN_PERIODO_INICIAL')
        if t: self.h.periodo_inicial = t.valor
        t = self._eat_opt('TOKEN_INGRESSO')
        if t: self.h.ingresso = t.valor
        t = self._eat('TOKEN_PERIODO_ATUAL')
        if t: self.h.periodo_atual = t.valor
        else: self.erros.append("[Sintático] Campo 'Período Letivo Atual' não encontrado.")

    def _tabela_componentes(self):
        t = self._eat('TOKEN_SECAO_COMP')
        if not t:
            self.erros.append("[Sintático] Seção 'Componentes Curriculares' não encontrada.")
        while self._tipo() not in ('TOKEN_SECAO_CH', 'TOKEN_SECAO_PEND', None):
            self._componente()

    def _componente(self):
        if self._tipo() in ('TOKEN_HISTORICO', 'TOKEN_DATA_EMISSAO', 'TOKEN_HORA_EMISSAO',
                            'TOKEN_NOME', 'TOKEN_MATRICULA', 'TOKEN_SECAO_COMP'):
            self.pos += 1; return
        comp = Componente()
        t_nome = self._eat_opt('TOKEN_NOME_DISC')
        if t_nome: comp.nome = t_nome.valor
        t_cod = self._eat_opt('TOKEN_COD_DISC')
        if t_cod: comp.codigo = t_cod.valor
        t_ld = self._eat('TOKEN_LINHA_COMP')
        if not t_ld:
            self.pos += 1; return
        comp.linha_num = t_ld.linha
        m = RE_LINHA_COMP.match(t_ld.valor.strip())
        if not m:
            self.erros.append(f'[Sintático] Linha {t_ld.linha}: linha de componente malformada.')
            return
        comp.periodo   = m.group('periodo')
        comp.flag      = m.group('flag') or ''
        comp.cod_turma = m.group('turma')
        comp.hora_aula = m.group('ha')
        comp.ch        = m.group('ch')
        comp.num_turma = m.group('num_turma')
        comp.frequencia= m.group('freq')
        comp.nota_min  = m.group('nota_min')
        comp.media     = m.group('media')
        comp.situacao  = m.group('situacao')
        
        if comp.situacao == 'MATR' and comp.nota_min != '--':
          self.erros.append(
            f'[Sintático] Linha {t_ld.linha}: {comp.cod_turma} MATR '
            f'mas nota_min="{comp.nota_min}" preenchida.'
          )

        if comp.situacao not in _SEM_NOTA and comp.nota_min == '--':
          self.erros.append(
            f'[Sintático] Linha {t_ld.linha}: {comp.cod_turma} situação '
            f'{comp.situacao} mas notas ausentes.'
          )
        self.h.componentes.append(comp)
        
    def _sumario(self):
        self._tabela_ch(); self._pendentes()

    def _tabela_ch(self):
        t = self._eat_opt('TOKEN_SECAO_CH')
        if not t: return
        for rotulo, obr, opt, comp_, tot in [
            ('Exigido',       'exigido_obrig','exigido_opt','exigido_comp','exigido_total'),
            ('Integralizado', 'integr_obrig', 'integr_opt', 'integr_comp', 'integr_total'),
            ('Pendente',      'pend_obrig',   'pend_opt',   'pend_comp',   'pend_total'),
        ]:
            t_ch = self._eat('TOKEN_LINHA_CH')
            if not t_ch: continue
            m = RE_LINHA_CH.match(t_ch.valor.strip())
            if not m: continue
            if m.group(1) != rotulo:
                self.erros.append(
                    f'[Sintático] Linha {t_ch.linha}: esperado CH "{rotulo}", '
                    f'encontrado "{m.group(1)}".'
                )
            setattr(self.h.ch, obr,   m.group(2) + ' h')
            setattr(self.h.ch, opt,   m.group(3) + ' h')
            setattr(self.h.ch, comp_, m.group(4) + ' h')
            setattr(self.h.ch, tot,   m.group(5) + ' h')

    def _pendentes(self):
        t = self._eat_opt('TOKEN_SECAO_PEND')
        if not t: return
        qtd_declarada = int(t.valor)
        while self._tipo() == 'TOKEN_LINHA_PEND':
            tp = self._eat('TOKEN_LINHA_PEND')
            m = RE_LINHA_PEND.match(tp.valor.strip())
            if m:
                self.h.pendentes.append({
                    'codigo': m.group(1), 'nome': m.group(2).strip(),
                    'ch': m.group(4) + ' h'
                })
        if len(self.h.pendentes) != qtd_declarada:
            self.erros.append(
                f'[Sintático] Pendentes declarados: {qtd_declarada}, '
                f'reconhecidos: {len(self.h.pendentes)}.'
            )

print('✓ Módulo Parser carregado')

"""## 🔍 Módulo 4 — Analisador Semântico"""



_APR      = {'APR', 'APRN'}
_SEM_NOTA = {'MATR', 'CANC', 'TRANC', 'DISP', 'TRANS', 'INCORP', 'CUMP'}

def _f(v):
    if not v or v.strip() == '--': return None
    try: return float(v.replace(',', '.'))
    except ValueError: return None

def _ch_int(v):
    if not v: return None
    m = re.search(r'\d+', v)
    return int(m.group()) if m else None

class AnalisadorSemantico:
    def __init__(self, h, matriz=None):
        self.h = h; 
        self.matriz = matriz
        self.erros = []; 
        self.avisos = []

    def analisar(self):
        self._r01(); self._r02(); self._r03(); self._r04()
        self._r05(); self._r06(); self._r07(); self._r08()
        self._r09(); self._r10(); self._r11(); self._r12()
        self._r13(); self._r14();self._r15()
        return self.erros, self.avisos

    def _r01(self):
        mat = self.h.matricula
        if not mat: self.erros.append('[Semântico] R01: matrícula ausente.'); return
        if not re.fullmatch(r'\d{11}', mat):
            self.erros.append(f'[Semântico] R01: matrícula "{mat}" não tem 11 dígitos.'); return
        ano = int(mat[:4])
        if not (2000 <= ano <= 2099):
            self.erros.append(f'[Semântico] R01: ano da matrícula "{ano}" fora de 2000–2099.')

    def _r02(self):
        dn = self.h.data_nasc
        if not dn: self.avisos.append('[Semântico] R02: data de nascimento não encontrada.'); return
        try:
            dt = datetime.strptime(dn, '%d/%m/%Y')
            idade = (datetime.today() - dt).days // 365
            if not (15 <= idade <= 80):
                self.avisos.append(f'[Semântico] R02: data "{dn}" → idade improvável ({idade} anos).')
        except ValueError:
            self.erros.append(f'[Semântico] R02: data de nascimento "{dn}" inválida.')

    def _r03(self):
        ira = _f(self.h.ira)
        if ira is None: self.avisos.append('[Semântico] R03: IRA não encontrado.'); return
        if not (0.0 <= ira <= 10.0):
            self.erros.append(f'[Semântico] R03: IRA "{self.h.ira}" fora de [0,10].')

    def _r04(self):
        mat = self.h.matricula; pi = self.h.periodo_inicial
        if not mat or not pi: return
        m = re.match(r'(\d{4})\.[12]', pi)
        if m and abs(int(m.group(1)) - int(mat[:4])) > 1:
            self.erros.append(f'[Semântico] R04: período inicial "{pi}" inconsistente com matrícula "{mat[:4]}".')

    def _r05(self):
        for c in self.h.componentes:
            if c.situacao in _SEM_NOTA: continue
            freq = _f(c.frequencia)
            if freq is not None and not (0.0 <= freq <= 100.0):
                self.erros.append(f'[Semântico] R05: {c.cod_turma} ({c.periodo}) freq "{c.frequencia}" fora de [0,100].')

    def _r06(self):
        for c in self.h.componentes:
            if c.situacao in _SEM_NOTA: continue
            for label, val in [('nota_min', c.nota_min), ('média', c.media)]:
                n = _f(val)
                if n is not None and not (0.0 <= n <= 10.0):
                    self.erros.append(f'[Semântico] R06: {c.cod_turma} ({c.periodo}) {label}="{val}" fora de [0,10].')

    def _r07(self):
        for c in self.h.componentes:
            med = _f(c.media)
            if c.situacao == 'APR' and med is not None and med < 6.0:
                self.erros.append(f'[Semântico] R07: {c.cod_turma} ({c.periodo}) APR mas média {med:.1f} < 6.0.')
            if c.situacao == 'APRN' and med is not None and not (6.0 <= med < 7.0):
                self.erros.append(f'[Semântico] R07: {c.cod_turma} ({c.periodo}) APRN mas média {med:.1f} ∉ [6.0,7.0).')

    def _r08(self):
        for c in self.h.componentes:
            if c.situacao in ('REP', 'REPMF'):
                med = _f(c.media)
                if med is not None and med >= 6.0:
                    self.erros.append(f'[Semântico] R08: {c.cod_turma} ({c.periodo}) {c.situacao} mas média {med:.1f} ≥ 6.0.')

    def _r09(self):
        for c in self.h.componentes:
            if c.situacao in ('REPF', 'REPMF', 'REPNF'):
                freq = _f(c.frequencia)
                if freq is not None and freq >= 75.0:
                    self.erros.append(f'[Semântico] R09: {c.cod_turma} ({c.periodo}) {c.situacao} mas freq {freq:.1f}% ≥ 75%.')

    def _r10(self):
        for c in self.h.componentes:
            if c.situacao == 'MATR':
                if _f(c.nota_min) is not None:
                    self.erros.append(f'[Semântico] R10: {c.cod_turma} ({c.periodo}) MATR mas nota_min preenchida.')
                if _f(c.media) is not None:
                    self.erros.append(f'[Semântico] R10: {c.cod_turma} ({c.periodo}) MATR mas média preenchida.')

    def _r11(self):
        for c in self.h.componentes:
            if c.situacao in _SEM_NOTA: continue
            nm = _f(c.nota_min); med = _f(c.media)
            if nm is not None and med is not None and nm > med + 0.05:
                self.erros.append(f'[Semântico] R11: {c.cod_turma} ({c.periodo}) nota_min {nm} > média {med}.')

    def _r12(self):
        for label, i_s, e_s in [
            ('Obrigatórias', self.h.ch.integr_obrig, self.h.ch.exigido_obrig),
            ('Optativos',    self.h.ch.integr_opt,   self.h.ch.exigido_opt),
            ('Total',        self.h.ch.integr_total,  self.h.ch.exigido_total),
        ]:
            i = _ch_int(i_s); e = _ch_int(e_s)
            if i and e and i > e:
                self.erros.append(f'[Semântico] R12: CH integralizada de {label} ({i}h) excede exigida ({e}h).')

    def _r13(self):
        ira_d = _f(self.h.ira)
        if ira_d is None: return
        notas = [_f(c.media) for c in self.h.componentes if c.situacao in _APR and _f(c.media)]
        if not notas: return
        ira_c = sum(notas) / len(notas)
        if abs(ira_c - ira_d) > 0.5:
            self.avisos.append(f'[Semântico] R13: IRA declarado ({ira_d:.4f}) difere da média simples ({ira_c:.4f}) — verifique pesos por CH.')

    def _r14(self):
        pa = self.h.periodo_atual
        if not pa: return
        try:
            p = int(pa)
            if not (1 <= p <= 20):
                self.erros.append(f'[Semântico] R14: período atual {p} fora de [1,20].')
        except ValueError:
            self.erros.append(f'[Semântico] R14: período atual "{pa}" não é inteiro.')
    def _r15(self):
        if not self.matriz: 
          return
        
        codigos_matriz = set(self.matriz.keys())
        
        for componente in self.h.componentes:
          if not componente.codigo:
            continue
          if componente.codigo not in codigos_matriz:
            
            self.erros.append(
                f'[Semântico] R15: disciplina "{componente.codigo}" não encontrada na matriz curricular.'
            )

print('✓ Módulo Semântico carregado')

"""## 🖨️ Módulo 5 — Exibição de resultados"""

SEP = '═' * 65

def exibir_dados(hist):
    print(f'\n{SEP}')
    print(' DADOS PESSOAIS')
    print(SEP)
    print(f'  Nome        : {hist.nome}')
    print(f'  Matrícula   : {hist.matricula}')
    print(f'  Nascimento  : {hist.data_nasc}')
    print(f'  CPF         : {hist.cpf}')

    print(f'\n{SEP}')
    print(' DADOS DO VÍNCULO')
    print(SEP)
    print(f'  Curso        : {hist.curso}')
    print(f'  Status       : {hist.status}')
    print(f'  IRA          : {hist.ira}')
    print(f'  Currículo    : {hist.curriculo}')
    print(f'  Ingresso     : {hist.ingresso}  |  Período inicial: {hist.periodo_inicial}')
    print(f'  Período atual: {hist.periodo_atual}')

    print(f'\n{SEP}')
    print(f' COMPONENTES CURRICULARES ({len(hist.componentes)} total)')
    print(SEP)
    print(f'  {"Período":<8} {"Turma":<10} {"CH":>4} {"Freq%":>7} {"NMín":>6} {"Média":>6}  Sit   Flag')
    print(f'  {"-"*7} {"-"*9} {"-"*4} {"-"*7} {"-"*6} {"-"*6}  {"-"*4}  {"-"*4}')
    for c in hist.componentes:
        print(f'  {c.periodo:<8} {c.cod_turma:<10} {c.ch:>4} {c.frequencia:>7} '
              f'{c.nota_min:>6} {c.media:>6}  {c.situacao:<4}  {c.flag}')

    ch = hist.ch
    print(f'\n{SEP}')
    print(' CARGA HORÁRIA INTEGRALIZADA / PENDENTE')
    print(SEP)
    print(f'  {"":14} {"Obrig.":>8} {"Optativ.":>9} {"Compl.":>7} {"Total":>7}')
    print(f'  {"Exigido":<14} {ch.exigido_obrig:>8} {ch.exigido_opt:>9} {ch.exigido_comp:>7} {ch.exigido_total:>7}')
    print(f'  {"Integralizado":<14} {ch.integr_obrig:>8} {ch.integr_opt:>9} {ch.integr_comp:>7} {ch.integr_total:>7}')
    print(f'  {"Pendente":<14} {ch.pend_obrig:>8} {ch.pend_opt:>9} {ch.pend_comp:>7} {ch.pend_total:>7}')

    if hist.pendentes:
        print(f'\n{SEP}')
        print(f' COMPONENTES OBRIGATÓRIOS PENDENTES ({len(hist.pendentes)})')
        print(SEP)
        for p in hist.pendentes:
            print(f'  [{p["codigo"]}] {p["nome"]}  {p["ch"]}')
    print(f'\n{SEP}\n')

print('✓ Módulo de exibição carregado')


"""### ▶️ Rodar análise completa"""

def analisar_historico(caminho_pdf, injetar_erros=False, mostrar_tokens=False):
    print(f'\n{SEP}')
    print(f'  ANALISADOR DE HISTÓRICO ESCOLAR — UERN/CAN')
    print(f'  Arquivo: {caminho_pdf}')
    print(f'{SEP}\n')

    # ── Fase 0: Extração ─────────────────────────────────────────────────
    print('► Fase 0 — Extração do PDF...')
    texto, avisos_extr = extrair_texto(caminho_pdf)
    for av in avisos_extr: print(f'  ⚠  {av}')
    if not texto:
        print('  ✗ Falha na extração — abortando.'); return
    print(f'  ✓ {len(texto)} caracteres extraídos\n')

    if injetar_erros:
        print('  ⚠  Modo de erros: injetando inconsistências propositais...\n')
        texto = texto.replace('2023.2 NCC0116 90 90 01 100,0 10.0 10.0 APR',
                              '2023.2 NCC0116 90 90 01 100,0 6.5 6.5 APR', 1)
        texto = texto.replace('2023.1 NCC0108 30 30 01 100,0 9.0 9.3 APR',
                              '2023.1 NCC0108 30 30 01 101,0 9.0 9.3 APR', 1)
        texto = texto.replace('2023.2 NCC0217 60 91 01  91,0 6.8 7.6 APR',
                              '2023.2 NCC0217 60 91 01  91,0 8.0 7.6 APR', 1)

    # ── Fase 1: Léxica ───────────────────────────────────────────────────
    print('► Fase 1 — Análise Léxica...')
    tokens, erros_lex = tokenizar(texto)
    print(f'  ✓ {len(tokens)} tokens  |  {len(erros_lex)} erro(s) léxico(s)')
    for e in erros_lex: print(f'  ✗ {e}')
    if mostrar_tokens:
        print(f'\n  {"TIPO":<28} {"VALOR":<35} {"LINHA":>5}')
        print(f'  {"-"*68}')
        for t in tokens:
            val = t.valor if len(t.valor) <= 35 else t.valor[:32] + '...'
            print(f'  {t.tipo:<28} {val:<35} {t.linha:>5}')
    print()

    # ── Fase 2: Sintática ────────────────────────────────────────────────
    print('► Fase 2 — Análise Sintática...')
    sint = Parser(tokens)
    historico = sint.parse()
    erros_sint = sint.erros
    print(f'  ✓ {len(historico.componentes)} componentes  |  {len(erros_sint)} erro(s) sintático(s)')
    for e in erros_sint: print(f'  ✗ {e}')
    print()

    # ── Fase 3: Semântica ────────────────────────────────────────────────
    print('► Fase 3 — Análise Semântica...')
    sem = AnalisadorSemantico(historico)
    erros_sem, avisos_sem = sem.analisar()
    print(f'  ✓ {len(erros_sem)} erro(s)  |  {len(avisos_sem)} aviso(s)')
    for e in erros_sem: print(f'  ✗ {e}')
    for av in avisos_sem: print(f'  ⚠  {av}')
    print()

    # ── Resultado ────────────────────────────────────────────────────────
    todos_erros = erros_lex + erros_sint + erros_sem
    print(f'{SEP}')
    print(' RESULTADO DA ANÁLISE')
    print(f'{SEP}')
    if todos_erros:
        print(f'\n  ✗ HISTÓRICO INVÁLIDO — {len(todos_erros)} erro(s):\n')
        for i, e in enumerate(todos_erros, 1):
            print(f'  {i:2d}. {e}')
        print()
    else:
        print('\n  ✓ HISTÓRICO VÁLIDO — nenhum erro encontrado.\n')
        exibir_dados(historico)

    if avisos_sem:
        print(f'  ⚠  Avisos ({len(avisos_sem)}):')
        for av in avisos_sem: print(f'     • {av}')
    return{
      "historico": historico,
      "erros_lexicos": erros_lex,
      "erros_sintaticos": erros_sint,
      "erros_semanticos": erros_sem,
      "avisos": avisos_sem,
      "valido": len(todos_erros) == 0
    }


def analisar_historico_gui(caminho_pdf, caminho_matriz=None):

    try:

        texto, avisos_extr = extrair_texto(caminho_pdf)

        if not texto:
            return {
                "valido": False,
                "erro_fatal": avisos_extr
            }

        tokens, erros_lex = tokenizar(texto)

        parser = Parser(tokens)
        historico = parser.parse()

        erros_sint = parser.erros

        sem = AnalisadorSemantico(historico)
        erros_sem, avisos_sem = sem.analisar()

        todos = erros_lex + erros_sint + erros_sem

        return {
            "valido": len(todos) == 0,
            "historico": historico,
            "tokens": tokens,
            "erros_lexicos": erros_lex,
            "erros_sintaticos": erros_sint,
            "erros_semanticos": erros_sem,
            "avisos": avisos_sem,
            "avisos_extracao": avisos_extr
        }

    except Exception as e:

        return {
            "valido": False,
            "erro_fatal": [str(e)]
        }
        
