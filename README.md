# Sistema de Pedidos da Lanchonete

Trabalho Prático Integrador — Programação de Software Básico em C.

**Autores: Giovanna Borneo e Felipe Bezerra.**

Aplicação de terminal que adapta o gerenciamento de tarefas ao atendimento de uma lanchonete. Cada pedido possui ID, descrição, tempo de preparo e estado. O preparo é uma **simulação com `sleep()` de 1 ou 2 segundos**, não uma operação real de cozinha ou uma carga intensa de processamento.

O projeto reúne cadastro e consulta, persistência em TXT, processos com `fork()`, comunicação por pipe, duas threads com `pthreads`, histórico e medição de desempenho.

## Estado da validação

As funcionalidades RF01–RF12 estão implementadas por inspeção do código. **A compilação e a execução completa ainda precisam ser validadas no Codespaces/Linux com GCC.**

A verificação local de 04/11/2026 confirmou a sintaxe dos sete arquivos de teste, agora com **101 métodos de teste**, incluindo regressão para NUL no TXT e ID duplicado no cadastro. Como não há GCC nem `make` no ambiente local, inclusive no Ubuntu/WSL verificado, a descoberta das suítes apresentou:

```text
Ran 0 tests
OK (skipped=7)
```

Isso significa **sete classes puladas**, e não 101 testes aprovados. A correção do carregamento com NUL e os dois novos métodos estão preparados, mas a validação C continua pendente. As evidências finais de execução, os slides e os resultados reais de desempenho também continuam pendentes.

## Ambiente e execução

O sistema tem como alvo **Linux/POSIX**, com GCC, GNU make e suporte a `pthreads`. Python 3 é usado apenas nos testes, não pelo programa C. O Windows nativo não é o ambiente de execução previsto.

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
├── tests/                # sete suítes Python
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
- O carregamento valida em um vetor temporário antes de substituir a lista atual. A leitura com `fgetc()` rejeita NUL embutido antes de interpretar a linha; também verifica formato inválido, IDs repetidos e excesso de registros. A correção e os novos testes ainda precisam de execução com GCC.
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

Na raiz, com Linux, GCC e Python 3:

```bash
python3 -B -m unittest discover -s tests -v
```

As suítes compilam em diretórios temporários com `-Wall -Wextra -Werror -pthread`. Os dados de cada cenário também ficam em temporários, sem modificar os TXT reais. Drivers e wrappers GNU simulam falhas somente nos testes; não integram o programa principal.

| Suíte | Métodos | Foco |
| --- | ---: | --- |
| [test_persistencia.py](tests/test_persistencia.py) | 15 | Salvar/carregar, formato, NUL, ID duplicado no cadastro, limites e falhas de arquivo. |
| [test_logs.py](tests/test_logs.py) | 11 | Campos, append, validação e erros de E/S. |
| [test_preparo.py](tests/test_preparo.py) | 12 | Preparo, estado, duração, histórico e falhas simuladas. |
| [test_processos.py](tests/test_processos.py) | 12 | Filho, PIDs, pipe, atualização do pai e falhas de IPC. |
| [test_threads.py](tests/test_threads.py) | 18 | Duas tarefas, sobreposição, mutex e falhas de criação/join. |
| [test_desempenho.py](tests/test_desempenho.py) | 12 | Cinco medições, estatísticas e falhas do relógio. |
| [test_entradas.py](tests/test_entradas.py) | 21 | Entradas inválidas, limites, EOF e erro de leitura. |
| **Total** | **101** | **Preparados; execução C ainda pendente.** |

Para executar uma suíte isolada, por exemplo:

```bash
python3 -B tests/test_persistencia.py
```

A ausência de GCC pula as sete classes. **Não considerar `OK (skipped=7)` como aprovação.**

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

- Compilar e executar as sete suítes no Codespaces; registrar falhas, skips e resultados reais.
- Confirmar em execução os novos testes de **ID duplicado no cadastro** e **NUL embutido no TXT**, incluindo a preservação da lista atual após rejeitar o arquivo.
- Executar e documentar os dez casos mínimos do professor e coletar as medições reais.
- Completar o relatório com os resultados e evidências; preparar slides e demonstração ao vivo de 10–15 minutos.
