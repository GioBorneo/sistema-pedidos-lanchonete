CC = gcc
CFLAGS = -Wall -Wextra -pthread

programa: main.c pedido.c pedido.h arquivo.c arquivo.h
	$(CC) $(CFLAGS) -o programa main.c pedido.c arquivo.c

clean:
	rm -f programa
