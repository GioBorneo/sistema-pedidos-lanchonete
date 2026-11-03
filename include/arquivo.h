#ifndef ARQUIVO_H
#define ARQUIVO_H

#include "pedido.h"

/* retornam 1 = sucesso, 0 = erro; o caminho e dados/pedidos.txt */
int salvarPedidos(const Pedido pedidos[], int total);
int carregarPedidos(Pedido pedidos[], int *total);

#endif
