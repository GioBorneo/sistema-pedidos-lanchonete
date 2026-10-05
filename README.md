# Sistema de Pedidos da Lanchonete

Trabalho Prático Integrador — Programação de Software Básico em C.

Sistema de gerenciamento e monitoramento de pedidos de uma lanchonete, usando processos (`fork`), threads (`pthreads`), comunicação entre processos (pipe) e persistência em arquivo.

## Status atual

**Fase 2** — cadastrar, listar e consultar pedidos (RF01-03) funcionando.

- Fase 1: menu principal navegável (estrutura inicial, sem lógica de negócio) — concluída.
- Fase 2: módulo `pedido.c/h` com cadastro, listagem e consulta de pedidos — concluída.
- Próxima fase: salvar/carregar pedidos em arquivo (RF05-06).

## Como rodar (GitHub Codespaces)

1. No repositório no GitHub, clique em **Code > Codespaces > Create codespace on main**.
2. Aguarde o ambiente carregar (já vem com `gcc`/`make` configurados).
3. No terminal do Codespace, rode:
   ```bash
   make
   ./programa
   ```

