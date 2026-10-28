#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <errno.h>
#include <limits.h>
#include "arquivo.h"

#define CAMINHO_PEDIDOS "dados/pedidos.txt"

static int lerInteiro(const char *texto, int *valor) {
    char *fim;
    long numero;

    errno = 0;
    numero = strtol(texto, &fim, 10);
    /* strtol permite detectar letras, campo vazio e numeros fora do limite. */
    if (fim == texto || *fim != '\0' || errno == ERANGE ||
        numero < INT_MIN || numero > INT_MAX) {
        return 0;
    }

    *valor = (int) numero;
    return 1;
}

static int lerPedido(char linha[], Pedido *pedido) {
    char *campos[4];
    campos[0] = linha;

    /* Separar manualmente preserva uma descricao vazia, ao contrario de strtok. */
    for (int i = 0; i < 3; i++) {
        char *separador = strchr(campos[i], ';');
        if (separador == NULL) {
            return 0;
        }
        *separador = '\0';
        campos[i + 1] = separador + 1;
    }

    if (strchr(campos[3], ';') != NULL ||
        strlen(campos[1]) >= sizeof(pedido->descricao) ||
        strchr(campos[1], '\r') != NULL) {
        return 0;
    }

    if (!lerInteiro(campos[0], &pedido->id) ||
        !lerInteiro(campos[2], &pedido->tempoPreparo) ||
        !lerInteiro(campos[3], &pedido->status)) {
        return 0;
    }
    if (pedido->status != PENDENTE && pedido->status != PRONTO) {
        return 0;
    }

    strcpy(pedido->descricao, campos[1]);
    return 1;
}

int salvarPedidos(const Pedido pedidos[], int total) {
    FILE *arquivo = fopen(CAMINHO_PEDIDOS, "w");
    if (arquivo == NULL) {
        perror("Erro ao abrir arquivo para salvar pedidos");
        return 0;
    }

    /* TXT facilita conferir os dados no editor: ID;descricao;tempo;status. */
    for (int i = 0; i < total; i++) {
        if (fprintf(arquivo, "%d;%s;%d;%d\n", pedidos[i].id,
                    pedidos[i].descricao, pedidos[i].tempoPreparo,
                    pedidos[i].status) < 0) {
            perror("Erro ao escrever pedidos");
            if (fclose(arquivo) != 0) {
                perror("Erro ao fechar arquivo de pedidos");
            }
            return 0;
        }
    }

    /* A escrita pode falhar apenas ao descarregar o buffer no fechamento. */
    if (fclose(arquivo) != 0) {
        perror("Erro ao fechar arquivo de pedidos");
        return 0;
    }
    return 1;
}

int carregarPedidos(Pedido pedidos[], int *total) {
    FILE *arquivo = fopen(CAMINHO_PEDIDOS, "r");
    if (arquivo == NULL) {
        perror("Erro ao abrir arquivo para carregar pedidos");
        return 0;
    }

    Pedido temporarios[MAX_PEDIDOS];
    int quantidade = 0;
    int numeroLinha = 0;
    int valido = 1;
    char linha[256];

    /* So substituimos os pedidos atuais depois de validar o arquivo inteiro. */
    while (fgets(linha, sizeof(linha), arquivo) != NULL) {
        Pedido pedido;
        numeroLinha++;
        size_t tamanho = strlen(linha);
        if (tamanho == sizeof(linha) - 1) {
            printf("Erro: linha %d muito longa no arquivo de pedidos.\n", numeroLinha);
            valido = 0;
            break;
        }
        if (tamanho > 0 && linha[tamanho - 1] == '\n') {
            linha[--tamanho] = '\0';
        }
        if (tamanho > 0 && linha[tamanho - 1] == '\r') {
            linha[--tamanho] = '\0'; /* aceita arquivos com quebra de linha do Windows */
        }

        if (!lerPedido(linha, &pedido)) {
            printf("Erro: formato invalido na linha %d do arquivo de pedidos.\n", numeroLinha);
            valido = 0;
            break;
        }

        int resultado = cadastrarPedido(temporarios, &quantidade, pedido.id,
                                        pedido.descricao, pedido.tempoPreparo);
        if (resultado != 1) {
            if (resultado == 0) {
                printf("Erro: ID duplicado na linha %d do arquivo de pedidos.\n", numeroLinha);
            } else {
                printf("Erro: arquivo excede o limite de %d pedidos.\n", MAX_PEDIDOS);
            }
            valido = 0;
            break;
        }
        /* O cadastro inicia como PENDENTE; aqui restauramos o status salvo. */
        temporarios[quantidade - 1].status = pedido.status;
    }

    if (ferror(arquivo)) {
        perror("Erro ao ler arquivo de pedidos");
        valido = 0;
    }
    if (fclose(arquivo) != 0) {
        perror("Erro ao fechar arquivo de pedidos");
        valido = 0;
    }
    if (!valido) {
        printf("Os pedidos atuais foram mantidos.\n");
        return 0;
    }

    for (int i = 0; i < quantidade; i++) {
        pedidos[i] = temporarios[i];
    }
    *total = quantidade;
    return 1;
}
