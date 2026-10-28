"""Testes da fase 5. Rodar na raiz: python3 tests/test_preparo.py"""

import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


RAIZ = Path(__file__).resolve().parents[1]

# Wrappers existem apenas neste teste: simulam falhas sem mudar o programa real.
DRIVER = r'''
#define _POSIX_C_SOURCE 200809L
#include <stdio.h>
#include <string.h>
#include <time.h>
#include <errno.h>
#include "pedido.h"

static const char *cenario;
static int relogios, esperas, logs;

int __wrap_clock_gettime(clockid_t relogio, struct timespec *valor) {
    relogios++;
    if (relogio != CLOCK_MONOTONIC ||
        (strcmp(cenario, "inicio") == 0 && relogios == 1) ||
        (strcmp(cenario, "fim") == 0 && relogios == 2)) {
        errno = EIO;
        return -1;
    }
    valor->tv_sec = relogios == 1 ? 10 : 12;
    valor->tv_nsec = relogios == 1 ? 900000000L : 100000000L;
    return 0;
}

unsigned int __wrap_sleep(unsigned int segundos) {
    esperas++;
    printf("ESPERA=%u\n", segundos);
    return strcmp(cenario, "interrompido") == 0 && esperas == 1 ? 1 : 0;
}

int __wrap_registrarLog(int id, int status, double tempo) {
    logs++;
    printf("LOG=%d;%d;%.3f\n", id, status, tempo);
    return strcmp(cenario, "log") != 0;
}

int main(int argc, char *argv[]) {
    if (argc != 2) {
        return 2;
    }
    cenario = argv[1];
    Pedido pedido = {1, "Pedido de teste", 2, PENDENTE};
    int resultado = prepararPedido(&pedido);
    printf("RESULTADO=%d STATUS=%d RELOGIOS=%d ESPERAS=%d LOGS=%d\n",
           resultado, pedido.status, relogios, esperas, logs);
    return 0;
}
'''


class TestPreparo(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if shutil.which("gcc") is None:
            raise unittest.SkipTest("gcc nao encontrado; execute no Codespaces/Linux com gcc")
        cls.compilacao = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.compilacao.cleanup)
        pasta = Path(cls.compilacao.name)
        cls.programa = pasta / "programa"
        cls.driver = pasta / "teste_preparo"
        fonte = pasta / "teste_preparo.c"
        fonte.write_text(DRIVER, encoding="utf-8")
        flags = ["gcc", "-Wall", "-Wextra", "-Werror", "-pthread"]
        subprocess.run(
            flags + ["-o", str(cls.programa)] +
            [str(RAIZ / nome) for nome in ("main.c", "pedido.c", "arquivo.c", "log.c")],
            check=True,
        )
        subprocess.run(
            flags + ["-I", str(RAIZ), "-o", str(cls.driver), str(fonte),
                     str(RAIZ / "pedido.c"),
                     "-Wl,--wrap=clock_gettime,--wrap=sleep,--wrap=registrarLog"],
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

    def test_preparo_real_um_e_dois_segundos_com_append(self):
        saida = self.executar("1\n1\nBatata\n1\n1\n2\nSuco\n2\n4\n1\n4\n2\n3\n1\n3\n2\n7\n9\n0\n")
        self.assertIn("Pedido 1 pronto!", saida)
        self.assertIn("Pedido 2 pronto!", saida)
        self.assertEqual(saida.count("Status: PRONTO"), 2)
        linhas = self.historico.read_text().splitlines()
        self.assertEqual(len(linhas), 2)
        for linha, id_pedido, minimo in zip(linhas, [1, 2], [1, 2]):
            self.assertIn(f"PEDIDO={id_pedido} | STATUS=PRONTO", linha)
            self.assertRegex(linha, r"PID=\d+")
            duracao = float(re.search(r"TEMPO=(\d+\.\d{3}) s", linha).group(1))
            self.assertGreaterEqual(duracao, minimo - 0.001)
        self.assertEqual(self.pedidos.read_text(), "1;Batata;1;1\n2;Suco;2;1\n")
        self.assertIn("Status: PRONTO", self.executar("10\n3\n1\n0\n"))

    def test_pedido_pronto_nao_repete_preparo_ou_log(self):
        saida = self.executar("1\n1\nBatata\n1\n4\n1\n4\n1\n0\n")
        self.assertIn("Pedido 1 ja esta pronto", saida)
        self.assertEqual(saida.count("Preparando pedido 1"), 1)
        self.assertEqual(len(self.historico.read_text().splitlines()), 1)

    def test_id_inexistente_e_entrada_invalida(self):
        saida = self.executar("4\n99\n4\nabc\n0\n")
        self.assertIn("Pedido com ID 99 nao encontrado", saida)
        self.assertIn("ID invalido", saida)
        self.assertFalse(self.historico.exists())

    def test_entrada_encerrada_durante_opcao_de_preparo(self):
        for entrada in ["4\n", "4\nabc", "4\n99"]:
            with self.subTest(entrada=entrada):
                self.executar(entrada)
                self.assertFalse(self.historico.exists())

    def test_cadastro_rejeita_tempos_fora_da_faixa(self):
        for tempo in [-1, 0, 3]:
            with self.subTest(tempo=tempo):
                saida = self.executar(f"1\n1\nBatata\n{tempo}\n2\n0\n")
                self.assertIn("tempo de preparo deve ser entre 1 e 2", saida)
                self.assertIn("Nenhum pedido cadastrado", saida)
                self.assertFalse(self.historico.exists())

    def test_tempo_invalido_em_txt_nao_executa(self):
        for tempo in [-1, 0, 3, 2147483647]:
            with self.subTest(tempo=tempo):
                conteudo = f"1;Pedido antigo;{tempo};0\n"
                self.pedidos.write_text(conteudo)
                saida = self.executar("10\n4\n1\n3\n1\n0\n")
                self.assertIn("tempo de preparo entre 1 e 2", saida)
                self.assertIn("Status: PENDENTE", saida)
                self.assertEqual(self.pedidos.read_text(), conteudo)
                self.assertFalse(self.historico.exists())

    def test_falha_de_log_mantem_pronto_e_permite_salvar(self):
        self.historico.mkdir()
        saida = self.executar("1\n1\nBatata\n1\n4\n1\n3\n1\n9\n0\n")
        self.assertIn("Pedido 1 pronto!", saida)
        self.assertIn("registro no historico nao foi confirmado", saida)
        self.assertIn("Status: PRONTO", saida)
        self.assertEqual(self.pedidos.read_text(), "1;Batata;1;1\n")

    def test_preparo_nao_salva_txt_automaticamente(self):
        self.pedidos.write_text("1;Batata;1;0\n")
        self.executar("10\n4\n1\n0\n")
        self.assertEqual(self.pedidos.read_text(), "1;Batata;1;0\n")
        self.assertIn("STATUS=PRONTO", self.historico.read_text())

    def test_falha_do_relogio_inicial_nao_inicia_preparo(self):
        saida = self.executar_driver("inicio")
        self.assertIn("RESULTADO=0 STATUS=0 RELOGIOS=1 ESPERAS=0 LOGS=0", saida)

    def test_falha_do_relogio_final_mantem_pronto_sem_log(self):
        saida = self.executar_driver("fim")
        self.assertIn("RESULTADO=1 STATUS=1 RELOGIOS=2 ESPERAS=1 LOGS=0", saida)
        self.assertIn("sem duracao medida e sem registro", saida)

    def test_interrupcao_retoma_sono_e_calcula_nanossegundos(self):
        saida = self.executar_driver("interrompido")
        self.assertIn("ESPERA=2\nESPERA=1\n", saida)
        self.assertIn("LOG=1;1;1.200", saida)
        self.assertIn("RESULTADO=1 STATUS=1 RELOGIOS=2 ESPERAS=2 LOGS=1", saida)

    def test_falha_do_logger_nao_desfaz_preparo(self):
        saida = self.executar_driver("log")
        self.assertIn("RESULTADO=1 STATUS=1 RELOGIOS=2 ESPERAS=1 LOGS=1", saida)
        self.assertIn("registro no historico nao foi confirmado", saida)


if __name__ == "__main__":
    unittest.main(verbosity=2)
