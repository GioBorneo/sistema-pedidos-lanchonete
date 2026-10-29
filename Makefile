CC = gcc
CFLAGS = -Wall -Wextra -pthread

programa: main.c pedido.c pedido.h arquivo.c arquivo.h log.c log.h processo.c processo.h
	$(CC) $(CFLAGS) -o programa main.c pedido.c arquivo.c log.c processo.c

clean:
	rm -f programa
