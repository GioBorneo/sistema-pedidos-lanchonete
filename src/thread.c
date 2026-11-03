#include <stdio.h>
#include <string.h>
#include <pthread.h>
#include "thread.h"

static void *prepararNaThread(void *argumento) {
    prepararPedido(argumento);
    return NULL;
}

int prepararPedidosParalelo(Pedido *primeiro, Pedido *segundo) {
    if (primeiro == NULL || segundo == NULL) {
        printf("Erro: pedido invalido para preparo em paralelo.\n");
        return 0;
    }
    if (primeiro == segundo || primeiro->id == segundo->id) {
        printf("Erro: selecione dois pedidos diferentes.\n");
        return 0;
    }

    Pedido *pedidos[2] = {primeiro, segundo};
    for (int i = 0; i < 2; i++) {
        if (pedidos[i]->status != PENDENTE ||
            pedidos[i]->tempoPreparo < 1 || pedidos[i]->tempoPreparo > 2) {
            printf("Erro: pedido %d deve estar pendente e ter tempo de preparo entre 1 e 2 segundos.\n",
                   pedidos[i]->id);
            return 0;
        }
    }

    pthread_t threads[2];
    int criadas = 0;
    /* Criamos ambas antes de aguardar; join logo apos cada create seria sequencial. */
    for (int i = 0; i < 2; i++) {
        int erro = pthread_create(&threads[i], NULL, prepararNaThread, pedidos[i]);
        if (erro != 0) {
            fprintf(stderr, "Erro ao criar thread do pedido %d: %s\n",
                    pedidos[i]->id, strerror(erro));
            break;
        }
        criadas++;
    }

    int falhaEspera = 0;
    for (int i = 0; i < criadas; i++) {
        int erro = pthread_join(threads[i], NULL);
        if (erro != 0) {
            fprintf(stderr, "Erro ao aguardar thread do pedido %d: %s\n",
                    pedidos[i]->id, strerror(erro));
            falhaEspera = 1;
        }
    }
    if (falhaEspera) {
        printf("Termino das threads nao confirmado; encerrando por seguranca.\n");
        return -1;
    }

    /* Threads compartilham o vetor: cada uma altera um pedido distinto.
     * O menu so pode consultar os resultados depois dos joins. */
    if (criadas != 2 || primeiro->status != PRONTO || segundo->status != PRONTO) {
        printf("Preparo em paralelo incompleto; pedidos ja preparados foram mantidos.\n");
        return 0;
    }
    printf("Pedidos %d e %d prontos apos preparo com threads.\n", primeiro->id, segundo->id);
    return 1;
}
