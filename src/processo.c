#define _POSIX_C_SOURCE 200809L

#include <stdio.h>
#include <unistd.h>
#include <sys/wait.h>
#include <errno.h>
#include "processo.h"

static int fecharDescritor(int descritor) {
    if (close(descritor) != 0) {
        perror("Erro ao fechar descritor do pipe");
        return 0;
    }
    return 1;
}

int abrirEstacaoPreparo(Pedido *pedido) {
    if (pedido == NULL) {
        printf("Erro: pedido invalido para a estacao de preparo.\n");
        return 0;
    }
    if (pedido->status == PRONTO) {
        printf("Pedido %d ja esta pronto.\n", pedido->id);
        return 0;
    }
    if (pedido->status != PENDENTE || pedido->tempoPreparo < 1 || pedido->tempoPreparo > 2) {
        printf("Erro: pedido deve estar pendente e ter tempo de preparo entre 1 e 2 segundos.\n");
        return 0;
    }

    /* Evita que o filho imprima novamente o menu guardado no buffer do pai. */
    if (fflush(stdout) == EOF) {
        perror("Erro ao descarregar saida antes de criar processo");
        return 0;
    }

    int canais[2];
    if (pipe(canais) != 0) {
        perror("Erro ao criar pipe");
        return 0;
    }
    pid_t filho = fork();
    if (filho < 0) {
        perror("Erro ao criar processo filho");
        fecharDescritor(canais[0]);
        fecharDescritor(canais[1]);
        return 0;
    }

    if (filho == 0) {
        /* Filho escreve; nao precisa da ponta de leitura. */
        int sucesso = fecharDescritor(canais[0]);
        if (sucesso) {
            if (printf("Estacao de preparo: PID filho=%ld.\n", (long) getpid()) < 0) {
                sucesso = 0;
            } else {
                sucesso = prepararPedido(pedido);
            }
        }

        int statusFinal = pedido->status;
        size_t enviados = 0;
        while (sucesso && enviados < sizeof(statusFinal)) {
            ssize_t quantidade = write(canais[1], (char *) &statusFinal + enviados,
                                       sizeof(statusFinal) - enviados);
            if (quantidade < 0) {
                if (errno == EINTR) {
                    continue;
                }
                perror("Erro ao enviar resultado pelo pipe");
                sucesso = 0;
            } else if (quantidade == 0) {
                printf("Erro: envio do resultado pelo pipe incompleto.\n");
                sucesso = 0;
            } else {
                enviados += (size_t) quantidade;
            }
        }
        if (!fecharDescritor(canais[1])) {
            sucesso = 0;
        }
        if (fflush(stdout) == EOF) {
            perror("Erro ao descarregar saida do filho");
            sucesso = 0;
        }
        /* _exit encerra apenas o filho, sem voltar ao menu ou limpar buffers herdados. */
        _exit(sucesso ? 0 : 1);
    }

    /* Pai so le; fechar a escrita permite detectar EOF quando o filho terminar. */
    int sucesso = fecharDescritor(canais[1]);
    if (printf("Caixa: PID pai=%ld, PID filho=%ld.\n", (long) getpid(), (long) filho) < 0) {
        sucesso = 0;
    }
    int statusRecebido = PENDENTE;
    size_t recebidos = 0;
    while (sucesso && recebidos < sizeof(statusRecebido)) {
        ssize_t quantidade = read(canais[0], (char *) &statusRecebido + recebidos,
                                  sizeof(statusRecebido) - recebidos);
        if (quantidade < 0) {
            if (errno == EINTR) {
                continue;
            }
            perror("Erro ao receber resultado pelo pipe");
            sucesso = 0;
        } else if (quantidade == 0) {
            printf("Erro: filho encerrou sem enviar um resultado completo.\n");
            sucesso = 0;
        } else {
            recebidos += (size_t) quantidade;
        }
    }
    if (!fecharDescritor(canais[0])) {
        sucesso = 0;
    }

    /* Mesmo com falha na leitura, recolhemos o filho para nao deixar um zumbi. */
    int estadoFilho;
    pid_t esperado;
    do {
        esperado = waitpid(filho, &estadoFilho, 0);
    } while (esperado < 0 && errno == EINTR);
    if (esperado < 0) {
        perror("Erro ao aguardar processo filho");
        sucesso = 0;
    } else if (!WIFEXITED(estadoFilho) || WEXITSTATUS(estadoFilho) != 0) {
        printf("Erro: processo filho terminou sem sucesso.\n");
        sucesso = 0;
    }
    if (sucesso && statusRecebido != PRONTO) {
        printf("Erro: status recebido da estacao de preparo e invalido.\n");
        sucesso = 0;
    }
    if (!sucesso) {
        printf("Resultado do preparo nao confirmado; status no pai foi mantido.\n");
        return 0;
    }

    /* fork cria memorias separadas: so o pipe permite atualizar a copia do pai. */
    pedido->status = statusRecebido;
    printf("Pipe: pedido %d PRONTO, confirmado no processo pai.\n", pedido->id);
    return 1;
}
