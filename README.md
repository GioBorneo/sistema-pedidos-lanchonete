# Sistema de Pedidos da Lanchonete

Trabalho Prático Integrador — Programação de Software Básico em C.

Sistema de gerenciamento e monitoramento de pedidos de uma lanchonete. O projeto completo prevê processos (`fork`), threads (`pthreads`), comunicação entre processos (pipe) e persistência em arquivo.

## Status atual

**Fase 7** — preparo de dois pedidos com threads (RF09) implementado pela opção 6, com mutex para o histórico compartilhado. Compilação e execução das fases 3 a 7 ainda precisam ser verificadas no Codespaces; o ambiente local usado na implementação não possui compilador C.

- Fase 1: menu principal navegável — concluída.
- Fase 2: cadastro, listagem e consulta de pedidos (RF01-03) — concluída.
- Fase 3: módulo `arquivo.c/h`, opções 9 e 10 e testes de persistência — implementada, aguardando execução dos testes.
- Fase 4: módulo `log.c/h`, opção 7 e testes de histórico — implementada, integrada ao preparo, aguardando execução dos testes.
- Fase 5: `prepararPedido()` em `pedido.c/h`, opção 4, medição e log — implementada, aguardando execução dos testes.
- Fase 6: módulo `processo.c/h`, opção 5 e testes de processo/pipe — implementada, aguardando execução dos testes.
- Fase 7: módulo `thread.c/h`, opção 6, sincronização do histórico e testes de threads — implementada, aguardando execução dos testes.
- A opção 8 continua reservada. A próxima etapa prevista é a medição repetida com mínimo, máximo e média (RF11), mediante autorização.

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
- O tempo é a duração real em segundos, com três casas decimais, medida e fornecida pelo módulo de preparo. Não é apenas o valor previsto em `tempoPreparo`.
- Duração negativa, infinita, NaN e status desconhecido são rejeitados. Falhas de abertura, leitura, escrita e fechamento são informadas.
- O histórico gerado é ignorado pelo Git. O programa deve ser executado na raiz do projeto, com a pasta `dados/` existente.

**As opções 4, 5 e 6 geram registros reais de preparo.** Na opção 5, o PID registrado é o do filho que executou o pedido, não o do pai. Na opção 6, as duas threads pertencem ao mesmo processo, portanto os registros têm o mesmo PID. Cadastro, salvamento e carregamento não criam eventos de execução. Os dados usados nos testes existem somente em pastas temporárias.

O módulo tem como alvo Linux/POSIX (`getpid` e `localtime_r`). Um mutex protege abertura, escrita e fechamento do histórico entre as threads do mesmo processo; a espera de preparo fica fora dessa região. A consulta pelo menu ocorre somente após os joins. Na opção 5, não há threads de preparo ativas: o pai aguarda um único filho e não escreve outro log enquanto ele prepara. O mutex não coordena instâncias independentes do programa; append e mutex não representam transação nem recuperação de uma escrita parcial.

Para verificar o estado atual da interface, execute `make`, abra `./programa` e escolha 7. Sem um histórico existente, o resultado esperado é `Nenhum historico registrado.`

## Preparo sequencial (fase 5)

A opção **4 — Preparar pedido (sequencial)** solicita o ID e procura o pedido cadastrado. Um pedido pendente com tempo de 1 ou 2 segundos é preparado com `sleep()`, passa a `PRONTO` e gera um registro no histórico. O menu aguarda o término: não há processo filho nem thread nesta fase.

- `prepararPedido(Pedido *pedido)` altera o pedido recebido por ponteiro. Retorna `1` se o preparo foi concluído e `0` se não foi executado.
- A duração é medida com `clock_gettime(CLOCK_MONOTONIC)`, apropriado para intervalos de tempo. `clock()` mediria CPU, não a espera de preparo.
- Se um sinal interromper o `sleep()`, a função espera os segundos restantes.
- Pedido inexistente ou já pronto não é preparado; não há novo log para uma tentativa repetida.
- O cadastro interativo agora exige tempo entre 1 e 2 segundos. Arquivos TXT antigos ainda podem ser carregados, mas pedidos com tempo fora dessa faixa não podem ser preparados.
- Falha no relógio inicial impede o preparo. Se a medição final falhar após a espera, o pedido continua pronto, com aviso e sem duração inventada ou log.
- Falha no histórico não desfaz o preparo: o pedido continua pronto, mas o registro não é confirmado. Uma escrita parcial ainda pode existir.
- **O novo status não é salvo automaticamente no TXT.** Use a opção 9 antes de sair para recuperá-lo na próxima sessão.

### Demonstração da fase 5

1. Execute `make` e `./programa` no Codespaces.
2. Cadastre um pedido de 1 segundo na opção 1; consulte na opção 3 para ver `PENDENTE`.
3. Use a opção 4 e informe o ID. Aguarde a mensagem de pedido pronto e a duração medida.
4. Consulte novamente ou liste: o status deve ser `PRONTO`.
5. Use a opção 7 para ver data/hora, PID, pedido, status e duração.
6. Tente preparar o mesmo pedido: o sistema deve informar que já está pronto, sem duplicar o histórico.
7. Salve com 9, saia com 0, abra novamente e carregue com 10. Confira o status pronto.

## Estação de preparo com processo e pipe (fase 6)

A opção **5 — Abrir estação de preparo** solicita o ID de um pedido pendente com tempo de 1–2 segundos. `abrirEstacaoPreparo(Pedido *pedido)` cria um pipe anônimo e um processo filho com `fork()`.

### Fluxo de dados e descritores

1. `pipe(canais)` fornece `canais[0]` (leitura) e `canais[1]` (escrita). Ambos são herdados no `fork()`.
2. O filho fecha a leitura, mostra seu PID e reutiliza `prepararPedido()`, incluindo medição e log. Envia um inteiro com seu status final pela escrita e fecha essa ponta.
3. O pai fecha a escrita e recebe o inteiro pela leitura. Ao terminar, fecha a leitura e aguarda aquele filho com `waitpid()`.
4. O pai confirma `PRONTO` somente após receber a mensagem inteira e verificar que o filho terminou normalmente com código zero.

**Por que o pipe é necessário?** Após `fork()`, pai e filho têm memórias separadas. Alterar a cópia do pedido no filho não altera o vetor do pai; o resultado recebido pelo pipe é usado para atualizar esse vetor. O parâmetro `tempoPreparo` continua o mesmo, pois somente o status é transmitido.

O menu espera a estação terminar; não é execução em segundo plano. Antes do `fork()`, a saída é descarregada para evitar repetição do menu herdado no buffer. O filho descarrega suas mensagens e termina com `_exit()`, sem voltar ao menu.

### Erros e limites

- Verificam-se `pipe`, `fork`, `read`, `write`, `close` e `waitpid`. Leituras/escritas parciais são completadas e interrupções `EINTR` de E/S e espera são retomadas.
- Falha na criação fecha os descritores abertos. Após criar o filho, o pai tenta recolhê-lo mesmo se a comunicação falhar.
- Pedido pronto, inexistente ou com tempo inválido não abre uma estação.
- Falha do histórico no filho não desfaz preparo concluído; o pai ainda pode confirmar `PRONTO` pelo pipe.
- A função retorna `1` para resultado confirmado no pai e `0` para recusa ou resultado não confirmado. Se o filho preparar e a comunicação falhar, seu log pode existir enquanto o pai mantém o status anterior. Não há transação nem recuperação automática nessa situação.
- Se o pai fechar a leitura por falha, a escrita do filho pode terminar por `SIGPIPE`; o pai não confirma um término anormal.
- **Salvar continua manual pela opção 9.** Não há threads nesta fase.

### Demonstração da fase 6

1. Execute `make` e `./programa` no Codespaces.
2. Cadastre um pedido de 1 segundo na opção 1.
3. Use a opção 5 e informe o ID. Observe os PIDs do caixa (pai) e da estação (filho).
4. Aguarde a mensagem de confirmação pelo pipe e consulte o pedido na opção 3: deve estar `PRONTO` no pai.
5. Use a opção 7: o PID do registro deve corresponder ao filho.
6. Salve com 9, saia, abra novamente e carregue com 10 para conferir a persistência do status.

## Preparo com threads (fase 7)

A opção **6 — Preparar pedidos em paralelo** solicita exatamente dois IDs diferentes. Ambos devem existir, estar pendentes e ter tempo de 1–2 segundos. O par é validado antes de iniciar qualquer preparo.

- `prepararPedidosParalelo()` cria duas threads com `pthread_create()` antes de aguardar com `pthread_join()`. Cada uma reutiliza `prepararPedido()` em um elemento diferente do vetor.
- Threads compartilham a memória: os estados são alterados diretamente no vetor, sem pipe. O menu só volta após os joins; mensagens e registros podem aparecer em qualquer ordem.
- O mutex do histórico evita gravações simultâneas no mesmo arquivo dentro deste processo. Ele não envolve o `sleep()`, para não transformar o preparo em sequencial.
- Falha na primeira criação não inicia preparo. Falha na segunda aguarda a primeira e pode deixar somente o primeiro pedido pronto. Um preparo que falha não desfaz o outro.
- Erros pthread são informados pelo código retornado, não por `errno`. Se um join falhar, ainda são tentados os demais, e o programa encerra com erro sem voltar ao menu com threads de término incerto.
- Falha comum de arquivo mantém o pedido pronto e libera o mutex. Falha de lock não tenta gravar; falha excepcional de unlock encerra com erro, para não continuar com uma trava de estado incerto.
- Retorno do módulo: `1` para ambos prontos após os joins; `0` para recusa ou operação incompleta (pode haver preparo parcial); `-1` para término de thread não confirmado.
- **Salvar continua manual pela opção 9.** Esta fase não calcula estatísticas de desempenho.

### Demonstração da fase 7

1. Execute `make` e `./programa` no Codespaces.
2. Cadastre dois pedidos de 1–2 segundos com IDs diferentes.
3. Selecione 6 e informe os dois IDs. Aguarde a conclusão das threads.
4. Consulte os dois pedidos: ambos devem estar `PRONTO`.
5. Consulte 7: os registros devem ter os IDs dos dois pedidos e o mesmo PID, sem ordem obrigatória.
6. Salve com 9, saia, abra novamente e carregue com 10 para conferir os estados.

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

A suíte compila a aplicação e um pequeno programa de teste temporário para testar a gravação de forma independente do preparo. Verifica append, data/hora, PID, formato, validação de parâmetros, consulta inexistente/vazia, opção 7 e erros de E/S. Também verifica que cadastro, salvamento e carregamento não geram logs de execução. Não altera os arquivos reais em `dados/`.

## Testes do preparo

```bash
python3 tests/test_preparo.py
```

A suíte testa preparos reais de 1 e 2 segundos, transição para pronto, histórico, persistência manual, recusa de repetição e entradas inválidas. Um driver C temporário usa wrappers do linker GNU apenas nos testes para simular falhas do relógio/logger e retomada da espera. Nenhum mecanismo de simulação é incluído no programa real. Os testes não alteram os pedidos ou o histórico do projeto.

## Testes de processos e pipe

```bash
python3 tests/test_processos.py
```

A suíte verifica processo real, PIDs distintos, histórico com PID do filho, atualização do pai pelo pipe, persistência manual, ausência de menus duplicados e entradas inválidas. Um driver temporário com wrappers GNU simula falhas de criação, comunicação, espera e término do filho, incluindo transferências parciais e `EINTR`. Nenhum desses mecanismos é incluído no programa real.

## Testes de threads

```bash
python3 -B tests/test_threads.py
```

A suíte verifica dois pedidos reais, registros completos com mesmo PID, persistência manual, recusas, EOF e falha de histórico sem bloquear as threads. Drivers temporários com wrappers GNU testam falhas de criação, preparo, join e mutex. Uma barreira exclusiva do teste verifica sobreposição das threads sem depender de um limite de tempo de execução. Também verifica encerramento do menu após falha de join e preparo por processo depois dos joins. Esses mecanismos não fazem parte do programa entregue.

Para rodar as cinco suítes:

```bash
python3 -m unittest discover -s tests -v
```

A compilação e a execução dos testes dependem de GCC e Linux/POSIX. Se forem pulados por ausência de GCC, a validação continua pendente.
