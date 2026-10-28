#define _POSIX_C_SOURCE 200809L

#include <stdio.h>
#include <string.h>
#include <time.h>
#include <unistd.h>
#include "pedido.h"
#include "log.h"

int cadastrarPedido(Pedido pedidos[], int *total, int id, const char *descricao, int tempoPreparo) {
    if (*total >= MAX_PEDIDOS) {
        return -1;
    }

    /* percorre o vetor pra garantir que nao existe outro pedido com esse ID */
    for (int i = 0; i < *total; i++) {
        if (pedidos[i].id == id) {
            return 0;
        }
    }

    pedidos[*total].id = id;
    strncpy(pedidos[*total].descricao, descricao, sizeof(pedidos[*total].descricao) - 1);
    pedidos[*total].descricao[sizeof(pedidos[*total].descricao) - 1] = '\0';
    pedidos[*total].tempoPreparo = tempoPreparo;
    pedidos[*total].status = PENDENTE;

    /* total e recebido por ponteiro porque essa funcao precisa alterar
     * o contador la de dentro do main(), e C passa variaveis por valor */
    (*total)++;

    return 1;
}

void listarPedidos(Pedido pedidos[], int total) {
    if (total == 0) {
        printf("Nenhum pedido cadastrado.\n");
        return;
    }

    printf("\n%-5s %-30s %-10s\n", "ID", "DESCRICAO", "STATUS");
    for (int i = 0; i < total; i++) {
        printf("%-5d %-30s %-10s\n",
               pedidos[i].id,
               pedidos[i].descricao,
               pedidos[i].status == PRONTO ? "PRONTO" : "PENDENTE");
    }
}

int consultarPedido(Pedido pedidos[], int total, int id) {
    for (int i = 0; i < total; i++) {
        if (pedidos[i].id == id) {
            return i;
        }
    }
    return -1;
}

int prepararPedido(Pedido *pedido) {
    if (pedido == NULL) {
        printf("Erro: pedido invalido para preparo.\n");
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

    struct timespec inicio, fim;
    /* O relogio monotonico mede tempo decorrido, incluindo a espera do sleep. */
    if (clock_gettime(CLOCK_MONOTONIC, &inicio) != 0) {
        perror("Erro ao iniciar medicao do preparo");
        return 0;
    }

    printf("Preparando pedido %d (%ds)...\n", pedido->id, pedido->tempoPreparo);
    fflush(stdout);
    unsigned int restante = (unsigned int) pedido->tempoPreparo;
    while (restante > 0) {
        restante = sleep(restante); /* retoma a espera se um sinal interromper o sleep */
    }
    pedido->status = PRONTO;

    /* O preparo ja terminou: falhas de medicao ou log nao desfazem o resultado. */
    if (clock_gettime(CLOCK_MONOTONIC, &fim) != 0) {
        perror("Erro ao finalizar medicao do preparo");
        printf("Pedido %d pronto, mas sem duracao medida e sem registro no historico.\n", pedido->id);
        return 1;
    }

    double duracao = (double) (fim.tv_sec - inicio.tv_sec) +
                     (double) (fim.tv_nsec - inicio.tv_nsec) / 1000000000.0;
    printf("Pedido %d pronto! Tempo de execucao: %.3f s.\n", pedido->id, duracao);
    if (!registrarLog(pedido->id, pedido->status, duracao)) {
        printf("Aviso: pedido pronto, mas o registro no historico nao foi confirmado.\n");
    }
    return 1;
}
