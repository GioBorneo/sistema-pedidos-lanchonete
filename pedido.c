#include <stdio.h>
#include <string.h>
#include "pedido.h"

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
