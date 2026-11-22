# Escola Sabatina Kids — lições infantis em português (PWA)

Puxa as lições infantojuvenis do **Alive in Jesus** (Beginner, Jardim, Primários e, se existir, Juniores), **baixa as figuras**, **traduz do inglês para o português** e mostra num app colorido para as crianças, com leitura em voz alta, estrelinhas de progresso e uso offline.

## Como funciona
1. O workflow `.github/workflows/infantil.yml` roda 2 vezes por dia no GitHub Actions.
2. `tools/gerar_infantil.py` busca o JSON de cada semana em
   `https://sabbath-school.adventech.io/api/v3/en/aij/AAAA-0T-NN/SS/index.json`
   (`AAAA-0T` = trimestre, `NN` = `bg`, `kd`, `pr`, `jr`; `SS` = semana 01–13).
3. As figuras vão para `img/infantil/`, o texto traduzido (e o original em inglês) para `data/infantil/`.
4. O app (`index.html`) lê esses arquivos. Botão **"Ver em inglês"** serve para o professor conferir a tradução.

## Publicar no GitHub Pages
1. Crie um repositório e envie **todos** os arquivos (inclusive `.github/`, `tools/`, `data/` e `img/`).
2. Settings → Pages → *Deploy from a branch* → `main` / `(root)`.
3. Settings → Actions → General → *Workflow permissions* → **Read and write**.
4. Actions → **Atualizar lições infantis** → *Run workflow* (primeira vez; leva alguns minutos).
5. Abra `https://SEU-USUARIO.github.io/NOME-DO-REPO/` e use "Adicionar à tela inicial".

## Tradução melhor (opcional)
Sem configurar nada, usa o Google Tradutor gratuito. Para traduzir com o Claude (linguagem mais simples e nomes bíblicos corretos), crie o segredo **ANTHROPIC_API_KEY** em Settings → Secrets and variables → Actions. Opcional: variável `CLAUDE_MODEL`.
Traduções ficam em cache (`data/infantil/_traducao.json`), então cada texto é traduzido uma vez só. Se quiser corrigir uma frase, edite esse arquivo e rode o workflow.

## Rodar no computador
```
python tools/gerar_infantil.py              # trimestre atual (e o próximo, se já existir)
python tools/gerar_infantil.py 2026-04 pr   # um trimestre e nível
python -m http.server 8000                  # abrir http://localhost:8000
```

## Observações importantes
- **Direitos autorais:** o texto e as figuras pertencem à Associação Geral da IASD / Adventech. Use na sua igreja e confirme a permissão antes de divulgar publicamente. Como o workflow salva o conteúdo no repositório, prefira repositório **privado** ou mantenha o link do app restrito à igreja.
- Os textos bíblicos em várias versões (que a API traz embutidos) são ignorados; ficam só o texto da lição, as listas, os títulos e as figuras.
- A tradução é automática: vale uma revisão rápida do professor, principalmente nas perguntas e atividades.
- O endereço da API e a forma do JSON foram observados na página de uma lição (`2026-04-pr/05`). Se a Adventech mudar o formato, ajuste `blocos()` em `tools/gerar_infantil.py`.
- Códigos de nível (`bg`, `kd`, `pr`) vieram dos links que você enviou; `jr` é tentativa e é ignorado se não existir. Edite `NIVEIS` no script para ajustar.
