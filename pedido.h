#ifndef PEDIDO_H
#define PEDIDO_H

#define MAX_PEDIDOS 50
#define PENDENTE 0
#define PRONTO 1

typedef struct {
    int id;
    char descricao[100];
    int tempoPreparo;   /* segundos simulados de preparo */
    int status;         /* PENDENTE ou PRONTO */
} Pedido;

/* retorna 1 = cadastrado, 0 = ID duplicado, -1 = vetor cheio */
int cadastrarPedido(Pedido pedidos[], int *total, int id, const char *descricao, int tempoPreparo);

void listarPedidos(Pedido pedidos[], int total);

/* retorna o indice do pedido no vetor, ou -1 se nao encontrado */
int consultarPedido(Pedido pedidos[], int total, int id);

#endif
