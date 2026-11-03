#ifndef THREAD_PEDIDOS_H
#define THREAD_PEDIDOS_H

#include "pedido.h"

/* 1 = ambos prontos; 0 = recusado ou preparo parcial; -1 = falha de join.
 * Com -1, o chamador deve encerrar sem voltar ao menu. */
int prepararPedidosParalelo(Pedido *primeiro, Pedido *segundo);

#endif
