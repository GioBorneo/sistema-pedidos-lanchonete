CC = gcc
CPPFLAGS = -Iinclude
CFLAGS = -Wall -Wextra -pthread

FONTES = src/main.c src/pedido.c src/arquivo.c src/log.c src/processo.c src/thread.c
CABECALHOS = include/pedido.h include/arquivo.h include/log.h include/processo.h include/thread.h

programa: $(FONTES) $(CABECALHOS)
	$(CC) $(CPPFLAGS) $(CFLAGS) -o programa $(FONTES)

.PHONY: clean
clean:
	rm -f programa
