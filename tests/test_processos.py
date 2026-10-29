"""Testes da fase 6. Rodar na raiz: python3 tests/test_processos.py"""

import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


RAIZ = Path(__file__).resolve().parents[1]

# Driver exclusivo dos testes: fork/pipe reais, preparo sem espera e falhas controladas.
DRIVER = r'''
#define _POSIX_C_SOURCE 200809L
#include <stdio.h>
#include <string.h>
#include <unistd.h>
#include <sys/wait.h>
#include <signal.h>
#include <errno.h>
#include "processo.h"

int __real_pipe(int canais[2]);
pid_t __real_fork(void);
ssize_t __real_read(int fd, void *buffer, size_t tamanho);
ssize_t __real_write(int fd, const void *buffer, size_t tamanho);
pid_t __real_waitpid(pid_t pid, int *estado, int opcoes);
int __real_close(int fd);

static const char *cenario;
static pid_t pai;
static int canaisTeste[2];
static int leituras, escritas, esperas, criacoes, fechamentos;

int __wrap_pipe(int canais[2]) {
    if (strcmp(cenario, "pipe") == 0) {
        errno = EMFILE;
        return -1;
    }
    int resultado = __real_pipe(canais);
    if (resultado == 0) {
        canaisTeste[0] = canais[0];
        canaisTeste[1] = canais[1];
    }
    return resultado;
}

pid_t __wrap_fork(void) {
    criacoes++;
    if (strcmp(cenario, "fork") == 0) {
        errno = EAGAIN;
        return -1;
    }
    return __real_fork();
}

int __wrap_close(int fd) {
    fechamentos++;
    int resultado = __real_close(fd);
    if (strcmp(cenario, "close") == 0 && getpid() == pai && fd == canaisTeste[1]) {
        errno = EIO;
        return -1;
    }
    return resultado;
}

ssize_t __wrap_read(int fd, void *buffer, size_t tamanho) {
    leituras++;
    if (strcmp(cenario, "leitura") == 0) {
        errno = EIO;
        return -1;
    }
    if (strcmp(cenario, "interrompido") == 0 && leituras == 1) {
        errno = EINTR;
        return -1;
    }
    if (strcmp(cenario, "parcial") == 0 && tamanho > 1) {
        tamanho = 1;
    }
    return __real_read(fd, buffer, tamanho);
}

ssize_t __wrap_write(int fd, const void *buffer, size_t tamanho) {
    escritas++;
    if (strcmp(cenario, "escrita") == 0) {
        errno = EIO;
        return -1;
    }
    if (strcmp(cenario, "zero") == 0 ||
        (strcmp(cenario, "truncado") == 0 && escritas > 1)) {
        return 0;
    }
    if (strcmp(cenario, "interrompido") == 0 && escritas == 1) {
        errno = EINTR;
        return -1;
    }
    if (strcmp(cenario, "invalido") == 0) {
        int invalido = 99;
        return __real_write(fd, &invalido, sizeof(invalido));
    }
    if ((strcmp(cenario, "parcial") == 0 || strcmp(cenario, "truncado") == 0) && tamanho > 1) {
        tamanho = 1;
    }
    return __real_write(fd, buffer, tamanho);
}

pid_t __wrap_waitpid(pid_t pid, int *estado, int opcoes) {
    esperas++;
    if (strcmp(cenario, "interrompido") == 0 && esperas == 1) {
        errno = EINTR;
        return -1;
    }
    pid_t resultado = __real_waitpid(pid, estado, opcoes);
    if (strcmp(cenario, "espera") == 0 && resultado == pid) {
        errno = ECHILD; /* filho real recolhido antes de simular a falha */
        return -1;
    }
    return resultado;
}

int __wrap_prepararPedido(Pedido *pedido) {
    if (strcmp(cenario, "sinal") == 0) {
        raise(SIGTERM);
    }
    if (strcmp(cenario, "preparo") == 0) {
        return 0;
    }
    pedido->status = PRONTO;
    if (strcmp(cenario, "log") == 0) {
        printf("Aviso de teste: preparo concluido sem log.\n");
    }
    return 1;
}

int main(int argc, char *argv[]) {
    if (argc != 2) {
        return 2;
    }
    pai = getpid();
    cenario = argv[1];
    Pedido pedido = {1, "Pedido de teste", 1, PENDENTE};
    int resultado = abrirEstacaoPreparo(&pedido);
    printf("RESULTADO=%d STATUS=%d ESPERAS=%d LEITURAS=%d CRIACOES=%d FECHAMENTOS=%d\n",
           resultado, pedido.status, esperas, leituras, criacoes, fechamentos);
    return 0;
}
'''


class TestProcessos(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if shutil.which("gcc") is None:
            raise unittest.SkipTest("gcc nao encontrado; execute no Codespaces/Linux com gcc")
        cls.compilacao = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.compilacao.cleanup)
        pasta = Path(cls.compilacao.name)
        cls.programa = pasta / "programa"
        cls.driver = pasta / "teste_processos"
        fonte = pasta / "teste_processos.c"
        fonte.write_text(DRIVER, encoding="utf-8")
        flags = ["gcc", "-Wall", "-Wextra", "-Werror", "-pthread"]
        subprocess.run(
            flags + ["-o", str(cls.programa)] +
            [str(RAIZ / nome) for nome in ("main.c", "pedido.c", "arquivo.c", "log.c", "processo.c", "thread.c")],
            check=True,
        )
        subprocess.run(
            flags + ["-I", str(RAIZ), "-o", str(cls.driver), str(fonte), str(RAIZ / "processo.c"),
                     "-Wl,--wrap=pipe,--wrap=fork,--wrap=read,--wrap=write,--wrap=waitpid,"
                     "--wrap=close,--wrap=prepararPedido"],
            check=True,
        )

    def setUp(self):
        self.pasta = tempfile.TemporaryDirectory()
        self.addCleanup(self.pasta.cleanup)
        self.raiz = Path(self.pasta.name)
        (self.raiz / "dados").mkdir()
        self.pedidos = self.raiz / "dados" / "pedidos.txt"
        self.historico = self.raiz / "dados" / "historico.txt"

    def executar(self, entrada):
        resultado = subprocess.run(
            [str(self.programa)], input=entrada, cwd=self.raiz,
            capture_output=True, text=True, encoding="utf-8", timeout=15,
        )
        self.assertEqual(resultado.returncode, 0, resultado.stderr)
        return resultado.stdout + resultado.stderr

    def executar_driver(self, cenario):
        resultado = subprocess.run(
            [str(self.driver), cenario], cwd=self.raiz,
            capture_output=True, text=True, encoding="utf-8", timeout=5,
        )
        self.assertEqual(resultado.returncode, 0, resultado.stderr)
        return resultado.stdout + resultado.stderr

    def test_preparo_no_filho_pipe_status_no_pai_e_persistencia(self):
        saida = self.executar("1\n1\nBatata\n1\n5\n1\n3\n1\n9\n0\n")
        pids = re.search(r"Caixa: PID pai=(\d+), PID filho=(\d+)", saida)
        self.assertIsNotNone(pids, saida)
        pai, filho = pids.groups()
        self.assertNotEqual(pai, filho)
        self.assertIn(f"Estacao de preparo: PID filho={filho}", saida)
        self.assertIn("Pipe: pedido 1 PRONTO, confirmado no processo pai", saida)
        self.assertIn("Status: PRONTO", saida)
        self.assertEqual(saida.count("===== SISTEMA DE PEDIDOS DA LANCHONETE ====="), 5)
        linhas = self.historico.read_text().splitlines()
        self.assertEqual(len(linhas), 1)
        self.assertIn(f"PID={filho} | PEDIDO=1 | STATUS=PRONTO", linhas[0])
        self.assertEqual(self.pedidos.read_text(), "1;Batata;1;1\n")
        self.assertIn("Status: PRONTO", self.executar("10\n3\n1\n0\n"))

    def test_estacoes_sequenciais_preservam_historico(self):
        saida = self.executar("1\n1\nBatata\n1\n1\n2\nSuco\n1\n5\n1\n5\n2\n0\n")
        self.assertEqual(saida.count("confirmado no processo pai"), 2)
        self.assertEqual(len(self.historico.read_text().splitlines()), 2)

    def test_pedido_pronto_nao_cria_nova_estacao(self):
        saida = self.executar("1\n1\nBatata\n1\n5\n1\n5\n1\n0\n")
        self.assertIn("Pedido 1 ja esta pronto", saida)
        self.assertEqual(saida.count("Estacao de preparo: PID filho="), 1)
        self.assertEqual(len(self.historico.read_text().splitlines()), 1)

    def test_id_inexistente_entrada_invalida_e_eof(self):
        saida = self.executar("5\n99\n5\nabc\n0\n")
        self.assertIn("Pedido com ID 99 nao encontrado", saida)
        self.assertIn("ID invalido", saida)
        self.assertNotIn("PID filho=", saida)
        for entrada in ["5\n", "5\nabc", "5\n99"]:
            with self.subTest(entrada=entrada):
                self.executar(entrada)
        self.assertFalse(self.historico.exists())

    def test_tempo_invalido_nao_cria_estacao(self):
        self.pedidos.write_text("1;Pedido antigo;-1;0\n")
        saida = self.executar("10\n5\n1\n3\n1\n0\n")
        self.assertIn("tempo de preparo entre 1 e 2", saida)
        self.assertIn("Status: PENDENTE", saida)
        self.assertNotIn("PID filho=", saida)
        self.assertFalse(self.historico.exists())

    def test_log_indisponivel_nao_impede_confirmar_preparo(self):
        self.historico.mkdir()
        saida = self.executar("1\n1\nBatata\n1\n5\n1\n3\n1\n9\n0\n")
        self.assertIn("registro no historico nao foi confirmado", saida)
        self.assertIn("confirmado no processo pai", saida)
        self.assertIn("Status: PRONTO", saida)
        self.assertEqual(self.pedidos.read_text(), "1;Batata;1;1\n")

    def test_estacao_nao_salva_txt_automaticamente(self):
        self.pedidos.write_text("1;Batata;1;0\n")
        self.executar("10\n5\n1\n0\n")
        self.assertEqual(self.pedidos.read_text(), "1;Batata;1;0\n")
        self.assertIn("STATUS=PRONTO", self.historico.read_text())

    def test_pipe_e_fork_falham_sem_alterar_pedido(self):
        for cenario in ["pipe", "fork"]:
            with self.subTest(cenario=cenario):
                saida = self.executar_driver(cenario)
                self.assertIn("RESULTADO=0 STATUS=0 ESPERAS=0", saida)
                if cenario == "fork":
                    self.assertIn("FECHAMENTOS=2", saida)

    def test_transferencias_parciais_completam_mensagem(self):
        saida = self.executar_driver("parcial")
        self.assertIn("RESULTADO=1 STATUS=1 ESPERAS=1", saida)
        self.assertIn("confirmado no processo pai", saida)

    def test_io_e_espera_retomam_em_eintr(self):
        saida = self.executar_driver("interrompido")
        self.assertIn("RESULTADO=1 STATUS=1 ESPERAS=2", saida)

    def test_falhas_recolhem_filho_e_nao_confirmam_status(self):
        for cenario in ["leitura", "escrita", "zero", "truncado", "invalido",
                        "preparo", "sinal", "espera", "close"]:
            with self.subTest(cenario=cenario):
                saida = self.executar_driver(cenario)
                self.assertIn("RESULTADO=0 STATUS=0 ESPERAS=1", saida)
                self.assertIn("Resultado do preparo nao confirmado", saida)
                self.assertNotIn("PRONTO, confirmado no processo pai", saida)

    def test_conclusao_com_aviso_de_log_ainda_confirma(self):
        saida = self.executar_driver("log")
        self.assertIn("Aviso de teste: preparo concluido sem log", saida)
        self.assertIn("RESULTADO=1 STATUS=1 ESPERAS=1", saida)


if __name__ == "__main__":
    unittest.main(verbosity=2)
