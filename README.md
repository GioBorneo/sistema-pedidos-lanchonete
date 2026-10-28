# Sistema de Pedidos da Lanchonete

Trabalho Prático Integrador — Programação de Software Básico em C.

Sistema de gerenciamento e monitoramento de pedidos de uma lanchonete. O projeto completo prevê processos (`fork`), threads (`pthreads`), comunicação entre processos (pipe) e persistência em arquivo.

## Status atual

**Fase 4** — módulo de histórico (RF10) implementado, com gravação e consulta pela opção 7. A integração com o preparo dos pedidos será feita na fase 5. Compilação e execução das fases 3 e 4 ainda precisam ser verificadas no Codespaces; o ambiente local usado na implementação não possui compilador C.

- Fase 1: menu principal navegável — concluída.
- Fase 2: cadastro, listagem e consulta de pedidos (RF01-03) — concluída.
- Fase 3: módulo `arquivo.c/h`, opções 9 e 10 e testes de persistência — implementada, aguardando execução dos testes.
- Fase 4: módulo `log.c/h`, opção 7 e testes de histórico — implementada, aguardando execução dos testes e integração com o preparo.
- Opções 4, 5, 6 e 8 continuam reservadas. A próxima etapa prevista é preparar pedido sequencialmente (RF04), medindo o tempo e registrando o resultado no histórico, mediante autorização.

## Como rodar (GitHub Codespaces)

1. No repositório no GitHub, selecione a branch que contém a fase desejada e abra **Code > Codespaces** para criar ou acessar o ambiente dessa branch.
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

## Histórico de pedidos (fase 4)

A opção **7 — Ver histórico** mostra o conteúdo de `dados/historico.txt`. Se o arquivo ainda não existir ou estiver vazio, informa que não há histórico; consultar não cria nem altera o arquivo.

O módulo `log.c/h` disponibiliza `registrarLog(idPedido, status, tempoExecucao)` e `exibirHistorico()`, com retorno `1` para sucesso e `0` para erro. A gravação acrescenta linhas (modo append), sem apagar as anteriores. Exemplo de formato:

```text
28/10/2026 14:30:00 | PID=5231 | PEDIDO=3 | STATUS=PRONTO | TEMPO=2.001 s
```

- Data/hora e PID são obtidos do sistema no momento da gravação.
- Status usa os estados existentes: `PENDENTE` ou `PRONTO`.
- O tempo é a duração real em segundos, com três casas decimais, que deverá ser medida e fornecida pelo módulo de preparo. Não é apenas o valor previsto em `tempoPreparo`.
- Duração negativa, infinita, NaN e status desconhecido são rejeitados. Falhas de abertura, leitura, escrita e fechamento são informadas.
- O histórico gerado é ignorado pelo Git. O programa deve ser executado na raiz do projeto, com a pasta `dados/` existente.

**Nesta fase ainda não há registros reais gerados pelo menu:** a opção 4 não prepara pedidos. A função de gravação será chamada na fase 5, após implementar o preparo sequencial. Cadastro, salvamento e carregamento não criam eventos de execução. Os dados usados nos testes existem somente em pastas temporárias.

O módulo tem como alvo Linux/POSIX (`getpid` e `localtime_r`). A sincronização de gravações será avaliada quando houver processos e threads; append não representa garantia de gravação indivisível ou recuperação de uma escrita parcial.

Para verificar o estado atual da interface, execute `make`, abra `./programa` e escolha 7. Sem um histórico existente, o resultado esperado é `Nenhum historico registrado.`

## Testes de persistência

No Codespaces/Linux com GCC e Python 3, na raiz do projeto:

```bash
python3 tests/test_persistencia.py
```

O teste compila com `-Wall -Wextra -Werror -pthread` e utiliza diretórios temporários, sem alterar os pedidos reais. Cobre salvamento entre sessões, preservação do status, substituição da lista, erros de arquivo, formatos inválidos, IDs repetidos, limites, CRLF e arquivo vazio. Se não houver GCC, informa que os testes foram pulados; isso não significa que o programa foi validado.

## Testes do histórico

```bash
python3 tests/test_logs.py
```

A suíte compila a aplicação e um pequeno programa de teste temporário para chamar a gravação sem antecipar o preparo no menu. Verifica append, data/hora, PID, formato, validação de parâmetros, consulta inexistente/vazia, opção 7 e erros de E/S. Também verifica que cadastro, salvamento e carregamento não geram logs de execução. Não altera os arquivos reais em `dados/`.

Para rodar as duas suítes:

```bash
python3 -m unittest discover -s tests -v
```

A compilação e a execução dos testes dependem de GCC e Linux/POSIX. Se forem pulados por ausência de GCC, a validação continua pendente.
