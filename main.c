#include <stdio.h>
#include <string.h>
#include "pedido.h"

void exibirMenu(void) {
    printf("\n===== SISTEMA DE PEDIDOS DA LANCHONETE =====\n");
    printf("1  - Cadastrar pedido\n");
    printf("2  - Listar pedidos\n");
    printf("3  - Consultar pedido\n");
    printf("4  - Preparar pedido (sequencial)\n");
    printf("5  - Abrir estacao de preparo (processo + pipe)\n");
    printf("6  - Preparar pedidos em paralelo (threads)\n");
    printf("7  - Ver historico (logs)\n");
    printf("8  - Medir desempenho\n");
    printf("9  - Salvar pedidos\n");
    printf("10 - Carregar pedidos\n");
    printf("0  - Sair\n");
    printf("Digite uma opcao: ");
}

int main(void) {
    int opcao;
    int sair = 0;

    /* vetor fixo de pedidos */
    Pedido pedidos[MAX_PEDIDOS];
    int total = 0;

    while (!sair) {
        exibirMenu();

        /* scanf retorna o numero de itens lidos com sucesso; usamos isso
         * para detectar entrada invalida (ex: letras) sem travar o programa */
        if (scanf("%d", &opcao) != 1) {
            printf("Entrada invalida. Digite um numero.\n");
            while (getchar() != '\n') {
                /* limpa o buffer de entrada, senao o scanf fica em loop */
            }
            continue;
        }

        switch (opcao) {
            case 1: {
                int id, tempo;
                char descricao[100];

                printf("Digite o ID do pedido: ");
                if (scanf("%d", &id) != 1) {
                    printf("ID invalido.\n");
                    while (getchar() != '\n') { }
                    break;
                }
                while (getchar() != '\n') { } /* limpa o '\n' que ficou no buffer antes do fgets */

                printf("Digite a descricao do pedido: ");
                fgets(descricao, sizeof(descricao), stdin);
                descricao[strcspn(descricao, "\n")] = '\0'; /* fgets guarda o '\n', aqui a gente corta */

                printf("Digite o tempo de preparo em segundos (1 a 2): ");
                if (scanf("%d", &tempo) != 1) {
                    printf("Tempo invalido.\n");
                    while (getchar() != '\n') { }
                    break;
                }
                while (getchar() != '\n') { }

                int resultado = cadastrarPedido(pedidos, &total, id, descricao, tempo);
                if (resultado == 1) {
                    printf("Pedido cadastrado com sucesso!\n");
                } else if (resultado == 0) {
                    printf("Erro: ja existe um pedido com o ID %d.\n", id);
                } else {
                    printf("Erro: limite de %d pedidos atingido.\n", MAX_PEDIDOS);
                }
                break;
            }
            case 2:
                listarPedidos(pedidos, total);
                break;
            case 3: {
                int id;
                printf("Digite o ID do pedido a consultar: ");
                if (scanf("%d", &id) != 1) {
                    printf("ID invalido.\n");
                    while (getchar() != '\n') { }
                    break;
                }
                while (getchar() != '\n') { }

                int idx = consultarPedido(pedidos, total, id);
                if (idx == -1) {
                    printf("Pedido com ID %d nao encontrado.\n", id);
                } else {
                    printf("ID: %d\n", pedidos[idx].id);
                    printf("Descricao: %s\n", pedidos[idx].descricao);
                    printf("Tempo de preparo: %ds\n", pedidos[idx].tempoPreparo);
                    printf("Status: %s\n", pedidos[idx].status == PRONTO ? "PRONTO" : "PENDENTE");
                }
                break;
            }
            case 4:
                printf("[Preparar pedido] sera implementado na proxima etapa.\n");
                break;
            case 5:
                printf("[Abrir estacao de preparo] sera implementado na proxima etapa.\n");
                break;
            case 6:
                printf("[Preparar em paralelo] sera implementado na proxima etapa.\n");
                break;
            case 7:
                printf("[Ver historico] sera implementado na proxima etapa.\n");
                break;
            case 8:
                printf("[Medir desempenho] sera implementado na proxima etapa.\n");
                break;
            case 9:
                printf("[Salvar pedidos] sera implementado na proxima etapa.\n");
                break;
            case 10:
                printf("[Carregar pedidos] sera implementado na proxima etapa.\n");
                break;
            case 0:
                printf("Saindo do sistema...\n");
                sair = 1;
                break;
            default:
                printf("Opcao invalida. Tente novamente.\n");
        }
    }

    return 0;
}
