# Sistema de Pedidos da Lanchonete

Trabalho Prático Integrador — Programação de Software Básico em C.

**Autores: Giovanna Borneo e Felipe Bezerra.**

Aplicação de terminal que adapta o gerenciamento de tarefas ao atendimento de uma lanchonete. Cada pedido possui ID, descrição, tempo de preparo e estado. O preparo é uma **simulação com `sleep()` de 1 ou 2 segundos**, não uma operação real de cozinha ou uma carga intensa de processamento.

O projeto reúne cadastro e consulta, persistência em TXT, processos com `fork()`, comunicação por pipe, duas threads com `pthreads`, histórico e medição de desempenho.

## Estado da validação

As funcionalidades RF01–RF12 estão implementadas. A dupla informou que a execução no Codespaces ocorreu com sucesso. Para a entrega, os resultados dos dez casos de teste devem ser documentados com as evidências reais, junto das medições de desempenho.

O roteiro abaixo apresenta os passos e os resultados esperados; não substitui o registro do que foi observado em cada caso.

## Ambiente e execução

O sistema tem como alvo **Linux/POSIX**, com GCC, GNU make e suporte a `pthreads`. Não é necessário Python para compilar ou executar o programa. O Windows nativo não é o ambiente de execução previsto.

### GitHub Codespaces

1. Abra o repositório no GitHub e selecione a branch desejada.
2. Use **Code > Codespaces** para abrir ou criar o ambiente.
3. Aguarde o carregamento da configuração em [.devcontainer/devcontainer.json](.devcontainer/devcontainer.json), baseada em Ubuntu 24.04 com ferramentas C/C++.
4. No terminal, na raiz do projeto, execute:

```bash
make
./programa
```

O Makefile usa `gcc -Iinclude -Wall -Wextra -pthread` e gera `programa` na raiz. Execute sempre a partir dessa pasta, pois os caminhos de dados são relativos.

Para remover somente o executável:

```bash
make clean
```

A limpeza não apaga os pedidos, o histórico ou a documentação.

## Organização

```text
sistema-pedidos-lanchonete/
├── src/                  # implementações em C
│   ├── main.c
│   ├── pedido.c
│   ├── arquivo.c
│   ├── processo.c
│   ├── thread.c
│   └── log.c
├── include/              # interfaces dos módulos (.h)
├── dados/                # pedidos.txt e historico.txt durante o uso
├── docs/
│   ├── relatorio.pdf
│   └── evidencias/
│       └── fase1.mp4     # vídeo antigo do menu inicial
├── .devcontainer/
├── Makefile
├── README.md
└── .gitignore
```

| Módulo | Responsabilidade |
| --- | --- |
| [main.c](src/main.c) | Menu, leitura de entradas, integração dos módulos e medição da consulta. |
| [pedido.c](src/pedido.c) / [pedido.h](include/pedido.h) | Vetor de pedidos, cadastro, listagem, busca e preparo sequencial. |
| [arquivo.c](src/arquivo.c) / [arquivo.h](include/arquivo.h) | Salvar e carregar pedidos em TXT. |
| [processo.c](src/processo.c) / [processo.h](include/processo.h) | Criar filho, transmitir resultado pelo pipe e aguardar seu término. |
| [thread.c](src/thread.c) / [thread.h](include/thread.h) | Preparar dois pedidos com threads e aguardar os joins. |
| [log.c](src/log.c) / [log.h](include/log.h) | Registrar e consultar o histórico; proteger gravações entre threads. |

A pasta local `data/`, quando presente, contém materiais de apoio e é ignorada pelo Git. Ela não é a pasta `dados/` usada pelo programa.

## Menu e requisitos

| Opção | Operação | Requisitos |
| --- | --- | --- |
| 1 | Cadastrar pedido | RF01 |
| 2 | Listar pedidos e estados | RF02 |
| 3 | Consultar por ID | RF03 |
| 4 | Preparar pedido sequencialmente | RF04, RF10 |
| 5 | Abrir estação de preparo com processo e pipe | RF04, RF07, RF08, RF10 |
| 6 | Preparar dois pedidos em paralelo | RF04, RF09, RF10 |
| 7 | Consultar histórico | RF10 |
| 8 | Medir cinco consultas e apresentar estatísticas | RF11 |
| 9 | Salvar pedidos | RF05 |
| 10 | Carregar pedidos | RF06 |
| 0 | Sair | — |

RF12 é transversal: entradas, arquivos, relógio, processos, threads e comunicação possuem tratamentos de erro nos módulos correspondentes.

O vetor comporta até **50 pedidos**. O ID pode ocupar toda a faixa de `int`, inclusive zero e negativos, mas não pode se repetir. A descrição pode ser vazia, tem limite de **99 bytes** e não aceita `;`, NUL ou CR interno na entrada do menu. Caracteres acentuados podem ocupar mais de um byte em UTF-8. O tempo informado no cadastro deve ser 1 ou 2 segundos.

A entrada é lida por linha e os inteiros são convertidos com `strtol()`. Valores como `1abc`, overflow e linhas longas são recusados. EOF encerra normalmente; erro real de leitura encerra com falha. Pedidos já prontos não são preparados novamente.

## Persistência em TXT

Os pedidos permanecem em memória até a opção **9 — Salvar pedidos**. A opção **10 — Carregar pedidos** recupera o conteúdo de `dados/pedidos.txt`.

Exemplo ilustrativo, não resultado de teste:

```text
1;X-burger e suco;2;0
2;Batata frita;1;1
```

Formato: `ID;descricao;tempoPreparo;status`, um registro por linha. O tempo é em segundos; `0` significa **PENDENTE** e `1`, **PRONTO**.

- TXT foi escolhido por ser legível e não exigir biblioteca externa de serialização.
- Salvar substitui o arquivo anterior; salvar uma lista vazia gera um arquivo vazio.
- Carregar substitui a lista, não acrescenta registros. Arquivo vazio carrega zero pedidos.
- O carregamento valida em um vetor temporário antes de substituir a lista atual. A leitura com `fgetc()` rejeita NUL embutido antes de interpretar a linha; também verifica formato inválido, IDs repetidos e excesso de registros.
- O salvamento **não é automático**, nem ao sair nem ao concluir o preparo. Para preservar o novo estado, use 9.
- Arquivos legados com tempo fora de 1–2 segundos podem ser carregados, mas esses pedidos não podem ser preparados.
- O salvamento não mantém backup nem é transacional: uma falha após abrir para escrita pode deixar um arquivo incompleto.
- Os TXT gerados são ignorados pelo Git; `dados/.gitkeep` mantém a pasta no repositório.

## Processos, threads e histórico

**Opção 5 — Processo e pipe:** o pai cria o pipe antes do `fork()`. O filho prepara sua cópia do pedido, registra o histórico com seu PID e envia o status final. O pai recebe o inteiro completo, aguarda `waitpid()` e só confirma `PRONTO` após término normal bem-sucedido. O pipe é necessário porque pai e filho têm memórias separadas. O menu aguarda a conclusão; não há estação em segundo plano.

**Opção 6 — Threads:** recebe dois IDs distintos, válidos e pendentes. Cria as duas threads antes dos joins. Cada uma altera um pedido diferente no vetor compartilhado; o menu só continua após aguardar ambas. O mutex protege abertura, escrita e fechamento do histórico, sem envolver a espera de preparo. Uma falha de criação pode deixar preparo parcial; falha de join leva ao encerramento com erro, sem retomar o menu com threads de término incerto.

**Histórico:** as opções 4, 5 e 6 acrescentam registros em `dados/historico.txt`, sem apagar os anteriores. Exemplo ilustrativo:

```text
03/11/2026 14:30:00 | PID=5231 | PEDIDO=3 | STATUS=PRONTO | TEMPO=2.001 s
```

Data/hora e PID vêm do sistema. A duração é medida com relógio monotônico. No processo filho, registra-se o PID do filho; nas duas threads, o PID é o mesmo porque pertencem ao mesmo processo. A ordem das mensagens e dos logs das threads não é fixa.

Falhas de medição final ou de histórico não desfazem um preparo já concluído. Se o filho preparar e a comunicação falhar, o pai pode manter o estado anterior mesmo havendo log do filho. Não há recuperação automática dessa divergência. O mutex coordena threads do mesmo processo, não instâncias independentes do programa.

## Medição de desempenho

A opção 8 mede **cinco buscas por ID** com `consultarPedido()` e `clock_gettime(CLOCK_MONOTONIC)`. Exibe os tempos em milissegundos, menor, maior e média, sem preparar pedidos nem alterar os arquivos.

A consulta é curta: resolução e custo do relógio, cache, posição do ID e carga do sistema influenciam os valores. Cinco repetições atendem ao mínimo do enunciado, mas não demonstram estabilidade estatística. Tempos zero são possíveis; seis casas decimais não garantem essa precisão. Não há comparação de desempenho sequencial versus concorrente nem resultados reais coletados nesta versão da documentação.

## Testes

O enunciado exige pelo menos dez casos, mas não exige automação nem Python. Eles podem ser realizados pelo menu. Os testes automatizados usados como apoio local não fazem parte da entrega e sua pasta é ignorada pelo Git.

Compile com `make` e abra com `./programa`. Use este roteiro em uma sessão de teste:

| Caso | Como testar | Resultado esperado |
| --- | --- | --- |
| 1. Cadastro válido | Opção 1: ID 1, Hamburguer, 1 segundo. | Pedido cadastrado como PENDENTE. |
| 2. ID duplicado | Opção 1: tentar cadastrar o ID 1 novamente. | Recusa, sem alterar o pedido original. |
| 3. Consulta válida | Opção 3: consultar ID 1. | Dados do pedido exibidos. |
| 4. Consulta inexistente | Opção 3: consultar ID 999, sem cadastrá-lo. | Mensagem de pedido não encontrado. |
| 5. Salvar | Opção 9. | Confirmação e arquivo `dados/pedidos.txt` gravado. |
| 6. Carregar | Sair com 0, reabrir, usar 10 e consultar ID 1. | Pedido recuperado com os mesmos dados. |
| 7. Criar processo | Opção 5: preparar ID 1 ainda pendente. | Mensagens do pai e do filho com PIDs diferentes. |
| 8. IPC | Após o caso 7, observar a confirmação do pipe e consultar ID 1. | Pai recebe o resultado e exibe PRONTO. |
| 9. Threads | Cadastrar IDs 2 e 3 pendentes; opção 6 com esses IDs. | Dois preparos iniciados antes das conclusões; ambos PRONTO e registrados no histórico (7). |
| 10. Entrada inválida | No menu, digitar `abc`. | Entrada recusada e nova solicitação, sem executar operação. |

Anote o resultado observado de cada caso e guarde capturas em `docs/evidencias/`, incluindo compilação, execução, processos, IPC, threads e testes. A tabela descreve resultados esperados, não resultados já registrados. Salvar no caso 5 substitui o TXT anterior; preserve os dados que quiser manter antes de testar.

### Roteiro curto de demonstração

1. Compile e abra o programa na raiz.
2. Cadastre pedidos com IDs diferentes; tente repetir um ID e consulte um ID inexistente.
3. Prepare um pedido com 4 e outro com 5; confira os PIDs e a confirmação pelo pipe.
4. Prepare dois pedidos ainda pendentes com 6 e consulte os estados e o histórico em 7.
5. Use 8 com um ID existente e confira as cinco medições e estatísticas.
6. Salve com 9, saia, reabra e carregue com 10; consulte os dados recuperados.
7. Verifique também uma entrada inválida e registre os resultados reais.

## Documentação e pendências

- [Relatório técnico em PDF](docs/relatorio.pdf).
- [Vídeo da fase 1](docs/evidencias/fase1.mp4): registro do menu inicial, não evidência do sistema completo.

Antes da entrega final:

- Executar e documentar os dez casos mínimos do professor conforme o roteiro acima.
- Guardar as capturas exigidas e coletar as cinco medições reais da opção 8, com menor, maior e média.
- Completar o relatório com os resultados e evidências; preparar slides e demonstração ao vivo de 10–15 minutos.
