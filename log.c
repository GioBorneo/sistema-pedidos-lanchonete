#define _POSIX_C_SOURCE 200809L

#include <stdio.h>
#include <time.h>
#include <unistd.h>
#include <errno.h>
#include <math.h>
#include <stdlib.h>
#include <string.h>
#include <pthread.h>
#include "pedido.h"
#include "log.h"

#define CAMINHO_HISTORICO "dados/historico.txt"

/* Cada thread tem seu pedido, mas todas escrevem no mesmo arquivo. */
static pthread_mutex_t mutexHistorico = PTHREAD_MUTEX_INITIALIZER;

int registrarLog(int idPedido, int status, double tempoExecucao) {
    if ((status != PENDENTE && status != PRONTO) ||
        !isfinite(tempoExecucao) || tempoExecucao < 0.0) {
        printf("Erro: status ou tempo de execucao invalido para o historico.\n");
        return 0;
    }

    time_t agora = time(NULL);
    struct tm horario;
    char dataHora[32];
    if (agora == (time_t) -1 || localtime_r(&agora, &horario) == NULL ||
        strftime(dataHora, sizeof(dataHora), "%d/%m/%Y %H:%M:%S", &horario) == 0) {
        printf("Erro ao obter data e hora para o historico.\n");
        return 0;
    }

    int erro = pthread_mutex_lock(&mutexHistorico);
    if (erro != 0) {
        fprintf(stderr, "Erro ao bloquear historico: %s\n", strerror(erro));
        return 0;
    }

    /* Protegemos apenas o arquivo, nao a espera do preparo. */
    int sucesso = 1;
    FILE *arquivo = fopen(CAMINHO_HISTORICO, "a");
    if (arquivo == NULL) {
        perror("Erro ao abrir historico para registrar");
        sucesso = 0;
    } else {
        int resultado = fprintf(arquivo,
                                "%s | PID=%ld | PEDIDO=%d | STATUS=%s | TEMPO=%.3f s\n",
                                dataHora, (long) getpid(), idPedido,
                                status == PRONTO ? "PRONTO" : "PENDENTE", tempoExecucao);
        if (resultado < 0) {
            perror("Erro ao escrever no historico");
            sucesso = 0;
        }
        /* O buffer precisa ser descarregado antes de liberar a outra thread. */
        if (fclose(arquivo) != 0) {
            perror("Erro ao fechar historico");
            sucesso = 0;
        }
    }
    erro = pthread_mutex_unlock(&mutexHistorico);
    if (erro != 0) {
        fprintf(stderr, "Erro ao liberar historico: %s\n", strerror(erro));
        exit(EXIT_FAILURE); /* nao continuar com uma trava de estado incerto */
    }
    return sucesso;
}

int exibirHistorico(void) {
    FILE *arquivo = fopen(CAMINHO_HISTORICO, "r");
    if (arquivo == NULL) {
        if (errno == ENOENT) {
            printf("Nenhum historico registrado.\n");
            return 1;
        }
        perror("Erro ao abrir historico para leitura");
        return 0;
    }

    char linha[256];
    int exibiu = 0;
    int sucesso = 1;
    while (fgets(linha, sizeof(linha), arquivo) != NULL) {
        if (!exibiu) {
            printf("\n===== HISTORICO DE PEDIDOS =====\n");
        }
        if (fputs(linha, stdout) == EOF) {
            perror("Erro ao exibir historico");
            sucesso = 0;
            break;
        }
        exibiu = 1;
    }
    if (ferror(arquivo)) {
        perror("Erro ao ler historico");
        sucesso = 0;
    }
    if (fclose(arquivo) != 0) {
        perror("Erro ao fechar historico");
        sucesso = 0;
    }
    if (sucesso && !exibiu) {
        printf("Nenhum historico registrado.\n");
    }
    return sucesso;
}
