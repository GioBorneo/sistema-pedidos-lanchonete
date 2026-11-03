#ifndef PROCESSO_H
#define PROCESSO_H

#include "pedido.h"

/* 1 = preparo confirmado no pai; 0 = recusado ou resultado nao confirmado.
 * Em falhas de comunicacao, o filho pode ter preparado sem o pai confirmar. */
int abrirEstacaoPreparo(Pedido *pedido);

#endif
