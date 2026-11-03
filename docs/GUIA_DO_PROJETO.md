# Guia de estudo — Sistema de Pedidos da Lanchonete

**Autores do projeto: Giovanna Borneo e Felipe Bezerra.**  
**Referência desta revisão: 03/11/2026.**

Este guia explica o trabalho de dentro para fora: proposta, arquitetura, núcleo de dados, arquivos, funções, decisões e fluxos de execução. É material de estudo para entender e defender o código, não um registro de testes aprovados.

> **Importante:** a implementação foi conferida por leitura. Na última execução local das suítes, faltava GCC e as sete classes foram puladas: `Ran 0 tests` e `OK (skipped=7)`. Compilação C, execução completa e medições reais continuam pendentes no Codespaces.
>
> Este arquivo está em `data/`, uma pasta ignorada pelo Git. Portanto, ele permanece local e não será enviado por um `git add` comum. Não confundir `data/`, de materiais de apoio, com `dados/`, usada pelo programa.

## Como usar este guia

1. Comece pelas seções 1 a 4 para entender a ideia e localizar os arquivos.
2. Leia as seções 5 a 11 acompanhando os módulos no editor.
3. Use a seção 12 para comparar os três modos de preparo.
4. Revise as escolhas, limitações e perguntas de defesa no final.

## Sumário

- [1. O que é o trabalho](#1-o-que-é-o-trabalho)
- [2. Arquitetura e desenho geral](#2-arquitetura-e-desenho-geral)
- [3. Organização das pastas e arquivos](#3-organização-das-pastas-e-arquivos)
- [4. O núcleo: Pedido, vetor, contador e estados](#4-o-núcleo-pedido-vetor-contador-e-estados)
- [5. main.c: entrada e coordenação](#5-mainc-entrada-e-coordenação)
- [6. pedido.c: operações centrais](#6-pedidoc-operações-centrais)
- [7. arquivo.c: persistência e escolha de TXT](#7-arquivoc-persistência-e-escolha-de-txt)
- [8. processo.c: filho e comunicação por pipe](#8-processoc-filho-e-comunicação-por-pipe)
- [9. thread.c: dois pedidos concorrentes](#9-threadc-dois-pedidos-concorrentes)
- [10. log.c: histórico e mutex](#10-logc-histórico-e-mutex)
- [11. Medição de desempenho](#11-medição-de-desempenho)
- [12. Comparação dos três modos de preparo](#12-comparação-dos-três-modos-de-preparo)
- [13. Cabeçalhos, bibliotecas e compilação](#13-cabeçalhos-bibliotecas-e-compilação)
- [14. Testes e requisitos do professor](#14-testes-e-requisitos-do-professor)
- [15. Revisão das escolhas e limitações](#15-revisão-das-escolhas-e-limitações)
- [16. Roteiro de leitura e defesa oral](#16-roteiro-de-leitura-e-defesa-oral)

## 1. O que é o trabalho

O professor pediu um sistema de gerenciamento e monitoramento de tarefas em C. Nosso projeto representa essas tarefas como **pedidos de uma lanchonete**.

| Conceito do enunciado | Representação no projeto |
| --- | --- |
| Tarefa | Pedido com ID, descrição, parâmetro e estado. |
| Executar tarefa | Simular o preparo de um pedido. |
| Criar processo | Abrir uma estação de preparo, representada por um filho. |
| Comunicação entre processos | Filho envia o resultado ao caixa, que é o processo pai. |
| Threads | Dois pedidos preparados concorrentemente no mesmo processo. |
| Persistência | Salvar e recuperar a lista de pedidos em TXT. |
| Logs | Histórico das execuções de preparo. |
| Desempenho | Medir cinco consultas e calcular menor, maior e média. |

A lanchonete é o contexto didático. Não há equipamento real, controle de estoque, pagamento ou integração externa. O preparo usa `sleep()` de um ou dois segundos: é uma espera simulada, não uma carga intensa de CPU.

**Uma explicação curta do projeto:**

> “Nosso sistema gerencia pedidos no terminal e usa esse tema para demonstrar conceitos de C e Linux. Podemos preparar um pedido no fluxo normal, em um processo filho ou com duas threads. Também salvamos os pedidos em TXT, registramos o histórico e medimos consultas.”

## 2. Arquitetura e desenho geral

### 2.1 O que significa arquitetura aqui

Arquitetura é a divisão das responsabilidades e a maneira como os módulos trabalham juntos. Neste projeto, ela é **modular e simples**, sem framework, servidor web ou banco de dados.

- A interface lê as escolhas e chama as funções correspondentes.
- O módulo de pedidos contém as operações de cadastro, busca e preparo.
- Processos e threads organizam maneiras diferentes de executar o mesmo preparo.
- Arquivos cuidam de salvar e recuperar a lista.
- Logs cuidam de registrar e consultar as execuções.

Não existe um arquivo chamado “core”. O núcleo é formado principalmente pelo tipo `Pedido`, pelo vetor mantido em `main()` e pelas operações de [pedido.c](../src/pedido.c).

### 2.2 Desenho das responsabilidades

```text
                    USUÁRIO NO TERMINAL
                             |
                             v
                   src/main.c — menu e leitura
                             |
          +------------------+--------------------+
          |                  |                    |
          v                  v                    v
   src/pedido.c      src/processo.c        src/thread.c
   cadastro/busca    processo filho        duas threads
   preparo normal   e pipe                 e joins
          ^                  |                    |
          +------------------+--------------------+
                 reutilizam prepararPedido()
                             |
                             v
                       src/log.c
                    histórico + mutex
                             |
                             v
                    dados/historico.txt

   src/main.c ---> src/arquivo.c <----> dados/pedidos.txt
                   salvar/carregar
```

O desenho mostra responsabilidades e chamadas; não significa que todos esses caminhos executam simultaneamente.

**Ponto importante:** há uma única função de preparo, `prepararPedido()`. Ela é reutilizada nos três modos. Não existem três versões independentes da regra de preparar um pedido.

### 2.3 Fluxo geral de uma sessão

```text
Iniciar o programa
       |
       v
Vetor vazio: total = 0
       |
       v
Mostrar menu e ler opção <---------------------------+
       |                                            |
       v                                            |
Validar entrada                                     |
       |                                            |
       v                                            |
Executar a operação escolhida -----------------------+
       |
       +--> opção 0 ou EOF normal: encerrar
       +--> erro de leitura/falha grave: encerrar com erro
```

A lista não é carregada automaticamente na abertura. Para recuperar o TXT de uma sessão anterior, é necessário escolher a opção 10.

## 3. Organização das pastas e arquivos

### 3.1 Árvore comentada

```text
sistema-pedidos-lanchonete/
├── src/                         implementações em C
│   ├── main.c                   entrada, menu e coordenação
│   ├── pedido.c                 cadastro, listagem, busca e preparo
│   ├── arquivo.c                salvar e carregar TXT
│   ├── processo.c               fork, pipe e waitpid
│   ├── thread.c                 criação e espera das duas threads
│   └── log.c                    histórico e proteção com mutex
├── include/                     interfaces dos módulos
│   ├── pedido.h                 tipo Pedido, constantes e operações
│   ├── arquivo.h                interface da persistência
│   ├── processo.h               interface da estação de preparo
│   ├── thread.h                 interface do preparo concorrente
│   └── log.h                    interface do histórico
├── tests/                       testes Python da aplicação C
│   ├── test_persistencia.py
│   ├── test_logs.py
│   ├── test_preparo.py
│   ├── test_processos.py
│   ├── test_threads.py
│   ├── test_desempenho.py
│   └── test_entradas.py
├── dados/                       arquivos usados durante a execução
│   ├── .gitkeep                 mantém a pasta no repositório
│   ├── pedidos.txt              gerado pela opção 9; ignorado pelo Git
│   └── historico.txt            gerado pelos preparos; ignorado pelo Git
├── docs/                        documentação de entrega
│   ├── relatorio.pdf            relatório técnico
│   └── evidencias/
│       └── fase1.mp4             vídeo antigo do menu inicial
├── data/                        apoio local; pasta ignorada pelo Git
│   ├── Trabalho-Pratico-Integrador.pdf
│   ├── PLANO.md
│   ├── relatorio.html           fonte local do relatório
│   ├── fase1.mp4                cópia local do vídeo inicial
│   └── GUIA_DO_PROJETO.md       este guia
├── .devcontainer/
│   └── devcontainer.json        configuração do Codespaces
├── .git/                        histórico e metadados do Git
├── .gitignore                   define o que não será versionado
├── Makefile                     comandos de compilação e limpeza
└── README.md                    apresentação e instruções de uso
```

Os dois TXT de `dados/` podem não existir antes do primeiro salvamento/preparo. O executável `programa` aparece na raiz depois de compilar e também é ignorado pelo Git. A pasta `.git/` é gerenciada pelo Git, não pelo nosso código.

### 3.2 Onde procurar cada assunto

| Quero entender… | Arquivo para abrir |
| --- | --- |
| Qual é a estrutura de um pedido | [pedido.h](../include/pedido.h). |
| Onde a lista é criada | [main.c](../src/main.c), dentro de `main()`. |
| Como o menu funciona | [main.c](../src/main.c), `exibirMenu()` e `switch`. |
| Como a entrada é validada | [main.c](../src/main.c), `lerLinha()` e `lerInteiro()`. |
| Como o ID repetido é recusado | [pedido.c](../src/pedido.c), `cadastrarPedido()`. |
| Como a busca funciona | [pedido.c](../src/pedido.c), `consultarPedido()`. |
| O que realmente prepara o pedido | [pedido.c](../src/pedido.c), `prepararPedido()`. |
| Por que o TXT tem ponto e vírgula | [arquivo.c](../src/arquivo.c), escrita e `lerPedido()`. |
| Como salvar/carregar funciona | [arquivo.c](../src/arquivo.c). |
| Onde o filho é criado | [processo.c](../src/processo.c), `fork()`. |
| O que atravessa o pipe | [processo.c](../src/processo.c), `statusFinal` e `statusRecebido`. |
| Onde as threads são criadas | [thread.c](../src/thread.c), `pthread_create()`. |
| Onde o programa aguarda as threads | [thread.c](../src/thread.c), `pthread_join()`. |
| Onde está o mutex | [log.c](../src/log.c), `mutexHistorico`. |
| Como as estatísticas são calculadas | [main.c](../src/main.c), `medirDesempenho()`. |
| Como compilar | [Makefile](../Makefile). |
| Como executar e quais são as pendências | [README.md](../README.md). |
| O que o professor pediu | [Enunciado](Trabalho-Pratico-Integrador.pdf). |
| Planejamento histórico das fases | [PLANO.md](PLANO.md); pode conter caminhos anteriores à reorganização. |
| Documento de entrega | [Relatório em PDF](../docs/relatorio.pdf). |

### 3.3 Por que separar `src/` e `include/`

A separação é visual e organizacional:

- `src/`: **como as funções funcionam**, isto é, suas implementações.
- `include/`: **o que os módulos oferecem aos outros**, isto é, tipos, constantes e declarações.

Os nomes dos arquivos não mudaram e não foram criadas camadas artificiais. O programa continua sendo uma aplicação pequena, compilada em um único executável.

## 4. O núcleo: Pedido, vetor, contador e estados

### 4.1 O tipo `Pedido`

Em [pedido.h](../include/pedido.h):

```c
#define MAX_PEDIDOS 50
#define PENDENTE 0
#define PRONTO 1

typedef struct {
    int id;
    char descricao[100];
    int tempoPreparo;
    int status;
} Pedido;
```

| Campo | Significado |
| --- | --- |
| `id` | Identificador usado nas buscas; deve ser único na lista. |
| `descricao` | Texto do pedido, com até 99 bytes mais o terminador NUL. |
| `tempoPreparo` | Tempo simulado de espera, em segundos. |
| `status` | `PENDENTE` ou `PRONTO`. |

A descrição usa bytes, não uma contagem de letras Unicode. Um caractere acentuado pode ocupar mais de um byte em UTF-8.

### 4.2 Onde os pedidos ficam

Dentro de `main()`:

```c
Pedido pedidos[MAX_PEDIDOS];
int total = 0;
```

Exemplo conceitual, não saída de execução:

```text
pedidos[0] -> ID 10, X-burger, 2 s, PENDENTE
pedidos[1] -> ID 25, Batata,   1 s, PRONTO
pedidos[2] -> posição ainda não utilizada
...

total = 2
```

**ID e índice são diferentes.** O ID 25 pode estar na posição 1. A busca percorre o vetor para descobrir a posição; não usa o ID diretamente como índice.

As posições não utilizadas não devem ser lidas como pedidos válidos. O contador limita os percursos ao trecho ocupado do vetor.

### 4.3 Por que vetor fixo

- Atende ao volume pequeno escolhido para o trabalho.
- Facilita cadastrar, percorrer, passar dados por parâmetro e explicar na defesa.
- Dispensa `malloc()`, `realloc()`, nós e liberação de memória dinâmica.
- Permite mostrar claramente vetores de estruturas e ponteiros.

**Limites assumidos:** no máximo 50 registros; busca linear, de custo O(n); não há crescimento automático. Não estamos dizendo que vetor fixo é sempre melhor, apenas que é suficiente para este escopo.

### 4.4 Estado do pedido

```text
Cadastro aceito
      |
      v
  PENDENTE ---- preparo concluído ----> PRONTO
                                         |
                                         +--> nova tentativa é recusada
```

Não existe estado intermediário persistido como “EM PREPARO”. A mensagem “Preparando…” informa a atividade, mas o campo `status` só muda para PRONTO depois da espera. Não há opção de remover pedido ou voltar um pedido pronto para pendente.

### 4.5 Por que usar ponteiros

Exemplo de cadastro:

```c
cadastrarPedido(pedidos, &total, id, descricao, tempo);
```

- `pedidos` permite acessar os elementos do vetor.
- `&total` passa o endereço do contador.
- A função altera `*total`, então o contador de `main()` também muda.

Exemplo de preparo:

```c
prepararPedido(&pedidos[idx]);
```

O endereço indica qual pedido deve ser alterado. Dentro da função, `pedido->status` acessa o campo da estrutura apontada.

Essa alteração alcança o vetor do chamador no mesmo processo, inclusive nas threads. Depois de um `fork()`, o endereço pertence à memória daquele processo: alterar o pedido no filho **não** altera o pedido do pai.

## 5. main.c: entrada e coordenação

Arquivo: [src/main.c](../src/main.c).

O papel principal é coordenar a sessão: mostrar opções, ler dados, validar a entrada, localizar pedidos e chamar os módulos. O processamento de arquivo e os detalhes de concorrência não ficam dentro do `switch`.

### 5.1 Funções do arquivo

| Função | O que faz |
| --- | --- |
| `exibirMenu()` | Imprime as opções de 0 a 10. |
| `lerLinha()` | Lê a linha inteira e informa linha válida, inválida ou EOF sem dados. |
| `lerInteiro()` | Usa a linha lida e `strtol()` para obter um `int` completo e válido. |
| `medirDesempenho()` | Mede cinco consultas e apresenta estatísticas. |
| `main()` | Mantém vetor/contador, repete o menu e encaminha cada escolha. |

As funções marcadas como `static` são auxiliares locais ao arquivo. Não precisam ficar disponíveis para os outros módulos.

### 5.2 Caminho das opções

| Opção | Caminho principal |
| --- | --- |
| 1 | Ler ID, descrição e tempo → `cadastrarPedido()`. |
| 2 | `listarPedidos()`. |
| 3 | Ler ID → `consultarPedido()` → exibir os campos do índice encontrado. |
| 4 | Ler ID → buscar → `prepararPedido()`. |
| 5 | Ler ID → buscar → `abrirEstacaoPreparo()`. |
| 6 | Ler dois IDs → buscar os dois → `prepararPedidosParalelo()`. |
| 7 | `exibirHistorico()`. |
| 8 | Ler ID → `medirDesempenho()`. |
| 9 | `salvarPedidos()`. |
| 10 | `carregarPedidos()`. |
| 0 | Encerrar a sessão. |

### 5.3 Por que ler a linha inteira

Se fosse aproveitado somente o começo de `1abc`, a entrada poderia virar indevidamente o número 1. A leitura por linha permite verificar a resposta inteira e rejeitar conteúdo sobrando.

A combinação atual:

1. Consome a linha, inclusive se for longa demais.
2. Evita que o restante vire uma resposta para o próximo campo.
3. Usa `strtol()` e verifica overflow, faixa de `int` e texto restante.
4. Aceita espaços antes/depois e sinal quando o valor é válido.

O ID aceita toda a faixa de `int`, inclusive negativos e zero. Isso é permitido pelo código atual; não se deve afirmar que o programa exige IDs positivos.

EOF normal, por exemplo Ctrl+D no Linux, encerra sem laço infinito. Um erro real de leitura é tratado como falha, não como EOF normal. Uma operação com campos incompletos não começa.

**Atenção à divisão das validações:** o cadastro interativo valida descrição e tempo em `main.c`; `cadastrarPedido()` cuida principalmente de capacidade, duplicidade e inserção. A função de cadastro não revalida sozinha todas as regras da interface.

## 6. pedido.c: operações centrais

Arquivo: [src/pedido.c](../src/pedido.c). Interface: [include/pedido.h](../include/pedido.h).

### 6.1 `cadastrarPedido()`

1. Verifica se o vetor já atingiu a capacidade.
2. Percorre os pedidos existentes para recusar ID repetido.
3. Copia ID, descrição e tempo para a posição `pedidos[*total]`.
4. Inicia o estado como PENDENTE.
5. Incrementa o contador por ponteiro.

Retornos: `1` = cadastrado; `0` = ID duplicado; `-1` = vetor cheio.

A descrição é copiada com limite e o terminador é garantido. A interface rejeita texto acima do limite antes de chamar a função, evitando que um cadastro normal seja silenciosamente encurtado.

### 6.2 `listarPedidos()`

Mostra ID, descrição e estado de cada posição ocupada. Se `total` é zero, informa que não há pedidos. A listagem não exibe o tempo, mas a consulta individual o exibe.

### 6.3 `consultarPedido()`

Percorre as posições de zero até `total - 1`, comparando IDs. Retorna o índice encontrado ou `-1`.

Não imprime o pedido e não altera os dados. Isso permite reutilizá-la no menu, antes dos preparos e no experimento de desempenho.

### 6.4 `prepararPedido()`

É a operação central de execução:

```text
Validar pedido, estado e tempo
              |
              v
Ler relógio monotônico inicial
              |
              v
Mostrar mensagem e esperar com sleep()
              |
              v
Alterar status para PRONTO
              |
              v
Ler relógio final e calcular duração
              |
              v
Tentar registrar o histórico
```

O `sleep()` é retomado se houver tempo restante depois de uma interrupção. O relógio monotônico mede tempo decorrido, incluindo a espera. `clock()` mediria CPU, que não é o objetivo dessa simulação.

**O tempo previsto não é a duração medida:** `tempoPreparo = 2` solicita dois segundos de espera; o log contém o intervalo observado, que pode ser um pouco maior.

Retornos: `1` = preparo concluído, inclusive quando houve falha posterior de medição/log; `0` = preparo não executado.

Se o relógio inicial falha, não inicia. Se o relógio final falha, o pedido já ficou pronto e permanece assim, com aviso e sem duração inventada. Se o histórico falha, também não desfaz o preparo.

**Justificativa da reutilização:** processo e threads precisam demonstrar modos diferentes de execução, não regras de preparo diferentes. Compartilhar essa função evita duplicar validação, espera, medição e log.

## 7. arquivo.c: persistência e escolha de TXT

Arquivo: [src/arquivo.c](../src/arquivo.c). Interface: [include/arquivo.h](../include/arquivo.h).

### 7.1 O que persistência significa

A RAM mantém os pedidos enquanto a sessão existe. Depois de encerrar, esse vetor deixa de existir. Persistir é gravar os dados para que uma sessão futura possa reconstruir a lista.

```text
SESSÃO ATUAL                             SESSÃO FUTURA
Vetor em memória                         Novo vetor, inicialmente vazio
       |                                            ^
       | opção 9: salvar                            | opção 10: carregar
       v                                            |
       +---------- dados/pedidos.txt ----------------+
```

O programa não salva nem carrega automaticamente.

### 7.2 Por que TXT, e não JSON ou binário

A página 12 do enunciado permite escolher texto ou binário e justificar. O formato `.dat` mostrado no exemplo não obriga usar binário; também não há obrigação de JSON.

**Por que TXT foi adequado aqui:**

- Podemos abrir o arquivo no editor e enxergar os dados na apresentação.
- O registro possui apenas quatro campos simples.
- Usamos a biblioteca padrão de C, sem biblioteca JSON.
- Escrita e leitura ficam pequenas o suficiente para explicar.
- Não gravamos a representação bruta de uma struct, que poderia envolver padding e detalhes de representação da plataforma.

**Por que não JSON nesta versão:** é uma opção válida e mais estruturada, mas exigiria uma biblioteca ou um parser mais elaborado. Não acrescenta uma necessidade essencial para estes quatro campos.

**Por que não binário nesta versão:** também seria válido, mas dificultaria a leitura humana na demonstração. Escrever a struct bruta ainda exigiria cuidado com compatibilidade quando sua estrutura ou plataforma mudasse.

**Limites do TXT escolhido:** precisamos definir separadores e validar os campos; não temos escape de `;` na descrição, versionamento do formato, transações ou recuperação automática.

**Resposta curta para a defesa:**

> “Escolhemos TXT porque o enunciado permite e nossos registros são pequenos. Ele é legível, facilita demonstrar a persistência e pode ser tratado com a biblioteca padrão de C. Em troca, proibimos o separador na descrição e precisamos validar o conteúdo ao carregar.”

### 7.3 Formato

Exemplo ilustrativo:

```text
10;X-burger e suco;2;0
25;Batata frita;1;1
```

Ordem: `ID;descricao;tempoPreparo;status`.

- Uma linha por pedido, sem cabeçalho.
- `;` separa os campos, então não é permitido na descrição.
- `0` significa PENDENTE; `1`, PRONTO.
- A descrição vazia é aceita, como em `10;;2;0`.

### 7.4 `salvarPedidos()`

Abre `dados/pedidos.txt` em modo `"w"`, que cria o arquivo ou substitui seu conteúdo. Escreve as posições ocupadas com `fprintf()` e verifica `fclose()`.

Verificar o fechamento importa porque uma escrita pode ficar no buffer e só falhar ao descarregá-lo. Lista vazia gera arquivo vazio.

O salvamento não é transacional: se falhar depois de abrir o arquivo para escrita, o conteúdo anterior pode já ter sido perdido ou o novo arquivo pode ficar parcial. Não há backup.

### 7.5 `carregarPedidos()`

```text
Abrir TXT
   |
   v
Ler e validar em vetor temporário
   |
   +--> falha detectada: não substituir a lista atual
   |
   +--> leitura/validação/fechamento bem-sucedidos:
        copiar temporários para o vetor principal
        atualizar total
```

As auxiliares locais `lerInteiro()` e `lerPedido()` convertem os campos e validam o formato. A `lerInteiro()` deste módulo é diferente da função com o mesmo nome em `main.c`: esta interpreta um campo de TXT; a de `main.c` obtém uma linha da entrada do usuário. Como ambas são `static`, não conflitam entre arquivos.

A separação dos campos é manual e preserva descrição vazia. O carregamento reutiliza `cadastrarPedido()` para controlar capacidade e duplicidade. Como essa função inicia PENDENTE, o carregador restaura depois o estado lido do arquivo.

Arquivo válido substitui a lista inteira; não mescla os registros. Arquivo vazio resulta em `total = 0`. Tempos legados fora de um ou dois segundos são preservados ao carregar, mas o preparo os recusa.

**Limitação conhecida:** NUL embutido pode fazer as funções de string enxergarem só o prefixo da linha. Portanto, ainda não é correto prometer rejeição de todo arquivo corrompido. Esse caso e seu teste de regressão estão pendentes.

## 8. processo.c: filho e comunicação por pipe

Arquivo: [src/processo.c](../src/processo.c). Interface: [include/processo.h](../include/processo.h).

### 8.1 O que `fork()` faz

Cria um processo filho. A execução prossegue em dois processos, e o retorno permite distingui-los:

- Menor que zero: falha na criação.
- Zero: estamos no filho.
- Maior que zero: estamos no pai; o valor é o PID do filho.

O filho começa com uma cópia do estado do pai. Os vetores passam a pertencer a espaços de memória separados. Não devemos confundir o valor de um endereço com memória compartilhada entre processos.

### 8.2 Por que o pipe é necessário

Imagine um pedido pendente antes do `fork()`:

```text
ANTES DO FORK
Pai: pedido 10 = PENDENTE

DEPOIS DO FORK
Pai:   sua cópia do pedido 10 = PENDENTE
Filho: sua cópia do pedido 10 = PENDENTE

DEPOIS DO PREPARO NO FILHO
Pai:   sua cópia do pedido 10 = PENDENTE
Filho: sua cópia do pedido 10 = PRONTO

DEPOIS DA CONFIRMAÇÃO PELO PIPE
Pai: recebe PRONTO e atualiza sua cópia
```

O pipe não compartilha o vetor: transporta bytes com o resultado. Neste código, a comunicação de dados pelo pipe tem direção **filho → pai**. O pai não envia um pedido pelo pipe; o filho já recebeu sua cópia por herança do `fork()`.

### 8.3 Descritores e desenho do fluxo

`pipe(canais)` fornece dois descritores, que são identificadores de recursos abertos:

- `canais[0]`: leitura.
- `canais[1]`: escrita.

```text
Pai cria o pipe e chama fork()
                  |
       +----------+-----------+
       |                      |
       v                      v
PAI / CAIXA              FILHO / ESTAÇÃO
fecha canais[1]          fecha canais[0]
       |                      |
       |                 preparaPedido()
       |                 grava log com PID do filho
       |                      |
       | <--- int PRONTO -----| write(canais[1], ...)
read(canais[0], ...)           |
fecha canais[0]          fecha canais[1]
       |                 fflush() e _exit()
       v
waitpid(): verifica término
       |
       v
Atualiza pedido no pai
Retorna ao menu
```

As pontas não usadas são fechadas para liberar recursos e permitir observar EOF corretamente quando todos os escritores fecham a escrita. `read()` pode bloquear enquanto aguarda o resultado.

### 8.4 O que é enviado

Um `int` com o estado final. O pai já sabe qual pedido solicitou, e o filho não muda seu ID nem tempo; por isso não é necessário enviar a struct inteira.

Como são pai e filho do mesmo programa, usam a mesma representação de inteiro. Isso não deve ser vendido como um protocolo de rede portável entre máquinas diferentes.

O código trata leitura/escrita parcial e `EINTR`: uma chamada de E/S não é presumida suficiente em todos os casos. O acesso por `char *` permite avançar pelo inteiro em bytes até completar a mensagem.

### 8.5 Espera, buffers e encerramento

- `waitpid(filho, ...)` aguarda especificamente esse filho e permite conferir seu término, evitando deixar um processo zumbi após encerramento normal não recolhido.
- O pai só confirma PRONTO com mensagem completa, estado esperado e filho encerrado normalmente com código zero.
- `fflush(stdout)` antes de `fork()` evita duplicar mensagens que estavam no buffer herdado.
- O filho descarrega suas mensagens e usa `_exit()` para não voltar ao menu nem executar rotinas de saída da biblioteca herdadas desnecessariamente.
- A auxiliar `fecharDescritor()` centraliza o diagnóstico de erro ao fechar pontas do pipe.

### 8.6 Limite do fluxo

O pai espera; não há atendimento simultâneo de novos comandos enquanto a estação trabalha. Só existe uma estação por chamada da opção 5.

Se o filho preparar e registrar o log, mas a confirmação falhar, o pai pode continuar com PENDENTE. Não existe uma transação que una preparo, log, mensagem e salvamento. O retorno `0` significa resultado recusado/não confirmado, não prova que o filho não fez trabalho algum.

## 9. thread.c: dois pedidos concorrentes

Arquivo: [src/thread.c](../src/thread.c). Interface: [include/thread.h](../include/thread.h).

### 9.1 O que é uma thread

É um fluxo de execução dentro de um processo. Cada thread possui sua execução e pilha, mas compartilha a memória do processo com as outras threads.

No nosso caso, `main()` mantém o vetor e passa o endereço de um pedido diferente para cada thread. Não há cópia separada do vetor como no filho criado por `fork()`.

### 9.2 Funções do módulo

- `prepararPedidosParalelo()`: valida o par, cria as duas threads, aguarda e confere o resultado.
- `prepararNaThread()`: função auxiliar com a assinatura esperada por pthreads; recebe um `void *`, chama `prepararPedido()` e retorna `NULL`.

`void *` é um ponteiro genérico, usado pela API para permitir argumentos de diferentes tipos. Neste uso, ele representa o endereço de um `Pedido`.

O worker não devolve o estado por seu valor de retorno. Depois dos joins bem-sucedidos, o módulo observa o `status` dos pedidos compartilhados.

### 9.3 Passo a passo

1. O menu lê dois IDs e busca seus índices.
2. O módulo recusa ponteiros nulos, mesmo pedido, IDs iguais, estados inválidos ou tempos fora da faixa.
3. Cria a thread A passando o endereço do primeiro pedido.
4. Cria a thread B passando o endereço do segundo pedido.
5. Aguarda as threads criadas com `pthread_join()`.
6. Confere se as duas foram criadas e se ambos os pedidos estão PRONTO.
7. Só depois devolve o controle ao menu.

```text
                   UM PROCESSO / MESMO VETOR

main() chama prepararPedidosParalelo()
                 |
                 +--> pthread_create(A) --> pedido na posição X
                 |
                 +--> pthread_create(B) --> pedido na posição Y
                 |                          X e Y são diferentes
                 v
             join(A) e join(B)
                 |
                 v
       Consultar estados no mesmo vetor
                 |
                 v
              Voltar ao menu
```

### 9.4 Por que criar ambas antes dos joins

O fluxo atual é:

```text
criar A -> criar B -> aguardar A -> aguardar B
```

Mesmo enquanto a thread principal aguarda A, B já foi criada e pode trabalhar. Aguardar A primeiro não impede B de executar.

Se fosse assim:

```text
criar A -> aguardar A -> criar B -> aguardar B
```

B só começaria depois do término de A, tornando os preparos sequenciais.

A concorrência permite sobreposição. Não garante que duas instruções executem no mesmo instante em todo ambiente: isso depende do escalonador e do hardware. Nosso código não contém resultado medido que comprove aceleração.

### 9.5 Por que não há mutex no vetor

No fluxo atual:

- Cada thread modifica um elemento diferente.
- O contador e a estrutura do vetor não mudam durante o preparo.
- O menu aguarda os joins antes de listar, consultar, salvar ou carregar.
- O vetor de `main()` continua existindo enquanto as threads o utilizam.

Essas condições evitam acesso concorrente conflitante aos mesmos campos. Não significa que vetores nunca precisam de mutex. Se fossem permitidos dois preparos do mesmo pedido, cadastro simultâneo ou leitura enquanto uma thread escreve, seria necessário reavaliar a sincronização.

### 9.6 PIDs, mensagens e falhas

As duas threads têm o mesmo PID do processo nos logs, embora tenham identidades de thread próprias. O projeto registra PID; não registra TID. A ordem das mensagens e dos registros pode variar.

O código verifica o retorno de `pthread_create()` e `pthread_join()`. Essas funções devolvem códigos de erro próprios, apresentados com `strerror(erro)`, e não devem ser diagnosticadas presumindo que atualizaram `errno`.

| Situação | Comportamento |
| --- | --- |
| Primeira criação falha | Nenhum preparo iniciado por essas threads. |
| Segunda criação falha | Aguarda a primeira; pode haver um pedido pronto. |
| Um preparo falha | Não desfaz o preparo concluído pelo outro. |
| Um join falha | Tenta aguardar os demais e indica término não confirmado. |
| Ambos terminam prontos | Retorna sucesso para o menu. |

Retornos: `1` = ambos prontos; `0` = recusa ou resultado incompleto; `-1` = falha de espera. Se recebe `-1`, o menu encerra com erro para não continuar acessando dados de threads cujo término não foi confirmado.

## 10. log.c: histórico e mutex

Arquivo: [src/log.c](../src/log.c). Interface: [include/log.h](../include/log.h).

### 10.1 Pedidos salvos e logs não são a mesma coisa

| Arquivo | Pergunta que responde |
| --- | --- |
| `dados/pedidos.txt` | “Qual é a lista e o estado que foram salvos?” |
| `dados/historico.txt` | “Quais execuções de preparo foram registradas?” |

Preparar um pedido pode acrescentar um log sem atualizar o TXT da lista, pois o salvamento continua manual. O histórico também pode guardar registros antigos depois de a lista ser substituída por um carregamento.

Não usamos o histórico para reconstruir automaticamente a lista.

### 10.2 `registrarLog()`

Recebe ID, estado e duração do preparo. Verifica se o estado é conhecido e se a duração é finita e não negativa. Não exige uma duração estritamente positiva.

Obtém data/hora com `time()`, `localtime_r()` e `strftime()`, e PID com `getpid()`. `localtime_r()` utiliza uma estrutura fornecida por cada chamada, em vez de depender de uma única área de resultado estática compartilhada.

Abre o histórico em `"a"`, modo append, para acrescentar sem apagar as entradas anteriores. Exemplo ilustrativo:

```text
03/11/2026 14:30:00 | PID=5231 | PEDIDO=10 | STATUS=PRONTO | TEMPO=2.001 s
```

- Modo sequencial: PID do processo principal.
- Modo processo: PID do filho que preparou.
- Modo threads: mesmo PID para as duas threads.

Cadastro, busca, salvar e carregar não registram preparo. Uma tentativa recusada de preparar novamente um pedido pronto também não gera novo log de sucesso.

### 10.3 Por que o mutex está aqui

As threads trabalham em pedidos diferentes, mas ambas gravam no **mesmo histórico**. Essa é a região compartilhada que o projeto protege.

O mutex é declarado como variável estática do módulo e inicializado com `PTHREAD_MUTEX_INITIALIZER`. `static` aqui mantém a variável acessível apenas dentro desse arquivo, mas suas chamadas no mesmo processo usam a mesma trava.

```text
Thread A: prepara seu pedido ──┐
                              ├── região protegida, uma por vez:
Thread B: prepara seu pedido ──┘     lock
                                    abrir histórico
                                    escrever registro
                                    fechar/descarregar
                                    unlock
```

O mutex engloba **abrir, escrever e fechar**. Assim, uma thread não libera a região antes de descarregar sua gravação pelo fechamento.

Ele não engloba o `sleep()`: bloquear durante toda a espera impediria a sobreposição dos preparos. Também não protege todas as mensagens do terminal, então sua ordem continua não determinada.

**Append não substitui a justificativa de sincronização:** é uma escolha de modo de abertura, não uma transação completa nem garantia geral de coordenação para toda a sequência de E/S.

### 10.4 Limites e falhas

- Falha de arquivo não desfaz o pedido pronto; há aviso.
- Falha comum na gravação ainda passa pela tentativa de liberar o mutex.
- Falha de lock impede a tentativa de escrita por essa chamada.
- Falha excepcional de unlock encerra o programa para não continuar com a trava em estado incerto.
- O mutex não é configurado para compartilhamento entre processos e não coordena instâncias independentes.

O `fork()` da opção 5 ocorre sem threads de preparo ativas: o menu só retorna da opção 6 depois dos joins confirmados. Não estamos implementando um cenário geral de vários filhos e várias threads gravando ao mesmo tempo.

### 10.5 `exibirHistorico()`

Abre em `"r"` e mostra as linhas. Ausência ou arquivo vazio informam que não há histórico; a consulta não cria arquivo novo.

Não usa o mutex de gravação porque, no fluxo atual, o menu não consulta enquanto as threads de preparo estão ativas. Se isso mudar, a justificativa também precisa mudar.

## 11. Medição de desempenho

Local: `medirDesempenho()` em [main.c](../src/main.c), chamada pela opção 8.

### 11.1 O que medimos

**Cinco consultas do mesmo ID**, não cinco preparos, nem o tempo de criar threads ou processos.

1. Busca preliminar confirma que o ID existe; fica fora das medições.
2. Para cada repetição: relógio inicial → `consultarPedido()` → relógio final.
3. Confere se a busca retornou o índice esperado.
4. Guarda o intervalo em milissegundos.
5. Só após completar todas as medições imprime os cinco valores, menor, maior e média.

Entrada, impressão e cálculo de estatísticas ficam fora dos intervalos. A opção não altera os pedidos, não salva e não gera logs de preparo.

### 11.2 Cálculo

```c
tempo_ms = (fim.tv_sec - inicio.tv_sec) * 1000.0
         + (fim.tv_nsec - inicio.tv_nsec) / 1000000.0;
```

O relógio fornece segundos e nanossegundos. Ambos entram na diferença, inclusive quando a medição atravessa a mudança de um segundo para outro.

- Menor: mínimo dos cinco tempos.
- Maior: máximo dos cinco tempos.
- Média: soma dividida por cinco.

Falha de relógio, intervalo negativo ou busca com resultado inesperado cancelam o experimento sem resumo parcial. Intervalo zero é aceito.

### 11.3 Justificativa e limites

Consulta é uma operação relevante do sistema e aparece no requisito RF03. O RF11 pede uma operação relevante repetida ao menos cinco vezes, com estatísticas e análise da amostra.

A busca em até 50 elementos é muito curta. Resolução/custo do relógio, cache, posição do pedido e carga do sistema podem influenciar mais que o trabalho medido. Seis casas decimais na saída não garantem essa precisão real.

Cinco repetições atendem ao mínimo, mas não comprovam estabilidade estatística. Não há comparação sequencial versus concorrente. **Ainda faltam os tempos reais coletados em execução.**

## 12. Comparação dos três modos de preparo

| Aspecto | Opção 4: sequencial | Opção 5: processo | Opção 6: threads |
| --- | --- | --- | --- |
| Quantos pedidos por chamada | Um. | Um. | Dois distintos. |
| Onde prepara | Fluxo principal. | Processo filho. | Duas threads criadas. |
| Função reutilizada | `prepararPedido()`. | `prepararPedido()`. | `prepararPedido()`. |
| Memória do pedido | Vetor do processo principal. | Cópia no filho. | Vetor compartilhado do processo. |
| Como o pai/menu obtém o estado | Alteração direta por ponteiro. | Recebe pelo pipe e aplica. | Observa o vetor após os joins. |
| Como aguarda | A própria chamada bloqueia até retornar. | Recepção e `waitpid()`. | `pthread_join()`. |
| PID no histórico | Principal. | Filho. | Mesmo PID do processo para ambas. |
| Menu continua durante o preparo | Não. | Não. | Não. |
| Salva TXT automaticamente | Não. | Não. | Não. |

**Não confundir:** concorrência interna do preparo com interface em segundo plano. A opção 6 permite os dois preparos se sobreporem, mas a thread principal aguarda antes de mostrar o próximo menu.

## 13. Cabeçalhos, bibliotecas e compilação

### 13.1 Conteúdo de cada cabeçalho

| Cabeçalho | Conteúdo |
| --- | --- |
| [pedido.h](../include/pedido.h) | `MAX_PEDIDOS`, `PENDENTE`, `PRONTO`, tipo `Pedido` e declarações de cadastro, listagem, consulta e preparo. |
| [arquivo.h](../include/arquivo.h) | Declara `salvarPedidos()` e `carregarPedidos()`; inclui o tipo de pedido. |
| [processo.h](../include/processo.h) | Declara `abrirEstacaoPreparo()` e explica confirmação/possível falha parcial. |
| [thread.h](../include/thread.h) | Declara `prepararPedidosParalelo()` e os retornos, incluindo falha de join. |
| [log.h](../include/log.h) | Declara `registrarLog()` e `exibirHistorico()` e resume seus contratos. |

Os blocos `#ifndef`, `#define` e `#endif` são proteções para evitar processar repetidamente as declarações do mesmo cabeçalho dentro de uma unidade de compilação.

`#include "pedido.h"` disponibiliza declarações e tipos ao compilador; não executa o módulo nem equivale a chamar uma função. A implementação correspondente vem do `.c`, compilado e ligado ao executável.

**Os retornos não têm um significado global único:** `-1` é vetor cheio no cadastro, não encontrado na consulta e falha de join no módulo de threads. É preciso conhecer o contrato de cada função.

### 13.2 Bibliotecas e APIs mais importantes

| Recurso | Uso no projeto |
| --- | --- |
| `stdio.h` | Terminal e arquivos: `printf`, `getchar`, `fopen`, `fprintf`, `fgets`, `fclose`, `perror`. |
| `stdlib.h` | Conversão com `strtol` e encerramento com `exit`. |
| `string.h` | Operações de string, cópia, busca de separador e `strerror`. |
| `time.h` | Relógio monotônico e data/hora do histórico. |
| `unistd.h` | `sleep`, `fork`, `pipe`, `read`, `write`, `close`, `getpid` e `_exit`. |
| `sys/wait.h` | `waitpid` e macros para interpretar o término do filho. |
| `pthread.h` | Threads, joins e mutex. |
| `errno.h`, `limits.h`, `ctype.h` | Diagnósticos, limites e validação de conversões/entrada. |
| `math.h` | Verificação de duração finita no log com `isfinite`. |

`_POSIX_C_SOURCE 200809L`, definido antes dos includes nos módulos que o usam, solicita a exposição de interfaces POSIX apropriadas pela biblioteca. Não cria essas funções e não transforma o Windows nativo em Linux.

### 13.3 O Makefile

Arquivo: [Makefile](../Makefile).

- `CC = gcc`: compilador escolhido.
- `CPPFLAGS = -Iinclude`: diretório de busca dos nossos cabeçalhos.
- `CFLAGS = -Wall -Wextra -pthread`: avisos e suporte a threads na compilação/ligação.
- `FONTES`: seis implementações C.
- `CABECALHOS`: cinco interfaces; mudanças nelas também fazem o alvo precisar recompilar.
- `programa`: executável gerado na raiz.
- `clean`: remove somente `programa`.
- `.PHONY: clean`: informa que `clean` é uma ação, não um arquivo de saída.

Não usamos arquivos `.o` intermediários no Makefile atual. Compilar tudo em uma regra é suficiente para este tamanho e mantém o build simples. Os testes acrescentam `-Werror`, mas o Makefile principal não o usa.

Comandos, no terminal Linux/Codespaces, a partir da raiz:

```bash
make
./programa
```

Limpeza:

```bash
make clean
```

**Por que executar na raiz:** o código abre caminhos relativos como `dados/pedidos.txt`. São relativos ao diretório de execução, não à pasta onde `arquivo.c` está. Mover os fontes para `src/` não mudou os caminhos dos dados.

### 13.4 Arquivos de suporte

- [devcontainer.json](../.devcontainer/devcontainer.json): seleciona imagem C/C++ com Ubuntu 24.04 e extensão C/C++ do VS Code para o Codespaces. Não contém a lógica dos pedidos.
- [.gitignore](../.gitignore): ignora executável, objetos, TXT gerados, antigos `.dat` de dados e toda a pasta `data/`.
- [dados/.gitkeep](../dados/.gitkeep): arquivo vazio convencional para manter a pasta no Git; não é dado de pedido nem lido pelo programa.
- [README.md](../README.md): manual de entrada para compilar, usar e localizar a documentação.
- [relatorio.pdf](../docs/relatorio.pdf): texto técnico destinado à avaliação; não substitui o código nem os testes.
- [fase1.mp4](../docs/evidencias/fase1.mp4): evidência antiga do menu inicial, não demonstração final de processos/threads/IPC.
- [relatorio.html](relatorio.html): fonte editável local atualmente guardada em `data/`; não acompanha o repositório.

## 14. Testes e requisitos do professor

### 14.1 Por que os testes são Python se a aplicação é C

Python automatiza a compilação e a interação com o executável: envia entradas, captura saídas e confere arquivos/resultados. A aplicação entregue continua sendo C; não depende de Python para executar seu menu.

As suítes usam pastas temporárias para compilar e para executar cada cenário com uma pasta `dados/` própria. Isso evita modificar pedidos e histórico reais durante os testes.

Algumas suítes geram pequenos drivers C e usam wrappers do linker GNU para simular falhas. São instrumentos de teste, não caminhos ocultos do programa principal. O teste com relógio controlado, por exemplo, serve para conferir a conta, não para produzir uma medição real.

### 14.2 O que há em cada suíte

| Arquivo | Métodos | Assunto |
| --- | ---: | --- |
| [test_persistencia.py](../tests/test_persistencia.py) | 13 | Salvar, reabrir, carregar, preservar estados, formato inválido, capacidade, duplicidade no TXT e erros de arquivo. |
| [test_logs.py](../tests/test_logs.py) | 11 | Formato, append, data/hora, PID, parâmetros e falhas de E/S do histórico. |
| [test_preparo.py](../tests/test_preparo.py) | 12 | Espera simulada, estado pronto, log, recusa de repetição e falhas de relógio/logger. |
| [test_processos.py](../tests/test_processos.py) | 12 | Filho real quando executado, PIDs, pipe, estado no pai, transferências parciais e falhas. |
| [test_threads.py](../tests/test_threads.py) | 18 | Dois pedidos, logs, sobreposição por barreira de teste, criação parcial, join e mutex. |
| [test_desempenho.py](../tests/test_desempenho.py) | 12 | Cinco medições, estatísticas, casos de relógio e preservação dos dados. |
| [test_entradas.py](../tests/test_entradas.py) | 21 | EOF, números parciais, overflow, linhas longas, descrições e erros de leitura. |
| **Total** | **99** | **Métodos preparados; não aprovados em execução nesta revisão.** |

Rodar todas, na raiz e em Linux com GCC:

```bash
python3 -B -m unittest discover -s tests -v
```

O `-B` evita gerar caches Python. A descoberta encontra as suítes; se não houver GCC, os testes não compilam nem executam o programa C e as classes são puladas.

### 14.3 Onde cada requisito é atendido por implementação

| Requisito | Localização principal |
| --- | --- |
| RF01 — Cadastrar | `main.c` + `pedido.c`. |
| RF02 — Listar | `pedido.c`. |
| RF03 — Consultar | `pedido.c`, com exibição em `main.c`. |
| RF04 — Executar | `prepararPedido()` em `pedido.c`. |
| RF05 — Salvar | `salvarPedidos()` em `arquivo.c`. |
| RF06 — Carregar | `carregarPedidos()` em `arquivo.c`, com limitação NUL pendente. |
| RF07 — Criar processo | `processo.c`, `fork()` e `waitpid()`. |
| RF08 — IPC | `processo.c`, pipe filho → pai. |
| RF09 — Threads | `thread.c`, duas criações e joins. |
| RF10 — Logs | `log.c`, chamado pelo preparo. |
| RF11 — Medição | `medirDesempenho()` em `main.c`. |
| RF12 — Erros | Validações e retornos nos módulos; comprovação dinâmica ainda pendente. |

### 14.4 O que falta comprovar

Os dez cenários mínimos são: cadastro válido; ID duplicado no cadastro; consulta válida; consulta inexistente; salvar; carregar; criar filho; receber mensagem por IPC; executar duas tarefas com threads; entrada inválida.

Há testes preparados para nove desses cenários. Falta o caso específico de repetir o ID **no cadastro**. Testar IDs duplicados no arquivo carregado não comprova o mesmo caminho. A checagem de duplicidade existe no código, mas falta sua comprovação específica.

Também falta o teste de NUL no arquivo TXT. A rejeição de NUL na entrada do terminal não cobre automaticamente o parser de arquivo.

O relatório e este guia não devem ser usados para afirmar que os testes passaram. A ordem segura é executar, observar, registrar e só depois atualizar os resultados documentados.

## 15. Revisão das escolhas e limitações

### 15.1 Escolhas e justificativas em uma tabela

| Escolha | Justificativa | Limite assumido |
| --- | --- | --- |
| C com módulos pequenos | Demonstra os conteúdos da disciplina de forma localizável. | Não resolve sozinho os riscos de entrada/concorrência. |
| Vetor fixo de 50 structs | Simples, sem alocação dinâmica, fácil de percorrer. | Capacidade limitada e busca linear. |
| Duas situações de estado | Suficiente para pendente/concluído no fluxo atual. | Não há estado persistido de preparo ou falha. |
| `sleep()` curto | Torna a execução simulada observável na apresentação. | Não representa carga de CPU ou equipamento real. |
| Uma função de preparo | Reutiliza as mesmas regras em três modos. | Estado de preparo não é transação com log/arquivo. |
| Pipe anônimo | Comunicação local simples entre pai e filho. | Unidirecional neste uso; não é rede. |
| Transmitir só um inteiro | O pai já conhece o pedido e precisa do resultado. | Não é protocolo de mensagens geral. |
| Duas threads com pedidos distintos | Demonstra memória compartilhada sem disputa pelo mesmo pedido. | Não permite acessos arbitrários ao vetor durante o preparo. |
| Mutex apenas no histórico | Protege o recurso comum sem serializar a espera. | Não coordena vários programas/processos independentes. |
| TXT | Legível, pequeno, sem biblioteca externa. | Delimitador restrito; parser e falhas parciais exigem cuidado. |
| Salvar/carregar manual | Fluxo explícito para demonstrar a persistência. | Usuário pode sair sem salvar. |
| Cinco consultas medidas | Atende ao mínimo de medição de uma operação relevante. | Amostra pequena; sem conclusão forte sobre desempenho. |
| Linux/Codespaces | Disponibiliza ambiente compatível com as APIs usadas. | Build no Windows nativo não é objetivo. |

### 15.2 Pontos positivos encontrados por inspeção

- Responsabilidades separadas e funções de preparo/busca reaproveitadas.
- Vetor principal e contador têm localização clara.
- Entrada trata linha inteira, overflow e EOF.
- Carregamento usa temporários antes de substituir dados, dentro dos limites de validação existentes.
- Pai e filho fecham as pontas não utilizadas; o pai tenta aguardar o filho mesmo com erro de comunicação.
- As duas threads são criadas antes dos joins.
- Mutex não envolve a espera de preparo.
- Logs distinguem corretamente o PID do filho e o PID comum às threads.
- Documentação reconhece falhas parciais e ausência de validação real.

Esses pontos são observações sobre a implementação, não uma certificação de ausência de bugs.

### 15.3 Pendências e cuidados reais

1. **Validar no Codespaces:** GCC/make e execução C não foram comprovados localmente. `OK (skipped=7)` não significa aprovação.
2. **NUL no TXT:** corrigir a possibilidade de aceitar só o prefixo válido e acrescentar teste de regressão.
3. **ID repetido no cadastro:** acrescentar o teste do cenário pedido pelo professor.
4. **Persistência não atômica:** falha ao salvar pode afetar o arquivo anterior; não há backup.
5. **Resultado parcial:** pedido pronto pode ficar sem log; o filho pode preparar sem confirmação no pai.
6. **Instâncias independentes:** não há proteção geral para dois programas gravando os mesmos dados ao mesmo tempo.
7. **Entrega:** faltam evidências finais, tempos reais e slides; o relatório deve receber os resultados depois da execução.
8. **Defesa:** todos devem compreender os módulos, sem depender de uma divisão em que cada pessoa só conhece uma parte.

## 16. Roteiro de leitura e defesa oral

### 16.1 Ordem de leitura recomendada

1. [pedido.h](../include/pedido.h): entender os dados e os contratos.
2. [main.c](../src/main.c): localizar o vetor, o menu e as chamadas.
3. [pedido.c](../src/pedido.c): seguir cadastro, busca e preparo.
4. [arquivo.c](../src/arquivo.c): acompanhar ida e volta do TXT.
5. [log.c](../src/log.c): entender o registro e o mutex.
6. [processo.c](../src/processo.c): acompanhar separadamente pai e filho.
7. [thread.c](../src/thread.c): comparar compartilhamento com o caso de processos.
8. Voltar a `medirDesempenho()` em [main.c](../src/main.c) e depois aos testes.

### 16.2 Perguntas e respostas para treinar

**Onde estão os pedidos enquanto o programa roda?**

No vetor local de `main()`, acompanhado por `total`. O TXT não é consultado a cada busca: ele serve para salvar e recuperar a lista por opções específicas.

**Por que `total` é passado com `&`?**

Porque o cadastro precisa modificar o contador original. Em C, passar apenas o valor criaria outro parâmetro; pelo endereço, a função altera `*total`.

**Por que usamos TXT?**

Porque os quatro campos são simples, o formato é legível e não exige biblioteca de serialização. O enunciado permite essa escolha. Em troca, definimos separadores e validamos o conteúdo.

**O log salva automaticamente o pedido?**

Não. O log registra um evento de preparo. Atualizar `dados/pedidos.txt` exige a opção 9. São arquivos e finalidades diferentes.

**Por que `fork()` sozinho não atualiza o pai?**

Porque o filho altera sua cópia da memória. O estado é transmitido pelo pipe e só então aplicado pelo pai.

**O pai envia o pedido pelo pipe?**

Não nesta implementação. O filho herda sua cópia pelo `fork()`. O pipe leva o resultado do filho ao pai.

**Para que serve `waitpid()`?**

Para aguardar o filho específico e verificar como terminou. Receber bytes pelo pipe não substitui essa verificação de término.

**Por que fechar as pontas não usadas?**

Para liberar recursos e permitir o comportamento correto de EOF. O pai só lê, o filho só escreve nesse canal.

**Qual a diferença principal entre processo e thread no nosso projeto?**

O filho usa memória separada e precisa comunicar o resultado. As threads usam o mesmo vetor e deixam o resultado nele, que é observado depois dos joins.

**Por que não há mutex em volta de todo o preparo?**

Porque cada thread modifica um pedido diferente e o menu espera. A escrita compartilhada é o histórico. Travar durante o `sleep()` serializaria os preparos sem necessidade nesse fluxo.

**Se os logs têm o mesmo PID, são a mesma thread?**

Não. PID identifica o processo. As duas threads pertencem ao mesmo processo, mas são fluxos distintos. O projeto não registra seus IDs individuais de thread.

**`pthread_join()` faz a thread começar?**

Não. A criação é feita com `pthread_create()`. O join aguarda o término; as duas criações acontecem antes da espera.

**O programa fica disponível para outras opções durante o preparo?**

Não. A interface aguarda. Concorrência entre os dois preparos não significa menu assíncrono.

**O que o desempenho mede?**

Cinco buscas do mesmo ID com relógio monotônico; depois calcula menor, maior e média. Não mede o preparo nem compara os três modos.

**Cinco execuções provam que o programa é rápido?**

Não. Atendem ao mínimo didático, mas a operação é curta e a amostra pequena. É preciso reconhecer custo/resolução do relógio e condições do ambiente.

**Todos os testes passaram?**

Ainda não há esse resultado. A sintaxe dos 99 métodos foi verificada, mas a execução local pulou sete classes por falta de GCC. É necessário executar em Linux com compilador e registrar o resultado real.

### 16.3 Demonstração sugerida

Realizar no Codespaces, depois de validar compilação e testes:

1. Mostrar a árvore e explicar rapidamente `src/`, `include/`, `tests/` e `dados/`.
2. Compilar e abrir pela raiz.
3. Cadastrar pedidos distintos e mostrar recusa de ID repetido e consulta inexistente.
4. Preparar um pedido com a opção 4 e consultar seu estado.
5. Preparar outro com 5 e observar filho, PIDs e confirmação do pipe.
6. Preparar dois ainda pendentes com 6 e consultar os dois e o histórico.
7. Medir uma consulta com 8, explicando a amostra e seus limites.
8. Salvar com 9, sair, abrir novamente e carregar com 10.
9. Mostrar uma entrada inválida e o tratamento sem desorganizar o menu.

Esse é um roteiro de estudo e execução futura, não uma lista de resultados já observados. Separar implementação, teste preparado e teste executado é parte importante da defesa técnica.
