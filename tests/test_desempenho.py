"""Testes da fase 8. Rodar na raiz: python3 -B tests/test_desempenho.py"""

import os
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


RAIZ = Path(__file__).resolve().parents[1]

# Relogio e consulta controlados somente neste teste, sem hooks no programa real.
DRIVER = r'''
#define _POSIX_C_SOURCE 200809L
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <errno.h>
#include "pedido.h"

int __real_consultarPedido(Pedido pedidos[], int total, int id);
static int relogios, consultas;

int __wrap_consultarPedido(Pedido pedidos[], int total, int id) {
    consultas++;
    printf("CONSULTA_TESTE=%d\n", consultas);
    const char *cenario = getenv("CENARIO_DESEMPENHO");
    if (cenario != NULL && strcmp(cenario, "consulta") == 0 && consultas == 3) {
        return -1;
    }
    return __real_consultarPedido(pedidos, total, id);
}

int __wrap_clock_gettime(clockid_t relogio, struct timespec *valor) {
    relogios++;
    printf("RELOGIO_TESTE=%d\n", relogios);
    const char *cenario = getenv("CENARIO_DESEMPENHO");
    if (cenario == NULL) cenario = "normal";
    if (relogio != CLOCK_MONOTONIC ||
        (strncmp(cenario, "falha", 5) == 0 && relogios == atoi(cenario + 5))) {
        errno = EIO;
        return -1;
    }
    int repeticao = (relogios - 1) / 2;
    int final = relogios % 2 == 0;
    valor->tv_sec = 10 + repeticao;
    valor->tv_nsec = 100000000L;
    if (strcmp(cenario, "virada") == 0) {
        valor->tv_nsec = 999500000L;
        if (final) {
            valor->tv_sec++;
            valor->tv_nsec = (repeticao + 1) * 1000000L - 500000L;
        }
    } else if (final && strcmp(cenario, "zero") != 0) {
        valor->tv_nsec += strcmp(cenario, "negativo") == 0 ? -1L : (repeticao + 1) * 1000000L;
    }
    return 0;
}
'''


class TestDesempenho(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if shutil.which("gcc") is None:
            raise unittest.SkipTest("gcc nao encontrado; execute no Codespaces/Linux com gcc")
        cls.compilacao = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.compilacao.cleanup)
        pasta = Path(cls.compilacao.name)
        cls.programa = pasta / "programa"
        cls.controlado = pasta / "teste_desempenho"
        fonte = pasta / "teste_desempenho.c"
        fonte.write_text(DRIVER, encoding="utf-8")
        flags = ["gcc", "-Wall", "-Wextra", "-Werror", "-pthread"]
        fontes = [str(RAIZ / nome) for nome in
                  ("main.c", "pedido.c", "arquivo.c", "log.c", "processo.c", "thread.c")]
        subprocess.run(flags + ["-o", str(cls.programa)] + fontes, check=True)
        subprocess.run(
            flags + ["-I", str(RAIZ), "-o", str(cls.controlado)] + fontes +
            [str(fonte), "-Wl,--wrap=clock_gettime,--wrap=consultarPedido"], check=True,
        )

    def setUp(self):
        self.pasta = tempfile.TemporaryDirectory()
        self.addCleanup(self.pasta.cleanup)
        self.raiz = Path(self.pasta.name)
        (self.raiz / "dados").mkdir()
        self.pedidos = self.raiz / "dados" / "pedidos.txt"
        self.historico = self.raiz / "dados" / "historico.txt"

    def executar(self, entrada, cenario=None):
        ambiente = os.environ.copy()
        if cenario is not None:
            ambiente["CENARIO_DESEMPENHO"] = cenario
        resultado = subprocess.run(
            [str(self.controlado if cenario is not None else self.programa)],
            input=entrada, cwd=self.raiz, env=ambiente,
            capture_output=True, text=True, encoding="utf-8", timeout=5,
        )
        self.assertEqual(resultado.returncode, 0, resultado.stdout + resultado.stderr)
        return resultado.stdout + resultado.stderr

    def carregar(self, status=0, tempo=1):
        self.pedidos.write_text(f"1;Batata;{tempo};{status}\n2;Suco;2;0\n")
        return "10\n"

    def conferir_resumo(self, saida):
        linhas = re.findall(r"^Execucao (\d+): (\d+\.\d{6}) ms$", saida, re.MULTILINE)
        self.assertEqual([numero for numero, _ in linhas], ["1", "2", "3", "4", "5"], saida)
        tempos = [float(tempo) for _, tempo in linhas]
        resumo = {}
        for nome in ["Menor", "Maior", "Media"]:
            resultado = re.search(rf"^{nome}: (\d+\.\d{{6}}) ms$", saida, re.MULTILINE)
            self.assertIsNotNone(resultado, saida)
            resumo[nome] = float(resultado.group(1))
        self.assertEqual(resumo["Menor"], min(tempos))
        self.assertEqual(resumo["Maior"], max(tempos))
        self.assertLessEqual(resumo["Menor"], resumo["Media"])
        self.assertLessEqual(resumo["Media"], resumo["Maior"])
        self.assertAlmostEqual(resumo["Media"], sum(tempos) / 5, delta=0.000001)
        return tempos, resumo

    def test_medicao_real_cinco_consultas_e_analise(self):
        entrada = self.carregar()
        saida = self.executar(entrada + "8\n2\n0\n")
        self.conferir_resumo(saida)
        self.assertIn("ID: 2 | Pedidos no vetor: 2 | Repeticoes: 5", saida)
        self.assertIn("nao garantem estabilidade estatistica", saida)
        self.assertIn("seis casas decimais nao garantem essa precisao", saida)
        self.assertFalse(self.historico.exists())

    def test_calculo_deterministico_e_quantidade_de_chamadas(self):
        entrada = self.carregar()
        saida = self.executar(entrada + "8\n1\n0\n", "normal")
        tempos, resumo = self.conferir_resumo(saida)
        self.assertEqual(tempos, [1, 2, 3, 4, 5])
        self.assertEqual(resumo, {"Menor": 1, "Maior": 5, "Media": 3})
        self.assertEqual(re.findall(r"RELOGIO_TESTE=(\d+)", saida), [str(i) for i in range(1, 11)])
        # Uma validacao previa e cinco consultas medidas, sem pesquisa extra no menu.
        self.assertEqual(re.findall(r"CONSULTA_TESTE=(\d+)", saida), [str(i) for i in range(1, 7)])

    def test_diferenca_de_nanossegundos_na_virada_do_segundo(self):
        entrada = self.carregar()
        tempos, resumo = self.conferir_resumo(self.executar(entrada + "8\n1\n0\n", "virada"))
        self.assertEqual(tempos, [1, 2, 3, 4, 5])
        self.assertEqual(resumo["Media"], 3)

    def test_tempos_zero_sao_aceitos(self):
        entrada = self.carregar()
        tempos, resumo = self.conferir_resumo(self.executar(entrada + "8\n1\n0\n", "zero"))
        self.assertEqual(tempos, [0] * 5)
        self.assertEqual(resumo, {"Menor": 0, "Maior": 0, "Media": 0})

    def test_falhas_de_relogio_nao_exibem_estatisticas_parciais(self):
        for chamada in [1, 2, 7, 10]:
            with self.subTest(chamada=chamada):
                entrada = self.carregar()
                saida = self.executar(entrada + "8\n1\n0\n", f"falha{chamada}")
                self.assertIn("Erro ao", saida)
                self.assertIn("Medicao incompleta", saida)
                self.assertNotIn("DESEMPENHO DA CONSULTA", saida)
                self.assertNotIn("Execucao 1:", saida)
                self.assertNotIn("Media:", saida)
                self.assertEqual(len(re.findall(r"RELOGIO_TESTE=", saida)), chamada)
                self.assertFalse(self.historico.exists())

    def test_intervalo_negativo_recusado(self):
        entrada = self.carregar()
        saida = self.executar(entrada + "8\n1\n0\n", "negativo")
        self.assertIn("intervalo de tempo negativo", saida)
        self.assertNotIn("Media:", saida)

    def test_resultado_inesperado_da_consulta_cancela_medicao(self):
        entrada = self.carregar()
        saida = self.executar(entrada + "8\n1\n0\n", "consulta")
        self.assertIn("resultado da consulta mudou", saida)
        self.assertIn("Medicao incompleta", saida)
        self.assertNotIn("Media:", saida)

    def test_lista_vazia_e_id_inexistente_sem_relogio(self):
        for entrada in ["8\n99\n0\n", self.carregar() + "8\n99\n0\n"]:
            with self.subTest(entrada=entrada):
                saida = self.executar(entrada, "normal")
                self.assertIn("Pedido com ID 99 nao encontrado", saida)
                self.assertNotIn("RELOGIO_TESTE=", saida)
                self.assertNotIn("Media:", saida)

    def test_pendente_pronto_e_tempo_legado_sem_mutacao(self):
        for status, tempo in [(0, 1), (1, 2), (0, -5)]:
            with self.subTest(status=status, tempo=tempo):
                entrada = self.carregar(status, tempo)
                antes = self.pedidos.read_bytes()
                saida = self.executar(entrada + "8\n1\n3\n1\n9\n0\n")
                self.conferir_resumo(saida)
                self.assertIn("Status: " + ("PRONTO" if status else "PENDENTE"), saida)
                self.assertEqual(self.pedidos.read_bytes(), antes)
                self.assertFalse(self.historico.exists())
                reaberto = self.executar("10\n3\n1\n0\n")
                self.assertIn(f"Tempo de preparo: {tempo}s", reaberto)

    def test_medicao_nao_salva_nem_altera_historico(self):
        entrada = self.carregar()
        antes = self.pedidos.read_bytes()
        historico = b"Historico anterior\n"
        self.historico.write_bytes(historico)
        self.conferir_resumo(self.executar(entrada + "8\n1\n0\n"))
        self.assertEqual(self.pedidos.read_bytes(), antes)
        self.assertEqual(self.historico.read_bytes(), historico)

    def test_entrada_invalida_e_eof(self):
        for entrada in ["8\nabc\n0\n", "8\n", "8\nabc"]:
            with self.subTest(entrada=entrada):
                saida = self.executar(entrada)
                if "abc" in entrada:
                    self.assertIn("ID invalido", saida)
                self.assertNotIn("Media:", saida)
                self.assertFalse(self.historico.exists())

    def test_id_valido_sem_newline_mede_e_encerra(self):
        entrada = self.carregar()
        saida = self.executar(entrada + "8\n1")
        self.conferir_resumo(saida)
        self.assertEqual(saida.count("===== SISTEMA DE PEDIDOS DA LANCHONETE ====="), 2)


if __name__ == "__main__":
    unittest.main(verbosity=2)
