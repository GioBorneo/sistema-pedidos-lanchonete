#ifndef LOG_PEDIDOS_H
#define LOG_PEDIDOS_H

/* Retornam 1 = sucesso, 0 = erro. Tempo de execucao em segundos.
 * Gravar usa mutex entre threads; consultar ocorre depois dos joins.
 * Falha excepcional ao liberar o mutex encerra o programa com erro. */
int registrarLog(int idPedido, int status, double tempoExecucao);
int exibirHistorico(void);

#endif
