CC = gcc
CFLAGS = -Wall -Wextra -pthread

programa: main.c
	$(CC) $(CFLAGS) -o programa main.c

clean:
	rm -f programa
