# Escola Sabatina Kids (PWA)

App para as crianças da igreja: lições infantis da Escola Sabatina **em português**, com ilustrações, leitura em voz alta, estrelinhas e uso offline.

## De onde vêm as lições
O repositório Adventech/sabbath-school-lessons **não tem lições infantis em português**. Ele tem, **só em inglês** e em **PDF**:
Iniciantes (*Beginner*), Jardim (*Kindergarten*), Primários (*Primary*) e Juvenis em slides (*Junior PowerPoints*).
Por isso o workflow `.github/workflows/atualizar.yml` (todo dia) usa `tools/atualizar_kids.py` para:
1. achar o trimestre mais recente de cada turma;
2. baixar o PDF de cada lição, tirar o texto e as ilustrações;
3. **traduzir o texto automaticamente do inglês para o português** (Google via *deep-translator*, com MyMemory de reserva);
4. gravar tudo em `kids/` e `data/kids.json`, que o app lê.

O app ainda tem um tradutor de reserva: se algum trecho ficar sem tradução, ele traduz no aparelho (MyMemory).

## Publicar
1. Envie todos os arquivos (inclusive `.github/`) para um repositório.
2. Settings → Pages → *Deploy from a branch* → `main` / `(root)`.
3. Settings → Actions → General → *Workflow permissions* → **Read and write**.
4. **Actions → Atualizar lições infantis → Run workflow** (a primeira vez demora, pois traduz tudo).
5. Abra `https://SEU-USUARIO.github.io/NOME-DO-REPO/` e use "Adicionar à tela inicial".

## Corrigir traduções
Tradução automática erra. Para corrigir, coloque em `kids/revisao.json` o texto em inglês e a versão certa:
```json
{"Two Birth Announcements": "Dois anúncios de nascimento", "frase em inglês exatamente como aparece": "frase corrigida"}
```
Depois rode o workflow com **Refazer todas as lições**. As correções têm prioridade sobre o tradutor.

## Imagens
As ilustrações dos PDFs aparecem junto do texto. Se uma página tiver letras dentro da imagem (atividades, cartazes), elas **não** são traduzidas: use o botão **📄 Páginas originais** para ver a página inteira.

## Observações
- O trimestre atual das turmas Iniciantes, Jardim e Primários ainda não está no repositório (só o 3º trimestre de 2026). O app mostra o que existe e avisa. Os Juvenis (slides) já estão no 4º trimestre.
- Para o 4º trimestre, o app e o workflow pegam sozinhos quando for publicado.
- **Material oficial em português:** a CPB publica os manuais das lições infantojuvenis em português em mais.cpb.com.br (seção de PDFs). Para o professor, vale preferir esse material.
- O conteúdo pertence à Associação Geral e à CPB. Verifique as condições de uso antes de divulgar publicamente.
