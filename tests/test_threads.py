"""Testes da fase 7. Rodar na raiz: python3 -B tests/test_threads.py"""

import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


RAIZ = Path(__file__).resolve().parents[1]

# Threads reais; barreira e falhas existem apenas no programa de teste.
DRIVER = r'''
#define _POSIX_C_SOURCE 200809L
#include <stdio.h>
#include <string.h>
#include <pthread.h>
#include <errno.h>
#include "thread.h"

int __real_pthread_create(pthread_t *, const pthread_attr_t *, void *(*)(void *), void *);
int __real_pthread_join(pthread_t, void **);

static const char *cenario;
/* Somente a thread principal altera estes contadores. */
static int criacoes, esperas;
static pthread_barrier_t barreira;

int __wrap_pthread_create(pthread_t *thread, const pthread_attr_t *attr,
                          void *(*funcao)(void *), void *arg) {
    criacoes++;
    if ((strcmp(cenario, "criacao1") == 0 && criacoes == 1) ||
        (strcmp(cenario, "criacao2") == 0 && criacoes == 2)) {
        return EAGAIN;
    }
    return __real_pthread_create(thread, attr, funcao, arg);
}

int __wrap_pthread_join(pthread_t thread, void **retorno) {
    esperas++;
    printf("JOIN=%d CRIACOES=%d\n", esperas, criacoes);
    int erro = __real_pthread_join(thread, retorno);
    if (erro == 0 && ((strcmp(cenario, "join1") == 0 && esperas == 1) ||
                      (strcmp(cenario, "join2") == 0 && esperas == 2))) {
        return EINVAL; /* thread real ja recolhida: nao vazar recursos no teste */
    }
    return erro;
}

int __wrap_prepararPedido(Pedido *pedido) {
    if (strcmp(cenario, "paralelo") == 0) {
        int erro = pthread_barrier_wait(&barreira);
        if (erro != 0 && erro != PTHREAD_BARRIER_SERIAL_THREAD) {
            return 0;
        }
    }
    if (strcmp(cenario, "preparo") == 0 && pedido->id == 2) {
        return 0;
    }
    pedido->status = PRONTO;
    return 1;
}

int main(int argc, char *argv[]) {
    if (argc != 2) {
        return 2;
    }
    cenario = argv[1];
    Pedido primeiro = {1, "Batata", 1, PENDENTE};
    Pedido segundo = {2, "Suco", 2, PENDENTE};
    Pedido *a = &primeiro, *b = &segundo;
    if (strcmp(cenario, "nulo") == 0) a = NULL;
    if (strcmp(cenario, "mesmo") == 0) b = a;
    if (strcmp(cenario, "idigual") == 0) segundo.id = primeiro.id;
    if (strcmp(cenario, "pronto") == 0) segundo.status = PRONTO;
    if (strcmp(cenario, "status") == 0) segundo.status = 99;
    if (strcmp(cenario, "tempo") == 0) segundo.tempoPreparo = 0;
    if (strcmp(cenario, "paralelo") == 0 && pthread_barrier_init(&barreira, NULL, 2) != 0) {
        return 2;
    }
    int resultado = prepararPedidosParalelo(a, b);
    if (strcmp(cenario, "paralelo") == 0 && pthread_barrier_destroy(&barreira) != 0) {
        return 2;
    }
    printf("RESULTADO=%d PRIMEIRO=%d SEGUNDO=%d CRIACOES=%d ESPERAS=%d\n",
           resultado, primeiro.status, segundo.status, criacoes, esperas);
    return 0;
}
'''

# Este wrapper permite verificar que o menu encerra se nao confirmar um join.
FALHA_JOIN = r'''
#include <stdio.h>
#include <pthread.h>
#include <errno.h>

int __real_pthread_join(pthread_t, void **);

int __wrap_pthread_join(pthread_t thread, void **retorno) {
    static int esperas;
    int erro = __real_pthread_join(thread, retorno);
    esperas++;
    printf("JOIN_TESTE=%d\n", esperas);
    return erro == 0 && esperas == 1 ? EINVAL : erro;
}
'''

# Exercita os retornos de sincronizacao sem alterar o logger entregue.
MUTEX_DRIVER = r'''
#include <stdio.h>
#include <string.h>
#include <pthread.h>
#include <errno.h>
#include "log.h"

int __real_pthread_mutex_lock(pthread_mutex_t *);
int __real_pthread_mutex_unlock(pthread_mutex_t *);
static const char *cenario;

int __wrap_pthread_mutex_lock(pthread_mutex_t *mutex) {
    if (strcmp(cenario, "lock") == 0) return EINVAL;
    return __real_pthread_mutex_lock(mutex);
}

int __wrap_pthread_mutex_unlock(pthread_mutex_t *mutex) {
    int erro = __real_pthread_mutex_unlock(mutex);
    if (erro == 0 && strcmp(cenario, "unlock") == 0) return EPERM;
    return erro;
}

int main(int argc, char *argv[]) {
    if (argc != 2) return 2;
    cenario = argv[1];
    int resultado = registrarLog(1, 1, 1.0);
    printf("RESULTADO=%d\n", resultado);
    return 0;
}
'''


class TestThreads(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if shutil.which("gcc") is None:
            raise unittest.SkipTest("gcc nao encontrado; execute no Codespaces/Linux com gcc")
        cls.compilacao = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.compilacao.cleanup)
        pasta = Path(cls.compilacao.name)
        cls.programa = pasta / "programa"
        cls.driver = pasta / "teste_threads"
        cls.menu_falha = pasta / "menu_falha_join"
        cls.mutex_driver = pasta / "teste_mutex"
        fonte = pasta / "teste_threads.c"
        fonte.write_text(DRIVER, encoding="utf-8")
        falha = pasta / "falha_join.c"
        falha.write_text(FALHA_JOIN, encoding="utf-8")
        mutex = pasta / "teste_mutex.c"
        mutex.write_text(MUTEX_DRIVER, encoding="utf-8")
        flags = ["gcc", "-Wall", "-Wextra", "-Werror", "-pthread"]
        fontes = [str(RAIZ / nome) for nome in
                  ("main.c", "pedido.c", "arquivo.c", "log.c", "processo.c", "thread.c")]
        subprocess.run(flags + ["-o", str(cls.programa)] + fontes, check=True)
        subprocess.run(
            flags + ["-I", str(RAIZ), "-o", str(cls.driver), str(fonte), str(RAIZ / "thread.c"),
                     "-Wl,--wrap=pthread_create,--wrap=pthread_join,--wrap=prepararPedido"],
            check=True,
        )
        subprocess.run(
            flags + ["-o", str(cls.menu_falha)] + fontes +
            [str(falha), "-Wl,--wrap=pthread_join"], check=True,
        )
        subprocess.run(
            flags + ["-I", str(RAIZ), "-o", str(cls.mutex_driver), str(mutex), str(RAIZ / "log.c"),
                     "-Wl,--wrap=pthread_mutex_lock,--wrap=pthread_mutex_unlock"], check=True,
        )

    def setUp(self):
        self.pasta = tempfile.TemporaryDirectory()
        self.addCleanup(self.pasta.cleanup)
        self.raiz = Path(self.pasta.name)
        (self.raiz / "dados").mkdir()
        self.pedidos = self.raiz / "dados" / "pedidos.txt"
        self.historico = self.raiz / "dados" / "historico.txt"

    def executar(self, entrada, programa=None, retorno=0):
        resultado = subprocess.run(
            [str(programa or self.programa)], input=entrada, cwd=self.raiz,
            capture_output=True, text=True, encoding="utf-8", timeout=15,
        )
        self.assertEqual(resultado.returncode, retorno, resultado.stdout + resultado.stderr)
        return resultado.stdout + resultado.stderr

    def executar_driver(self, cenario):
        resultado = subprocess.run(
            [str(self.driver), cenario], cwd=self.raiz,
            capture_output=True, text=True, encoding="utf-8", timeout=5,
        )
        self.assertEqual(resultado.returncode, 0, resultado.stdout + resultado.stderr)
        return resultado.stdout + resultado.stderr

    def carregar_par(self, tempo=1, status=0):
        self.pedidos.write_text(f"1;Batata;1;0\n2;Suco;{tempo};{status}\n")
        return "10\n"

    def test_dois_pedidos_logs_mesmo_pid_e_persistencia(self):
        self.historico.write_text("Historico anterior\n")
        entrada = "1\n1\nBatata\n1\n1\n2\nSuco\n2\n6\n1\n2\n3\n1\n3\n2\n9\n0\n"
        saida = self.executar(entrada)
        self.assertIn("Pedidos 1 e 2 prontos apos preparo com threads", saida)
        self.assertEqual(saida.count("Status: PRONTO"), 2)
        linhas = self.historico.read_text().splitlines()
        self.assertEqual(linhas[0], "Historico anterior")
        self.assertEqual(len(linhas), 3)
        registros = []
        for linha in linhas[1:]:
            registro = re.fullmatch(
                r"\d{2}/\d{2}/\d{4} \d{2}:\d{2}:\d{2} \| PID=(\d+) \| PEDIDO=([12])"
                r" \| STATUS=PRONTO \| TEMPO=\d+\.\d{3} s", linha,
            )
            self.assertIsNotNone(registro, linha)
            registros.append(registro.groups())
        self.assertEqual({item[1] for item in registros}, {"1", "2"})
        self.assertEqual(len({item[0] for item in registros}), 1)
        self.assertEqual(self.pedidos.read_text(), "1;Batata;1;1\n2;Suco;2;1\n")
        self.assertEqual(self.executar("10\n3\n1\n3\n2\n0\n").count("Status: PRONTO"), 2)

    def test_threads_nao_salvam_txt_automaticamente(self):
        entrada = self.carregar_par()
        antes = self.pedidos.read_bytes()
        self.executar(entrada + "6\n1\n2\n0\n")
        self.assertEqual(self.pedidos.read_bytes(), antes)
        self.assertEqual(len(self.historico.read_text().splitlines()), 2)

    def test_repeticao_nao_duplica_historico(self):
        entrada = self.carregar_par()
        saida = self.executar(entrada + "6\n1\n2\n6\n1\n2\n0\n")
        self.assertEqual(saida.count("prontos apos preparo com threads"), 1)
        self.assertIn("deve estar pendente", saida)
        self.assertEqual(len(self.historico.read_text().splitlines()), 2)

    def test_ids_iguais_ou_inexistentes_nao_iniciam_preparo(self):
        for par in ["1\n1\n", "1\n99\n", "99\n2\n"]:
            with self.subTest(par=par):
                entrada = self.carregar_par()
                saida = self.executar(entrada + "6\n" + par + "3\n1\n0\n")
                self.assertIn("Erro:", saida)
                self.assertIn("Status: PENDENTE", saida)
                self.assertNotIn("Preparando pedido", saida)
                self.assertFalse(self.historico.exists())

    def test_par_invalido_nao_prepara_nem_primeiro(self):
        for tempo, status in [(0, 0), (3, 0), (1, 1)]:
            with self.subTest(tempo=tempo, status=status):
                entrada = self.carregar_par(tempo, status)
                saida = self.executar(entrada + "6\n1\n2\n3\n1\n0\n")
                self.assertIn("deve estar pendente", saida)
                self.assertIn("Status: PENDENTE", saida)
                self.assertNotIn("Preparando pedido", saida)
                self.assertFalse(self.historico.exists())

    def test_entrada_textual_em_cada_id(self):
        for entrada in ["6\nabc\n0\n", "6\n1\nabc\n0\n"]:
            with self.subTest(entrada=entrada):
                saida = self.executar(entrada)
                self.assertIn("ID invalido", saida)
                self.assertNotIn("Preparando pedido", saida)

    def test_eof_antes_de_completar_par_nao_prepara(self):
        prefixo = self.carregar_par()
        for entrada in ["6\n", "6\nabc", "6\n1", "6\n1\n", "6\n1\nabc"]:
            with self.subTest(entrada=entrada):
                saida = self.executar(prefixo + entrada)
                self.assertNotIn("Preparando pedido", saida)
                self.assertFalse(self.historico.exists())

    def test_segundo_id_valido_sem_newline_conclui_e_sai(self):
        entrada = self.carregar_par()
        saida = self.executar(entrada + "6\n1\n2")
        self.assertIn("prontos apos preparo com threads", saida)
        self.assertEqual(len(self.historico.read_text().splitlines()), 2)

    def test_falha_historico_nao_prende_mutex_nem_desfaz_preparo(self):
        entrada = self.carregar_par()
        self.historico.mkdir()
        saida = self.executar(entrada + "6\n1\n2\n3\n1\n3\n2\n9\n0\n")
        self.assertEqual(saida.count("registro no historico nao foi confirmado"), 2)
        self.assertEqual(saida.count("Status: PRONTO"), 2)
        self.assertIn("prontos apos preparo com threads", saida)
        self.assertEqual(self.pedidos.read_text(), "1;Batata;1;1\n2;Suco;1;1\n")

    def test_processo_funciona_depois_das_threads(self):
        self.pedidos.write_text("1;Batata;1;0\n2;Suco;1;0\n3;Lanche;1;0\n")
        saida = self.executar("10\n6\n1\n2\n5\n3\n0\n")
        self.assertIn("prontos apos preparo com threads", saida)
        self.assertIn("Pipe: pedido 3 PRONTO, confirmado no processo pai", saida)
        linhas = self.historico.read_text().splitlines()
        self.assertEqual(len(linhas), 3)
        pids = [re.search(r"PID=(\d+)", linha).group(1) for linha in linhas]
        self.assertEqual(pids[0], pids[1])
        self.assertNotEqual(pids[1], pids[2])

    def test_barreira_comprova_sobreposicao_e_create_antes_join(self):
        saida = self.executar_driver("paralelo")
        self.assertIn("JOIN=1 CRIACOES=2", saida)
        self.assertIn("RESULTADO=1 PRIMEIRO=1 SEGUNDO=1 CRIACOES=2 ESPERAS=2", saida)

    def test_recusas_do_modulo_nao_criam_threads(self):
        for cenario in ["nulo", "mesmo", "idigual", "pronto", "status", "tempo"]:
            with self.subTest(cenario=cenario):
                saida = self.executar_driver(cenario)
                self.assertIn("RESULTADO=0 PRIMEIRO=0", saida)
                self.assertIn("CRIACOES=0 ESPERAS=0", saida)

    def test_falha_primeira_criacao_sem_join(self):
        saida = self.executar_driver("criacao1")
        self.assertIn("Erro ao criar thread", saida)
        self.assertIn("RESULTADO=0 PRIMEIRO=0 SEGUNDO=0 CRIACOES=1 ESPERAS=0", saida)

    def test_falha_segunda_criacao_aguarda_primeira(self):
        saida = self.executar_driver("criacao2")
        self.assertIn("Erro ao criar thread", saida)
        self.assertIn("RESULTADO=0 PRIMEIRO=1 SEGUNDO=0 CRIACOES=2 ESPERAS=1", saida)

    def test_falha_de_um_preparo_preserva_outro(self):
        saida = self.executar_driver("preparo")
        self.assertIn("RESULTADO=0 PRIMEIRO=1 SEGUNDO=0 CRIACOES=2 ESPERAS=2", saida)

    def test_join_falho_ainda_tenta_aguardar_demais(self):
        for cenario in ["join1", "join2"]:
            with self.subTest(cenario=cenario):
                saida = self.executar_driver(cenario)
                self.assertIn("Erro ao aguardar thread", saida)
                self.assertIn("RESULTADO=-1", saida)
                self.assertIn("ESPERAS=2", saida)
                self.assertNotIn("prontos apos preparo com threads", saida)

    def test_menu_encerra_com_erro_apos_join_nao_confirmado(self):
        entrada = self.carregar_par()
        saida = self.executar(entrada + "6\n1\n2\n5\n1\n0\n", self.menu_falha, retorno=1)
        self.assertIn("JOIN_TESTE=1", saida)
        self.assertIn("JOIN_TESTE=2", saida)
        self.assertIn("encerrando por seguranca", saida)
        self.assertEqual(saida.count("===== SISTEMA DE PEDIDOS DA LANCHONETE ====="), 2)
        self.assertNotIn("Caixa: PID", saida)

    def test_falhas_mutex_sao_reportadas(self):
        for cenario, retorno in [("lock", 0), ("unlock", 1)]:
            with self.subTest(cenario=cenario):
                resultado = subprocess.run(
                    [str(self.mutex_driver), cenario], cwd=self.raiz,
                    capture_output=True, text=True, encoding="utf-8", timeout=5,
                )
                self.assertEqual(resultado.returncode, retorno, resultado.stderr)
                if cenario == "lock":
                    self.assertIn("Erro ao bloquear historico", resultado.stderr)
                    self.assertIn("RESULTADO=0", resultado.stdout)
                    self.assertFalse(self.historico.exists())
                else:
                    self.assertIn("Erro ao liberar historico", resultado.stderr)
                    self.assertNotIn("RESULTADO=", resultado.stdout)
                    self.assertTrue(self.historico.exists())


if __name__ == "__main__":
    unittest.main(verbosity=2)
