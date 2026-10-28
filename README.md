# Sistema de Pedidos da Lanchonete

Trabalho Prático Integrador — Programação de Software Básico em C.

Sistema de gerenciamento e monitoramento de pedidos de uma lanchonete. O projeto completo prevê processos (`fork`), threads (`pthreads`), comunicação entre processos (pipe) e persistência em arquivo.

## Status atual

**Fase 3** — salvamento e carregamento em TXT (RF05-06) implementados. Compilação e execução desta fase ainda precisam ser verificadas no Codespaces; o ambiente local usado na implementação não possui compilador C.

- Fase 1: menu principal navegável — concluída.
- Fase 2: cadastro, listagem e consulta de pedidos (RF01-03) — concluída.
- Fase 3: módulo `arquivo.c/h`, opções 9 e 10 e testes de persistência — implementada, aguardando execução dos testes.
- Opções 4 a 8 continuam reservadas para etapas posteriores. A próxima etapa prevista é o histórico de pedidos (logs), mediante autorização.

## Como rodar (GitHub Codespaces)

1. No repositório no GitHub, clique em **Code > Codespaces > Create codespace on main**.
2. Aguarde o ambiente carregar (já vem com `gcc`/`make` configurados).
3. Na pasta do projeto, rode:
   ```bash
   make
   ./programa
   ```

Execute o programa na raiz do projeto, onde está a pasta `dados/`.

## Persistência em TXT

Durante a execução, os pedidos ficam em um vetor de structs na memória RAM. A opção **9 — Salvar pedidos** grava esse vetor em `dados/pedidos.txt`. A opção **10 — Carregar pedidos** recupera os dados para o vetor.

O arquivo contém um pedido por linha, sem cabeçalho:

```text
1;X-burger e suco;2;0
2;Batata frita;1;1
```

Os campos são `ID;descricao;tempoPreparo;status`. O tempo está em segundos; status `0` significa **PENDENTE** e `1`, **PRONTO**.

**Por que TXT?** É legível em qualquer editor e permite demonstrar a gravação e recuperação usando apenas a biblioteca padrão de C, sem dependências externas. O ponto e vírgula separa os campos, por isso não pode aparecer na descrição. A descrição aceita até 99 bytes (caracteres acentuados podem ocupar mais de um byte em UTF-8).

### Comportamento das operações

- Salvar é manual e **substitui o conteúdo anterior** do arquivo. Salvar sem pedidos gera um arquivo vazio.
- Encerrar não salva automaticamente. Ao abrir novamente, use a opção 10 para recuperar os dados.
- Carregar **substitui** os pedidos da sessão; não acrescenta à lista existente. Um arquivo vazio carrega zero pedidos.
- A leitura usa um vetor temporário: arquivo inexistente, inválido, com IDs repetidos ou com mais de 50 pedidos não substitui a lista atual.
- Erros de abertura, leitura, escrita e fechamento são informados. O salvamento não mantém backup: uma falha depois da abertura para escrita pode deixar o arquivo incompleto.
- O TXT gerado é ignorado pelo Git; a pasta `dados/` é mantida por `.gitkeep`.

## Demonstração da fase 3

1. Execute `make` e `./programa`.
2. Cadastre dois pedidos usando a opção 1.
3. Use a opção 9 e confira `dados/pedidos.txt` no editor.
4. Saia com a opção 0 e execute `./programa` novamente.
5. Use a opção 2: inicialmente a lista estará vazia.
6. Use a opção 10 e depois as opções 2 e 3: os pedidos salvos devem reaparecer.

## Testes de persistência

No Codespaces/Linux com GCC e Python 3, na raiz do projeto:

```bash
python3 tests/test_persistencia.py
```

O teste compila com `-Wall -Wextra -Werror -pthread` e utiliza diretórios temporários, sem alterar os pedidos reais. Cobre salvamento entre sessões, preservação do status, substituição da lista, erros de arquivo, formatos inválidos, IDs repetidos, limites, CRLF e arquivo vazio. Se não houver GCC, informa que os testes foram pulados; isso não significa que o programa foi validado.
