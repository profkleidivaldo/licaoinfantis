#!/usr/bin/env python3
"""Gera data/kids.json e kids/* a partir dos PDFs infantis do repositório Adventech/sabbath-school-lessons.

Para cada turma (Iniciantes, Jardim, Primários, Juvenis) usa o trimestre mais recente publicado, baixa o PDF de cada
lição, extrai texto e ilustrações e traduz o texto do inglês para o português.

Uso (na raiz do projeto):   python tools/atualizar_kids.py [--forcar] [--sem-pdf] [--repo CAMINHO]
  --sem-pdf  só monta o índice (títulos, datas, capas), sem baixar PDFs nem traduzir.
Correções de tradução: coloque  "texto em inglês": "texto corrigido"  em kids/revisao.json (têm prioridade).
"""
import argparse, hashlib, io, json, os, re, shutil, subprocess, tempfile, time, urllib.request
from collections import Counter
import yaml
from PIL import Image

UA = {'User-Agent': 'Mozilla/5.0'}
REPO = 'https://github.com/Adventech/sabbath-school-lessons.git'
GRUPOS = {  # id: (nome, idade, emoji, cor, padrão da pasta no repositório)
    'bg': ('Iniciantes', '1 a 3 anos', '🐣', '#ff7eb6', r'(\d{4}-\d{2})-z[a-d]ijbgsg'),
    'kd': ('Jardim da Infância', '4 a 5 anos', '🌼', '#4fc77a', r'(\d{4}-\d{2})-z[a-d]ijkdsg'),
    'pr': ('Primários', '6 a 9 anos', '🚀', '#3d9bff', r'(\d{4}-\d{2})-z[a-d]ijprsg'),
    'pp': ('Juvenis (slides)', '10 a 14 anos', '⭐', '#9b7bff', r'(\d{4}-\d{2})-pp'),
}
lerjson = lambda p, d: json.load(open(p, encoding='utf8')) if os.path.exists(p) else d
def gravar(p, o):
    os.makedirs(os.path.dirname(p) or '.', exist_ok=True)
    json.dump(o, open(p, 'w', encoding='utf8'), ensure_ascii=False, separators=(',', ':'))

class Trad:
    """Tradutor en→pt: revisão manual > cache > Google (deep-translator) > MyMemory."""
    def __init__(self, ativo=True):
        self.man = {**lerjson('tools/titulos_pt.json', {}), **lerjson('kids/revisao.json', {})}
        self.cache = lerjson('kids/_cache.json', {}); self.ativo = ativo; self.mock = os.environ.get('KIDS_MOCK'); self.falhas = 0
    def partes(self, t, n):
        out, cur = [], ''
        for s in re.findall(r'[^.!?]+[.!?]*\s*', t) or [t]:
            if len(cur) + len(s) > n and cur: out.append(cur); cur = ''
            cur += s
        return out + ([cur] if cur else [])
    def um(self, t):
        t = t.strip()
        if not re.search(r'[A-Za-z]{2}', t): return t
        if t in self.man: return self.man[t]
        if t in self.cache: return self.cache[t]
        if not self.ativo: return ''
        if self.mock: return '[PT] ' + t
        r = ''
        try:
            from deep_translator import GoogleTranslator
            r = ' '.join(GoogleTranslator(source='en', target='pt').translate(p) or '' for p in self.partes(t, 4500)).strip(); time.sleep(.25)
        except Exception as e:
            try:
                from deep_translator import MyMemoryTranslator
                r = ' '.join(MyMemoryTranslator(source='en-US', target='pt-BR').translate(p) or '' for p in self.partes(t, 450)).strip()
            except Exception as e2: self.falhas += 1; print('  tradução falhou:', str(e2)[:80])
        if r: self.cache[t] = r
        return r
    def salvar(self): gravar('kids/_cache.json', self.cache)

def limpar(t):
    t = re.sub(r'(?<=[a-z])- (?=[a-z])', '', t.replace('\u00ad', ''))
    return re.sub(r'\s+', ' ', t).strip()

def salvar_img(raw, pasta, vistos):
    h = hashlib.md5(raw).hexdigest()[:10]
    if h in vistos: return None
    try:
        im = Image.open(io.BytesIO(raw)); im.load()
        if im.mode in ('RGBA', 'LA', 'P'):
            im = im.convert('RGBA'); f = Image.new('RGB', im.size, 'white'); f.paste(im, mask=im.split()[3]); im = f
        else: im = im.convert('RGB')
        im.thumbnail((720, 720)); im.save(os.path.join(pasta, h + '.jpg'), 'JPEG', quality=74, optimize=True, progressive=True)
    except Exception: return None
    vistos.add(h); return f'{pasta}/{h}.jpg'

def processar_pdf(caminho, pasta, prefixo):
    """PDF -> lista de páginas com blocos de texto (en) e ilustrações, mais a imagem da página original."""
    try: import pymupdf as fitz
    except ImportError: import fitz
    os.makedirs(pasta, exist_ok=True); doc = fitz.open(caminho); paginas = []; tam = []
    for pg in doc:
        its = []
        for b in pg.get_text('dict')['blocks']:
            if b['type'] == 0:
                sp = [s for l in b['lines'] for s in l['spans'] if s['text'].strip()]
                txt = limpar(' '.join(s['text'] for s in sp)) if sp else ''
                if not txt or re.fullmatch(r'[\d\W_]+', txt): continue
                tam += [max(s['size'] for s in sp)] * len(txt); its.append([b['bbox'][1], b['bbox'][0], 'p', txt, max(s['size'] for s in sp)])
            elif b['type'] == 1 and b.get('image') and min(b.get('width', 0), b.get('height', 0)) >= 100:
                its.append([b['bbox'][1], b['bbox'][0], 'img', b['image'], 0])
        its.sort(key=lambda t: (round(t[0] / 14), t[1])); paginas.append((pg, its))
    med = sorted(tam)[len(tam) // 2] if tam else 11
    rep = {t for t, n in Counter(i[3] for _, its in paginas for i in its if i[2] == 'p').items() if n >= 3 and n >= .4 * len(paginas) and len(t) < 90}
    imgrep = {h for h, n in Counter(hashlib.md5(i[3]).hexdigest() for _, its in paginas for i in its if i[2] == 'img').items() if n >= 3}
    vistos, out = set(), []
    for k, (pg, its) in enumerate(paginas, 1):
        blocos = []
        for y, x, t, v, sz in its:
            if t == 'p':
                if v not in rep: blocos.append({'t': 'h' if sz >= 1.3 * med else 'p', 'en': v})
            elif hashlib.md5(v).hexdigest() not in imgrep:
                s = salvar_img(v, pasta, vistos)
                if s: blocos.append({'t': 'img', 'src': s})
        pix = pg.get_pixmap(dpi=80, alpha=False); nome = f'{pasta}/{prefixo}-p{k}.jpg'
        Image.frombytes('RGB', (pix.width, pix.height), pix.samples).save(nome, 'JPEG', quality=60, optimize=True)
        out.append({'img': nome, 'blocos': blocos})
    return out

def baixar(url, dest):
    d = os.environ.get('KIDS_PDF_DIR')
    if d: return shutil.copy(os.path.join(d, os.path.basename(url)), dest)
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=90) as r, open(dest, 'wb') as f: shutil.copyfileobj(r, f)

def assinatura(url):
    d = os.environ.get('KIDS_PDF_DIR')
    if d: return str(os.path.getsize(os.path.join(d, os.path.basename(url))))
    try:
        r = urllib.request.urlopen(urllib.request.Request(url, headers=UA, method='HEAD'), timeout=30)
        return (r.headers.get('ETag') or '') + (r.headers.get('Content-Length') or '')
    except Exception: return ''

def git(repo, *a): return subprocess.run(['git', '-C', repo, *a], capture_output=True, text=True, check=True).stdout

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--forcar', action='store_true'); ap.add_argument('--sem-pdf', action='store_true'); ap.add_argument('--repo')
    a = ap.parse_args(); repo = a.repo
    if not repo:
        repo = tempfile.mkdtemp(); subprocess.run(['git', 'clone', '--depth', '1', '--filter=blob:none', '--sparse', REPO, repo], check=True)
    nomes = [n.split('/')[-1] for n in git(repo, 'ls-tree', '--name-only', 'HEAD', 'src/en/').split()]
    achados = {}
    for g, (_, _, _, _, pad) in GRUPOS.items():
        c = sorted((n for n in nomes if re.fullmatch(pad, n)), reverse=True)
        if c: achados[g] = c[0]
    git(repo, 'sparse-checkout', 'set', *[f'src/en/{n}' for n in achados.values()])
    tr = Trad(not a.sem_pdf); idx = {'atualizado': time.strftime('%Y-%m-%d'), 'grupos': []}
    for g in GRUPOS:
        if g not in achados: continue
        nome, idade, emoji, cor, _ = GRUPOS[g]; d = f'{repo}/src/en/{achados[g]}'; qid = achados[g][:7]; pasta = f'kids/{qid}-{g}'
        info = yaml.safe_load(open(d + '/info.yml', encoding='utf8')); pdfs = yaml.safe_load(open(d + '/pdf.yml', encoding='utf8'))['pdf']
        titulo = re.sub(r'^Student[^:]*:\s*', '', info['title']); os.makedirs(pasta, exist_ok=True)
        im = Image.open(d + '/cover.png').convert('RGB'); im.thumbnail((480, 720)); im.save(pasta + '/cover.jpg', 'JPEG', quality=80)
        sem, vistos = [], set()
        for e in pdfs:
            n = e['target'].split('/')[-1]
            if not re.fullmatch(r'\d\d', n) or e['title'] in ('Teacher', 'Parents') or n in vistos: continue
            vistos.add(n); arq = f'{pasta}/{n}.json'; les = lerjson(arq, None); sig = assinatura(e['src']) if not a.sem_pdf else ''
            if not a.sem_pdf and (a.forcar or not les or les.get('sig') != sig or sig == ''):
                try:
                    with tempfile.TemporaryDirectory() as tmp:
                        pf = tmp + '/l.pdf'; baixar(e['src'], pf); pgs = processar_pdf(pf, pasta, n)
                    for p in pgs:
                        for b in p['blocos']:
                            if b['t'] != 'img': b['pt'] = tr.um(b['en'])
                    les = {'titulo': e['title'], 'titulo_pt': tr.um(e['title']), 'sig': sig, 'paginas': pgs}; gravar(arq, les); tr.salvar()
                    print(f'  {g} lição {n}: {len(pgs)} páginas, {sum(len(p["blocos"]) for p in pgs)} blocos')
                except Exception as ex: print(f'  {g} lição {n}: FALHOU ({ex})')
            sem.append({'n': int(n), 'titulo': e['title'], 'titulo_pt': tr.um(e['title']) or e['title'], 'inicio': e['start_date'], 'fim': e['end_date'], 'pdf': e['src'], 'arquivo': arq if os.path.exists(arq) else None})
        for old in os.listdir('kids') if os.path.isdir('kids') else []:  # remove trimestres antigos da mesma turma
            if old.endswith('-' + g) and old != f'{qid}-{g}': shutil.rmtree('kids/' + old, ignore_errors=True)
        idx['grupos'].append({'id': g, 'nome': nome, 'idade': idade, 'emoji': emoji, 'cor': cor, 'trimestre': qid, 'rotulo': f'{int(qid[5:])}º trimestre de {qid[:4]}',
                              'titulo': titulo, 'titulo_pt': tr.um(titulo) or titulo, 'capa': pasta + '/cover.jpg', 'semanas': sem})
    tr.salvar(); gravar('data/kids.json', idx)
    print('data/kids.json:', ', '.join(f"{x['id']} {x['trimestre']} ({len(x['semanas'])} lições)" for x in idx['grupos']), '| falhas de tradução:', tr.falhas)

if __name__ == '__main__': main()
