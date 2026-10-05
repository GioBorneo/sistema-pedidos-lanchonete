#include <stdio.h>

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
            case 1:
                printf("[Cadastrar pedido] sera implementado na proxima etapa.\n");
                break;
            case 2:
                printf("[Listar pedidos] sera implementado na proxima etapa.\n");
                break;
            case 3:
                printf("[Consultar pedido] sera implementado na proxima etapa.\n");
                break;
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
