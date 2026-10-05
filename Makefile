CC = gcc
CFLAGS = -Wall -Wextra -pthread

programa: main.c pedido.c pedido.h
	$(CC) $(CFLAGS) -o programa main.c pedido.c

clean:
	rm -f programa
