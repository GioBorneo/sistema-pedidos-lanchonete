# Perguntas e respostas para a apresentação

**Sistema de Pedidos da Lanchonete**  
**Autores: Giovanna Borneo e Felipe Bezerra**

Material de treino para perguntas do professor e da turma. As respostas estão em linguagem de apresentação: curtas, diretas e ligadas ao código real. Não é necessário decorar palavra por palavra; o importante é compreender a ideia e conseguir mostrar onde ela aparece.

> **Para a defesa:** a dupla informou execução bem-sucedida no Codespaces. Preparem o registro dos dez casos exigidos pelo professor, com resultados observados e capturas. As respostas abaixo são um roteiro de estudo, não comprovantes de execução.

## Como treinar

- Uma pessoa faz a pergunta e a outra responde sem ler; depois troquem.
- Tentem responder primeiro em duas ou três frases. Abram o código se pedirem detalhes.
- Nas questões técnicas, leiam também o campo **Se aprofundarem**, quando houver.
- As duas pessoas devem saber explicar o sistema inteiro, não apenas sua parte.

## 1. Perguntas gerais — professor e turma

### 1. Qual é o objetivo do trabalho?

**Resposta sugerida:**

> “Nosso sistema gerencia pedidos de uma lanchonete pelo terminal. Usamos os pedidos para representar tarefas e demonstrar cadastro, consulta, arquivos, processos, comunicação por pipe, threads e logs em C.”

**Onde mostrar:** menu em [main.c](../src/main.c) e modelo em [pedido.h](../include/pedido.h).

### 2. Ele prepara pedidos de verdade? Por que usar `sleep()`?

**Resposta sugerida:**

> “Não, o preparo é simulado. Usamos uma espera de um ou dois segundos para representar uma tarefa e deixar visível quando ela começa e termina. O foco é demonstrar os recursos da disciplina, não controlar uma cozinha real.”

**Se aprofundarem:** `sleep()` suspende a execução da thread que o chamou; não representa dois segundos de uso intenso de CPU. Se for interrompido, o código repete a espera pelo tempo restante.

**Onde mostrar:** `prepararPedido()` em [pedido.c](../src/pedido.c).

### 3. Qual é a arquitetura? O que vocês chamam de núcleo do sistema?

**Resposta sugerida:**

> “Dividimos o sistema em módulos simples. O `main` cuida do menu; `pedido` contém as operações centrais; os outros módulos cuidam de arquivo, processo, threads e histórico. O núcleo é o tipo `Pedido`, a lista em memória e a função `prepararPedido()`, reutilizada nos três modos de preparo.”

**Onde mostrar:** [pedido.h](../include/pedido.h), [pedido.c](../src/pedido.c) e chamadas em [main.c](../src/main.c).

### 4. Por que separar os arquivos em pastas? Qual a diferença entre `.c` e `.h`?

**Resposta sugerida:**

> “Para localizar melhor cada responsabilidade. Em `src` ficam as implementações; em `include`, os tipos e as declarações que os módulos precisam compartilhar. A documentação fica em `docs` e os arquivos gerados pelo programa em `dados`.”

**Se aprofundarem:** incluir um `.h` disponibiliza declarações ao compilador; não executa as funções. Os blocos `#ifndef`/`#define`/`#endif` evitam processar repetidamente o mesmo cabeçalho em uma unidade de compilação.

### 5. Onde o programa deve rodar? Para que serve o Makefile?

**Resposta sugerida:**

> “O alvo é Linux, como o ambiente do Codespaces, porque usamos APIs POSIX. O Makefile reúne o comando de compilação: `make` gera o executável e `./programa` abre o menu. Assim não precisamos digitar todos os fontes e opções manualmente.”

**Se aprofundarem:** `-Iinclude` localiza os cabeçalhos; `-Wall -Wextra` ativa avisos; `-pthread` habilita o suporte de compilação e ligação para threads. Executamos na raiz porque os caminhos de `dados/` são relativos ao diretório de execução. `make clean` remove só o executável.

**Onde mostrar:** [Makefile](../Makefile) e [devcontainer.json](../.devcontainer/devcontainer.json).

## 2. Estruturas, ponteiros e entrada — perguntas comuns do professor

### 6. Como vocês representam um pedido? Por que um vetor fixo?

**Resposta sugerida:**

> “Cada pedido é uma struct com ID, descrição, tempo de preparo e estado. Guardamos até 50 pedidos em um vetor porque é suficiente para o escopo e deixa o código simples, sem alocação dinâmica. A limitação é que a capacidade não cresce automaticamente.”

**Se aprofundarem:** o vetor principal é declarado dentro de `main()`. A variável `total` informa quantas posições estão ocupadas; não percorremos posições vazias como se fossem pedidos.

**Onde mostrar:** [pedido.h](../include/pedido.h) e [main.c](../src/main.c).

### 7. O ID é a posição do pedido? Como funciona a busca?

**Resposta sugerida:**

> “Não. O ID identifica o pedido e pode ser diferente do índice. A busca percorre as posições ocupadas, compara os IDs e retorna o índice encontrado ou menos um. Por isso, o pedido de ID 25 pode estar na posição 1.”

**Se aprofundarem:** é uma busca linear, O(n). O código aceita qualquer valor de `int` como ID, inclusive zero e negativos, desde que não se repita.

**Onde mostrar:** `consultarPedido()` em [pedido.c](../src/pedido.c).

### 8. Por que passar `&total` e `&pedidos[indice]`? O que significa `->`?

**Resposta sugerida:**

> “Em C, os argumentos são passados por valor. Passamos o endereço de `total` para a função alterar o contador original, e o endereço de um pedido para alterar aquela estrutura. O operador `->` acessa um campo da estrutura por meio de um ponteiro.”

**Se aprofundarem:** o ponteiro também é passado por valor, mas sua cópia aponta para o mesmo objeto dentro daquele processo. O parâmetro de vetor permite acessar seus elementos; não copia automaticamente o vetor inteiro.

**Onde mostrar:** `cadastrarPedido()` e `prepararPedido()` em [pedido.c](../src/pedido.c).

### 9. Por que usar leitura por linha e `strtol()`?

**Resposta sugerida:**

> “Para validar a resposta inteira. Com `strtol()` verificamos se houve conversão, se o número cabe em `int` e se sobrou texto inválido. Assim, `1abc` não vira o número 1, e uma linha longa é consumida sem deixar restos para a próxima pergunta.”

**Se aprofundarem:** EOF normal encerra a entrada; erro de leitura é tratado como falha. A descrição tem até 99 bytes, não necessariamente 99 letras, porque caracteres acentuados podem ocupar mais de um byte.

**Onde mostrar:** `lerLinha()` e `lerInteiro()` em [main.c](../src/main.c).

### 10. O que acontece com ID repetido, vetor cheio ou pedido já pronto?

**Resposta sugerida:**

> “O cadastro recusa ID repetido e também recusa inserir além dos 50 pedidos. No preparo, recusamos um pedido que já esteja pronto ou tenha parâmetros inválidos. Isso evita repetir o preparo e gerar outro registro de sucesso para o mesmo pedido pronto.”

**Se aprofundarem:** os códigos de retorno têm significado por função. No cadastro, `-1` é vetor cheio; na consulta, `-1` é não encontrado. Não há um significado universal para o número.

**Onde mostrar:** [pedido.c](../src/pedido.c) e contratos em [pedido.h](../include/pedido.h).

## 3. Persistência — por que TXT e como funciona

### 11. Por que TXT em vez de JSON, banco de dados ou binário?

**Resposta sugerida:**

> “O enunciado permite texto ou binário, e nossos registros têm só quatro campos. Escolhemos TXT porque é legível, fácil de mostrar no editor e pode ser tratado com a biblioteca padrão de C. JSON ou banco de dados acrescentariam estrutura e dependências que não precisamos neste escopo.”

**Se aprofundarem:** binário também seria válido. Gravar uma struct bruta, porém, exigiria considerar padding e representação da plataforma. Nosso TXT também tem limites: exige parser, proíbe o separador na descrição e não possui transações.

**Onde mostrar:** [arquivo.c](../src/arquivo.c).

### 12. Como é o formato do TXT? Por que proibir ponto e vírgula na descrição?

**Resposta sugerida:**

> “Cada linha contém `ID;descricao;tempoPreparo;status`. O ponto e vírgula separa os campos. Como não implementamos uma regra de escape, ele não pode aparecer na descrição, pois ficaria ambíguo onde termina um campo e começa outro.”

**Exemplo apenas ilustrativo:**

```text
10;X-burger;2;0
25;Batata;1;1
```

`0` significa PENDENTE e `1`, PRONTO. A descrição vazia é permitida.

### 13. Salva automaticamente? Carregar acrescenta pedidos à lista?

**Resposta sugerida:**

> “Não há salvamento automático. A opção 9 salva e substitui o TXT; a opção 10 carrega e substitui a lista em memória. Ao abrir o programa, a lista começa vazia. Para recuperar os dados anteriores, precisamos carregar.”

**Se aprofundarem:** salvar uma lista vazia esvazia o arquivo. Carregar um arquivo vazio deixa zero pedidos. Sair sem salvar perde as mudanças da lista que estavam apenas na memória.

**Onde mostrar:** opções 9 e 10 em [main.c](../src/main.c), implementação em [arquivo.c](../src/arquivo.c).

### 14. Por que carregar primeiro em um vetor temporário? Todo arquivo inválido é rejeitado?

**Resposta sugerida:**

> “O temporário evita substituir a lista atual aos poucos. Se detectamos erro de formato, ID repetido, excesso de registros, NUL embutido ou erro de leitura, mantemos a lista anterior. Só copiamos depois da leitura e do fechamento bem-sucedidos.”

**Se aprofundarem:** funções como `strlen()` param no primeiro byte NUL. Por isso, a leitura usa `fgetc()` e rejeita esse byte antes de interpretar a linha.

**Onde mostrar:** `carregarPedidos()` em [arquivo.c](../src/arquivo.c).

### 15. Qual a diferença entre pedidos salvos e histórico? E se a gravação falhar?

**Resposta sugerida:**

> “O TXT de pedidos guarda a lista salva; o histórico registra eventos de preparo. Eles não são atualizados como uma única transação. Se o log falhar depois do preparo, o pedido permanece pronto e aparece um aviso. Se o salvamento falhar, não confirmamos sucesso, mas o arquivo anterior pode já ter sido alterado.”

**Se aprofundarem:** `"w"` cria ou trunca o arquivo; `"a"` acrescenta ao histórico; `"r"` lê. Verificamos `fclose()` porque a escrita pode falhar ao descarregar o buffer. Fechar com sucesso não equivale a uma garantia de recuperação diante de qualquer queda de energia. Não há backup nem salvamento atômico.

**Onde mostrar:** [arquivo.c](../src/arquivo.c), [log.c](../src/log.c) e chamada do logger em [pedido.c](../src/pedido.c).

## 4. Processos e pipe — perguntas técnicas do professor

### 16. O que `fork()` faz? Como sabem quem é pai e quem é filho?

**Resposta sugerida:**

> “O `fork()` cria um processo filho, e ambos continuam a partir da chamada. No filho o retorno é zero; no pai é o PID do filho. Se o retorno for negativo, a criação falhou. Usamos esses retornos para escolher o trabalho de cada processo.”

**Onde mostrar:** `abrirEstacaoPreparo()` em [processo.c](../src/processo.c).

### 17. Se o filho muda o pedido para PRONTO, por que o pai não vê automaticamente?

**Resposta sugerida:**

> “Porque pai e filho têm memórias separadas após o `fork()`. O filho prepara sua cópia. Para atualizar a lista do pai, ele envia o estado pelo pipe, e o pai aplica esse resultado depois das verificações.”

**Se aprofundarem:** um endereço herdado não transforma o objeto em memória compartilhada. O sistema operacional pode usar copy-on-write internamente, mas o efeito observado pelo programa continua sendo isolamento das alterações.

### 18. O que passa pelo pipe? Por que criar antes do `fork()`?

**Resposta sugerida:**

> “Enviamos apenas um inteiro com o estado final. O pai já sabe qual pedido solicitou, então não precisa receber a struct inteira. Criamos o pipe antes para pai e filho herdarem acesso ao mesmo canal.”

**Se aprofundarem:** nesta implementação, o sentido é filho → pai. O pedido não é enviado pelo pipe: sua cópia é herdada pelo filho. O inteiro nativo serve para estes dois processos do mesmo programa, não é um protocolo de rede portável.

### 19. Por que fechar as pontas não utilizadas do pipe?

**Resposta sugerida:**

> “O filho usa a escrita e fecha a leitura; o pai usa a leitura e fecha a escrita. Além de liberar recursos, isso permite detectar EOF corretamente. Se o pai mantivesse uma ponta de escrita aberta, uma leitura poderia continuar esperando mesmo depois do fim do filho.”

**Se aprofundarem:** `canais[0]` é leitura e `canais[1]` é escrita. EOF aparece quando não restam escritores abertos e os dados disponíveis já foram consumidos.

**Onde mostrar:** chamadas de `fecharDescritor()` em [processo.c](../src/processo.c).

### 20. Por que há laços em `read()` e `write()`? O que são `EINTR` e o cast para `char *`?

**Resposta sugerida:**

> “Não presumimos que uma chamada transfira toda a mensagem. Contamos os bytes já transferidos e continuamos até completar o inteiro. Se houver `EINTR`, a chamada foi interrompida por um sinal antes de concluir essa transferência e tentamos novamente.”

**Se aprofundarem:**

```c
(char *) &statusFinal + enviados
```

A conversão permite avançar pelo objeto em bytes. Sem ela, somar a um `int *` avançaria em unidades de `int`. `sizeof(statusFinal)` informa o tamanho completo; a próxima chamada pede só os bytes restantes. Quantidades positivas são contabilizadas, mesmo quando menores que o solicitado.

**Onde mostrar:** laços de envio e recepção em [processo.c](../src/processo.c).

### 21. Receber PRONTO já basta? Para que serve `waitpid()`?

**Resposta sugerida:**

> “Não basta receber bytes. Também aguardamos o filho específico e conferimos se terminou normalmente com código zero. Só confirmamos o pedido com a mensagem completa, estado PRONTO e término bem-sucedido. O `waitpid()` também recolhe o estado de término, evitando deixar um filho encerrado como zumbi.”

**Se aprofundarem:** `waitpid()` não copia o pedido; o pipe transporta esse resultado. Mesmo se a comunicação falhar, o pai tenta aguardar o filho. Se o filho preparou e a confirmação falhou, pode existir log de sucesso enquanto o pedido no pai permanece pendente.

### 22. Por que `fflush()` antes do fork e `_exit()` no filho? O menu fica livre?

**Resposta sugerida:**

> “Descarregamos a saída antes do fork para não duplicar mensagens que estavam no buffer herdado. No fim, o filho descarrega suas mensagens e usa `_exit()` para encerrar sem voltar ao menu nem executar a limpeza da biblioteca herdada. O pai aguarda a conclusão; a estação não fica em segundo plano.”

**Cuidado:** tanto `exit()` quanto `_exit()` podem encerrar o processo filho. A diferença relevante aqui é o tratamento de buffers e rotinas de saída, não uma suposta capacidade de um deles encerrar também o pai.

## 5. Threads e mutex — perguntas que exigem atenção

### 23. Qual a diferença entre processo e thread no trabalho? Por que não usar só um deles?

**Resposta sugerida:**

> “O filho tem memória separada e comunica o resultado pelo pipe. As threads pertencem ao mesmo processo e alteram o vetor compartilhado. Usamos os dois porque o trabalho pede demonstrar esses conceitos, não porque a simulação obrigatoriamente precise dos dois em um produto real.”

**Onde mostrar:** comparar [processo.c](../src/processo.c) e [thread.c](../src/thread.c).

### 24. O que cada thread recebe? O que é `void *`?

**Resposta sugerida:**

> “Cada thread recebe o endereço de um pedido diferente. A API usa `void *`, um ponteiro genérico, para aceitar diferentes tipos de argumento. Nossa função auxiliar recebe esse endereço e chama o mesmo `prepararPedido()` usado nos outros modos.”

**Se aprofundarem:** o worker retorna `NULL`; o resultado do preparo fica no campo `status` do pedido compartilhado. O vetor de `main()` continua existindo enquanto as threads trabalham.

**Onde mostrar:** `prepararNaThread()` em [thread.c](../src/thread.c).

### 25. Por que criar as duas threads antes de usar `pthread_join()`?

**Resposta sugerida:**

> “Para permitir que os dois preparos se sobreponham. Se criássemos uma thread e esperássemos seu término antes de criar a outra, o fluxo seria sequencial. O join aguarda uma thread; ele não a cria e não impede que a outra já criada trabalhe.”

**Resumo para lembrar:** criar A → criar B → aguardar A → aguardar B.

### 26. Por que não há mutex protegendo o vetor de pedidos?

**Resposta sugerida:**

> “Porque recusamos o mesmo pedido e cada thread altera um elemento diferente. O menu aguarda os joins antes de ler ou modificar os resultados, e o contador não muda durante o preparo. Nessas condições, não há acesso conflitante aos mesmos campos.”

**Se aprofundarem:** essa justificativa depende do fluxo atual. Permitir leitura/escrita simultânea do mesmo pedido, cadastro durante o preparo ou acesso ao vetor com término de thread incerto exigiria rever a sincronização. Não significa que ‘vetor nunca precisa de mutex’.

**Onde mostrar:** validação do par e joins em [thread.c](../src/thread.c).

### 27. Então por que há mutex no histórico? Qual é a seção crítica?

**Resposta sugerida:**

> “Os pedidos são diferentes, mas o histórico é o mesmo arquivo. O mutex organiza o acesso: uma thread abre, escreve e fecha antes de a outra entrar nessa região. Não travamos o `sleep()`, porque isso serializaria desnecessariamente os preparos.”

**Se aprofundarem:** fechar o arquivo ainda dentro da trava inclui a descarga do buffer na região protegida. O mutex não protege todas as mensagens do terminal nem coordena programas independentes. A consulta de histórico ocorre pelo menu depois dos preparos, sem leitores concorrentes nesse fluxo.

**Onde mostrar:** `mutexHistorico`, lock e unlock em [log.c](../src/log.c).

### 28. O que acontece se uma thread não for criada ou se o join falhar?

**Resposta sugerida:**

> “Se a segunda criação falhar, aguardamos a primeira; um pedido pode ter ficado pronto e não desfazemos isso. Se um join falhar, tentamos aguardar as demais e retornamos um erro especial. O menu encerra em vez de continuar usando dados de threads cujo término não foi confirmado.”

**Se aprofundarem:** erros pthread são obtidos pelo retorno da função e explicados com `strerror(erro)`, não presumindo que estejam em `errno`.

**Onde mostrar:** [thread.c](../src/thread.c) e tratamento da opção 6 em [main.c](../src/main.c).

### 29. Ter o mesmo PID significa ser a mesma thread? A ordem dos logs é fixa?

**Resposta sugerida:**

> “Não. As threads pertencem ao mesmo processo e por isso o log mostra o mesmo PID. Elas têm identidades próprias de thread, mas não registramos esses identificadores. A ordem de mensagens e logs pode variar conforme o escalonamento.”

**Se aprofundarem:** o mutex controla a entrada na seção crítica; não define antecipadamente qual thread deve entrar primeiro.

### 30. Threads garantem mais velocidade? Concorrência é igual a paralelismo?

**Resposta sugerida:**

> “Não garantem. Concorrência permite que os trabalhos avancem com sobreposição; paralelismo é executar ao mesmo tempo, o que depende do ambiente. Como usamos espera simulada, esperamos que as esperas se sobreponham, mas não coletamos uma comparação de desempenho para afirmar um ganho medido.”

**Se aprofundarem:** para dois preparos de dois segundos, uma expectativa didática é perto de quatro segundos sequenciais e perto de dois com sobreposição, mais custos adicionais. Isso é uma expectativa, não um resultado observado nem uma promessa de tempo exato. O menu continua bloqueado nos joins.

## 6. Desempenho e testes — como responder sem exagerar

### 31. O que a opção de desempenho mede? Por que relógio monotônico?

**Resposta sugerida:**

> “Medimos cinco chamadas de consulta por ID e calculamos menor, maior e média em milissegundos. Entrada, impressão e estatísticas ficam fora dos intervalos. Usamos relógio monotônico para medir tempo decorrido sem depender de ajustes no relógio civil.”

**Se aprofundarem:** uma consulta preliminar, fora das cinco medidas, confirma que o ID existe. No log, usamos data/hora civil para indicar quando aconteceu e relógio monotônico para a duração. `clock()` mede CPU, não a espera decorrida que queremos observar no preparo.

**Onde mostrar:** `medirDesempenho()` em [main.c](../src/main.c) e medição em [pedido.c](../src/pedido.c).

### 32. Cinco medições são suficientes? Um tempo zero é erro?

**Resposta sugerida:**

> “Cinco atendem ao mínimo do enunciado, mas não demonstram estabilidade estatística. A busca é curta e sofre influência do custo e da resolução do relógio, do cache e da carga do sistema. Um intervalo zero pode acontecer; mais casas decimais na impressão não garantem mais precisão.”

**Se aprofundarem:** a opção não mede preparo nem compara processo e threads. Para conclusões mais fortes, seriam necessárias mais repetições, condições controladas e um experimento apropriado à comparação.

### 33. Como vocês verificam os dez casos exigidos?

**Resposta sugerida:**

> “O roteiro cobre cadastro válido e duplicado, consulta válida e inexistente, salvar, carregar, processo, comunicação pelo pipe, threads e entrada inválida. Os casos podem ser executados pelo menu, comparando o resultado observado com o esperado.”

**Se aprofundarem:** o enunciado não exige automação nem Python. Os testes automatizados usados como apoio ficaram fora da entrega; o programa entregue é C e não depende deles.

**Onde mostrar:** [roteiro de testes no README](../README.md#testes) e capturas em [evidencias/](evidencias/).

**Antes da defesa:** preparem os registros reais dos dez casos. Só afirmem aprovação dos cenários que foram executados e conferidos.

## 7. Perguntas críticas e curiosidades da turma

### 34. Quais limitações vocês reconhecem? O que melhorariam primeiro?

**Resposta sugerida:**

> “O sistema é didático: tem limite de 50 pedidos, salvamento manual e menu que espera o preparo. Uma melhoria futura seria tornar o salvamento mais seguro para reduzir o risco de arquivo parcial, por exemplo usando um arquivo temporário antes de substituir o original.”

**Se aprofundarem:** também não há exclusão de pedido, cancelamento, múltiplas instâncias coordenadas ou recuperação automática quando filho, pai e log ficam divergentes. Interface gráfica, banco de dados e recursos novos seriam possibilidades futuras, não funcionalidades já prontas.

### 35. O que vocês aprenderam? Como dividiram o trabalho? Usaram ajuda externa ou IA?

**Resposta sobre aprendizado, se corresponder à experiência real:**

> “A principal diferença foi perceber que mudar um dado no filho não muda o pai, enquanto threads compartilham a memória. Também entendemos por que precisamos aguardar o término e proteger o recurso realmente compartilhado, que é o histórico.”

**Sobre divisão de tarefas:** descrevam o que cada pessoa realmente fez, sem inventar uma separação de módulos. Ambas devem conseguir explicar as partes cobradas.

**Sobre ajuda externa ou IA:** respondam com transparência, de acordo com o uso real e as regras da disciplina. Uma estrutura possível, a adaptar aos fatos, é: “Usamos apoio em [etapas reais]; nossa participação foi [atividades reais]. Podemos mostrar o código e explicar as decisões.” Não afirmem autoria sem assistência ou validação independente se isso não aconteceu.

### 36. “Pode mostrar isso funcionando agora?”

**Resposta sugerida:**

> “Podemos seguir o fluxo: cadastrar pedidos diferentes, preparar nos modos disponíveis, consultar os estados e o histórico e demonstrar salvar e carregar. Também podemos mostrar uma entrada inválida.”

**Preparação prática:** antes da apresentação, verificar o ambiente, compilar e ensaiar os passos. Se falhar ao vivo, mostrar a mensagem, distinguir falha de ambiente de falha do programa e explicar somente o que conseguirem comprovar. Não afirmar que funcionou se a demonstração falhou.

**Ponto de atenção:** o pedido já pronto não prepara de novo. Para mostrar os três modos na mesma sessão, reservem quatro pedidos pendentes: um para o sequencial, um para o processo e dois para as threads.

## Cartão de revisão rápida

| Se perguntarem… | Lembrar desta ideia |
| --- | --- |
| Por que TXT? | Legível, quatro campos, biblioteca padrão; tem limites de formato. |
| Por que ponteiro? | Alterar o objeto original naquele processo. |
| Por que pipe? | Filho e pai têm memórias separadas. |
| Por que `waitpid()`? | Recolher e verificar o término do filho; não transporta o pedido. |
| Por que criar antes do join? | Permitir sobreposição dos preparos. |
| Por que mutex no log? | Mesmo arquivo, acesso organizado entre as threads. |
| Por que não no vetor? | Pedidos distintos e menu aguardando os joins. |
| Por que mesmo PID? | Threads pertencem ao mesmo processo. |
| O que foi medido? | Cinco consultas; não comparação entre modos de preparo. |
| O que foi comprovado em testes? | Informar a última execução real, sem contar skips como aprovação. |

## Frases que devemos evitar

- **“O pipe compartilha a memória.”** Ele transporta bytes entre processos.
- **“O join cria a thread.”** Quem cria é `pthread_create()`; o join aguarda.
- **“O mutex deixa tudo mais rápido.”** Ele organiza o acesso; o ganho de tempo não é sua finalidade.
- **“Threads são sempre mais rápidas.”** Depende da tarefa, do ambiente e dos custos envolvidos.
- **“Fechar o arquivo garante que nunca perderemos dados.”** Não há tal garantia geral.
- **“Tudo inválido é rejeitado.”** As validações cobrem os casos previstos, mas não são garantia contra qualquer arquivo ou entrada possível.
- **“Todos os testes passaram.”** Só dizer isso com os resultados observados dos casos executados, não apenas com uma lista de resultados esperados.

## Se não soubermos responder na hora

Uma resposta segura é:

> “Esse detalhe eu preciso conferir. Posso mostrar o trecho e explicar o fluxo que implementamos, mas não quero afirmar uma garantia que nosso código não oferece.”

Não substitui o estudo: usem quando houver dúvida real. É melhor reconhecer um limite do que inventar uma explicação.

Para revisar a arquitetura completa, consultar o [Guia do projeto](GUIA_DO_PROJETO.md). Para comandos e pendências, consultar o [README](../README.md).
