#define _POSIX_C_SOURCE 200809L

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <errno.h>
#include <limits.h>
#include <ctype.h>
#include "pedido.h"
#include "arquivo.h"
#include "log.h"
#include "processo.h"
#include "thread.h"

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

static void medirDesempenho(Pedido pedidos[], int total, int id) {
    int indiceEsperado = consultarPedido(pedidos, total, id);
    if (indiceEsperado == -1) {
        printf("Pedido com ID %d nao encontrado.\n", id);
        return;
    }

    double tempos[5];
    for (int i = 0; i < 5; i++) {
        struct timespec inicio, fim;
        if (clock_gettime(CLOCK_MONOTONIC, &inicio) != 0) {
            perror("Erro ao iniciar medicao da consulta");
            printf("Medicao incompleta; estatisticas nao foram calculadas.\n");
            return;
        }
        /* Medimos so a busca; entrada, impressao e estatisticas ficam de fora. */
        int indice = consultarPedido(pedidos, total, id);
        if (clock_gettime(CLOCK_MONOTONIC, &fim) != 0) {
            perror("Erro ao finalizar medicao da consulta");
            printf("Medicao incompleta; estatisticas nao foram calculadas.\n");
            return;
        }
        if (indice != indiceEsperado) {
            printf("Erro: resultado da consulta mudou durante a medicao.\n");
            printf("Medicao incompleta; estatisticas nao foram calculadas.\n");
            return;
        }
        tempos[i] = (double) (fim.tv_sec - inicio.tv_sec) * 1000.0 +
                    (double) (fim.tv_nsec - inicio.tv_nsec) / 1000000.0;
        if (tempos[i] < 0.0) {
            printf("Erro: intervalo de tempo negativo.\n");
            printf("Medicao incompleta; estatisticas nao foram calculadas.\n");
            return;
        }
    }

    double menor = tempos[0], maior = tempos[0], soma = 0.0;
    printf("\n===== DESEMPENHO DA CONSULTA =====\n");
    printf("ID: %d | Pedidos no vetor: %d | Repeticoes: 5\n", id, total);
    for (int i = 0; i < 5; i++) {
        printf("Execucao %d: %.6f ms\n", i + 1, tempos[i]);
        soma += tempos[i];
        if (tempos[i] < menor) menor = tempos[i];
        if (tempos[i] > maior) maior = tempos[i];
    }
    printf("Menor: %.6f ms\n", menor);
    printf("Maior: %.6f ms\n", maior);
    printf("Media: %.6f ms\n", soma / 5.0);
    printf("Analise: cinco execucoes atendem ao minimo, mas nao garantem estabilidade estatistica.\n");
    printf("A consulta e curta: custo/resolucao do relogio, cache e carga do sistema influenciam os valores.\n");
    printf("Tempos zero sao possiveis; seis casas decimais nao garantem essa precisao.\n");
    printf("Para conclusoes mais fortes, sao necessarias mais repeticoes e condicoes controladas.\n");
}

/* 1 = linha valida, 0 = invalida/longa, -1 = fim de entrada sem dados. */
static int lerLinha(char linha[], size_t tamanho) {
    size_t usados = 0;
    int caractere;
    int invalida = 0, leuAlgo = 0;
    while ((caractere = getchar()) != '\n' && caractere != EOF) {
        leuAlgo = 1;
        if (caractere == '\0') {
            invalida = 1;
        }
        if (usados < tamanho - 1) {
            linha[usados++] = (char) caractere;
        } else {
            invalida = 1; /* continua consumindo, sem deixar restos para o menu */
        }
    }
    if (ferror(stdin)) {
        perror("Erro ao ler entrada");
        exit(EXIT_FAILURE); /* erro de leitura nao e um EOF normal */
    }
    linha[usados] = '\0';
    if (caractere == EOF && !leuAlgo) {
        return -1;
    }
    /* Remove somente o CR da terminacao CRLF, nao um CR dentro da descricao. */
    if (caractere == '\n' && usados > 0 && linha[usados - 1] == '\r') {
        linha[--usados] = '\0';
    }
    if (strchr(linha, '\r') != NULL) {
        invalida = 1;
    }
    return invalida ? 0 : 1;
}

static int lerInteiro(int *valor) {
    char linha[256], *fim;
    int leitura = lerLinha(linha, sizeof(linha));
    if (leitura != 1) {
        return leitura;
    }
    /* fim aponta para o que sobrou: "1abc" nao pode virar o numero 1. */
    errno = 0;
    long numero = strtol(linha, &fim, 10);
    if (fim == linha || errno == ERANGE || numero < INT_MIN || numero > INT_MAX) {
        return 0;
    }
    while (isspace((unsigned char) *fim)) {
        fim++;
    }
    if (*fim != '\0') {
        return 0;
    }
    *valor = (int) numero;
    return 1;
}

int main(void) {
    int opcao;
    int sair = 0;

    /* vetor fixo de pedidos */
    Pedido pedidos[MAX_PEDIDOS];
    int total = 0;

    while (!sair && !feof(stdin)) {
        exibirMenu();

        int leitura = lerInteiro(&opcao);
        if (leitura == -1) {
            return 0;
        }
        if (leitura == 0) {
            printf("Entrada invalida. Digite um numero.\n");
            continue;
        }

        switch (opcao) {
            case 1: {
                int id, tempo;
                char descricao[101]; /* 99 bytes de texto, CR opcional e terminador */

                printf("Digite o ID do pedido: ");
                leitura = lerInteiro(&id);
                if (leitura == -1) {
                    return 0;
                }
                if (leitura == 0) {
                    printf("ID invalido.\n");
                    break;
                }

                printf("Digite a descricao do pedido: ");
                leitura = lerLinha(descricao, sizeof(descricao));
                if (leitura == -1) {
                    return 0;
                }
                if (leitura == 0 || strlen(descricao) > 99) {
                    printf("Erro: descricao invalida ou maior que 99 bytes.\n");
                    break;
                }
                /* O ponto e virgula separa os campos do arquivo TXT. */
                if (strchr(descricao, ';') != NULL) {
                    printf("Erro: descricao nao pode conter ponto e virgula (;).\n");
                    break;
                }

                printf("Digite o tempo de preparo em segundos (1 a 2): ");
                leitura = lerInteiro(&tempo);
                if (leitura == -1) {
                    return 0;
                }
                if (leitura == 0) {
                    printf("Tempo invalido.\n");
                    break;
                }

                if (tempo < 1 || tempo > 2) {
                    printf("Erro: tempo de preparo deve ser entre 1 e 2 segundos.\n");
                    break;
                }

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
                leitura = lerInteiro(&id);
                if (leitura == -1) {
                    return 0;
                }
                if (leitura == 0) {
                    printf("ID invalido.\n");
                    break;
                }

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
            case 4: {
                int id;
                printf("Digite o ID do pedido a preparar: ");
                leitura = lerInteiro(&id);
                if (leitura == -1) {
                    return 0;
                }
                if (leitura == 0) {
                    printf("ID invalido.\n");
                    break;
                }

                int idx = consultarPedido(pedidos, total, id);
                if (idx == -1) {
                    printf("Pedido com ID %d nao encontrado.\n", id);
                } else {
                    prepararPedido(&pedidos[idx]);
                }
                break;
            }
            case 5: {
                int id;
                printf("Digite o ID do pedido para a estacao de preparo: ");
                leitura = lerInteiro(&id);
                if (leitura == -1) {
                    return 0;
                }
                if (leitura == 0) {
                    printf("ID invalido.\n");
                    break;
                }

                int idx = consultarPedido(pedidos, total, id);
                if (idx == -1) {
                    printf("Pedido com ID %d nao encontrado.\n", id);
                } else {
                    abrirEstacaoPreparo(&pedidos[idx]);
                }
                break;
            }
            case 6: {
                int ids[2];
                int leituraValida = 1;
                for (int i = 0; i < 2; i++) {
                    printf("Digite o ID do pedido %d para preparo em paralelo: ", i + 1);
                    leitura = lerInteiro(&ids[i]);
                    if (leitura == -1) {
                        return 0;
                    }
                    if (leitura == 0) {
                        printf("ID invalido.\n");
                        leituraValida = 0;
                        break;
                    }
                    if (feof(stdin) && i == 0) {
                        return 0; /* o par ainda esta incompleto */
                    }
                }
                if (!leituraValida) {
                    break;
                }

                int primeiro = consultarPedido(pedidos, total, ids[0]);
                int segundo = consultarPedido(pedidos, total, ids[1]);
                if (primeiro == -1 || segundo == -1) {
                    printf("Erro: um ou ambos os pedidos nao foram encontrados.\n");
                } else if (prepararPedidosParalelo(&pedidos[primeiro], &pedidos[segundo]) < 0) {
                    /* Sem join confirmado, nao acessamos o vetor nem voltamos ao menu. */
                    exit(EXIT_FAILURE);
                }
                break;
            }
            case 7:
                exibirHistorico();
                break;
            case 8: {
                int id;
                printf("Digite o ID do pedido para medir a consulta (5 repeticoes): ");
                leitura = lerInteiro(&id);
                if (leitura == -1) {
                    return 0;
                }
                if (leitura == 0) {
                    printf("ID invalido.\n");
                    break;
                }
                medirDesempenho(pedidos, total, id);
                break;
            }
            case 9:
                if (salvarPedidos(pedidos, total)) {
                    printf("%d pedido(s) salvo(s) em dados/pedidos.txt.\n", total);
                }
                break;
            case 10:
                if (carregarPedidos(pedidos, &total)) {
                    printf("%d pedido(s) carregado(s) de dados/pedidos.txt.\n", total);
                }
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
