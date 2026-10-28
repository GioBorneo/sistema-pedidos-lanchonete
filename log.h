#ifndef LOG_PEDIDOS_H
#define LOG_PEDIDOS_H

/* Retornam 1 = sucesso, 0 = erro. Tempo de execucao em segundos. */
int registrarLog(int idPedido, int status, double tempoExecucao);
int exibirHistorico(void);

#endif
