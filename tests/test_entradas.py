"""Testes da fase 9. Rodar na raiz: python3 -B tests/test_entradas.py"""

import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


RAIZ = Path(__file__).resolve().parents[1]
MENU = "===== SISTEMA DE PEDIDOS DA LANCHONETE ====="
INVALIDOS = ["abc", "1abc", "1.5", "1 2", "", " \t ", "+", "0x1",
             "2147483648", "-2147483649", "9" * 1000]

# Falhas de leitura controladas somente nesta compilacao de teste.
DRIVER = r'''
#include <stdio.h>
#include <stdlib.h>
#include <errno.h>

int __real_getchar(void);
int __real_ferror(FILE *fluxo);
static int lidos, falhou;

int __wrap_getchar(void) {
    const char *limite = getenv("FALHAR_APOS");
    if (limite != NULL && lidos == atoi(limite)) {
        falhou = 1;
        errno = EIO;
        return EOF;
    }
    int caractere = __real_getchar();
    if (caractere != EOF) lidos++;
    return caractere;
}

int __wrap_ferror(FILE *fluxo) {
    if (fluxo == stdin && falhou) return 1;
    return __real_ferror(fluxo);
}
'''


class TestEntradas(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if shutil.which("gcc") is None:
            raise unittest.SkipTest("gcc nao encontrado; execute no Codespaces/Linux com gcc")
        cls.compilacao = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.compilacao.cleanup)
        pasta = Path(cls.compilacao.name)
        cls.programa = pasta / "programa"
        cls.controlado = pasta / "teste_entrada"
        fonte = pasta / "teste_entrada.c"
        fonte.write_text(DRIVER, encoding="utf-8")
        flags = ["gcc", "-Wall", "-Wextra", "-Werror", "-pthread"]
        fontes = [str(RAIZ / nome) for nome in
                  ("main.c", "pedido.c", "arquivo.c", "log.c", "processo.c", "thread.c")]
        subprocess.run(flags + ["-o", str(cls.programa)] + fontes, check=True)
        subprocess.run(
            flags + ["-o", str(cls.controlado)] + fontes +
            [str(fonte), "-Wl,--wrap=getchar,--wrap=ferror"], check=True,
        )

    def setUp(self):
        self.pasta = tempfile.TemporaryDirectory()
        self.addCleanup(self.pasta.cleanup)
        self.raiz = Path(self.pasta.name)
        (self.raiz / "dados").mkdir()
        self.pedidos = self.raiz / "dados" / "pedidos.txt"
        self.historico = self.raiz / "dados" / "historico.txt"

    def executar(self, entrada, falhar_apos=None):
        ambiente = os.environ.copy()
        if falhar_apos is not None:
            ambiente["FALHAR_APOS"] = str(falhar_apos)
        resultado = subprocess.run(
            [str(self.controlado if falhar_apos is not None else self.programa)],
            input=entrada.encode("utf-8") if isinstance(entrada, str) else entrada,
            cwd=self.raiz, env=ambiente, capture_output=True, timeout=8,
        )
        saida = (resultado.stdout + resultado.stderr).decode("utf-8", errors="replace")
        if falhar_apos is None:
            self.assertEqual(resultado.returncode, 0, saida)
        else:
            self.assertNotEqual(resultado.returncode, 0, saida)
            self.assertIn("Erro ao ler entrada", saida)
        return saida

    def carregar_par(self):
        self.pedidos.write_bytes(b"1;Batata;1;0\n2;Suco;1;0\n")
        return "10\n"

    def test_eof_vazio_e_em_cada_campo_do_cadastro(self):
        for entrada in ["", "1", "1\n", "1\n7", "1\n7\n", "1\n7\nBatata",
                        "1\n7\nBatata\n"]:
            with self.subTest(entrada=entrada):
                saida = self.executar(entrada)
                self.assertNotIn("Pedido cadastrado com sucesso", saida)
                self.assertNotIn("Entrada invalida", saida)
                self.assertEqual(saida.count(MENU), 1)
                self.assertFalse(self.pedidos.exists())
                self.assertFalse(self.historico.exists())

    def test_eof_antes_dos_ids_nao_executa_operacoes(self):
        inicio = self.carregar_par()
        antes = self.pedidos.read_bytes()
        for final in ["3\n", "4\n", "5\n", "6\n", "6\n1", "6\n1\n", "8\n"]:
            with self.subTest(final=final):
                saida = self.executar(inicio + final)
                self.assertNotIn("Preparando pedido", saida)
                self.assertNotIn("Estacao de preparo: PID filho=", saida)
                self.assertNotIn("DESEMPENHO DA CONSULTA", saida)
                self.assertEqual(saida.count(MENU), 2)
                self.assertEqual(self.pedidos.read_bytes(), antes)
                self.assertFalse(self.historico.exists())

    def test_menu_rejeita_numero_parcial_overflow_e_linha_vazia(self):
        for valor in INVALIDOS + ["2\x00resto", "2\rresto"]:
            with self.subTest(valor=valor[:30]):
                saida = self.executar(valor + "\n2\n0\n")
                self.assertEqual(saida.count("Entrada invalida"), 1)
                self.assertIn("Nenhum pedido cadastrado", saida)
                self.assertIn("Saindo do sistema", saida)
                self.assertEqual(saida.count(MENU), 3)

    def test_todos_os_ids_rejeitam_valores_invalidos_sem_reaproveitar_linha(self):
        inicio = self.carregar_par()
        for opcao in [1, 3, 4, 5, 6, 8]:
            for valor in INVALIDOS + ["1\x00resto"]:
                with self.subTest(opcao=opcao, valor=valor[:30]):
                    saida = self.executar(inicio + f"{opcao}\n{valor}\n3\n2\n0\n")
                    self.assertIn("ID invalido", saida)
                    self.assertIn("Descricao: Suco", saida)
                    self.assertNotIn("Pedido cadastrado com sucesso", saida)
                    self.assertNotIn("Preparando pedido", saida)
                    self.assertNotIn("DESEMPENHO DA CONSULTA", saida)
                    self.assertFalse(self.historico.exists())

    def test_segundo_id_invalido_nao_inicia_threads(self):
        inicio = self.carregar_par()
        for valor in INVALIDOS:
            with self.subTest(valor=valor[:30]):
                saida = self.executar(inicio + f"6\n1\n{valor}\n3\n1\n0\n")
                self.assertIn("ID invalido", saida)
                self.assertIn("Status: PENDENTE", saida)
                self.assertNotIn("Preparando pedido", saida)
                self.assertFalse(self.historico.exists())

    def test_tempo_rejeita_valores_invalidos_sem_cadastrar(self):
        for valor in INVALIDOS + ["1\x00resto"]:
            with self.subTest(valor=valor[:30]):
                saida = self.executar(f"1\n7\nBatata\n{valor}\n2\n0\n")
                self.assertIn("Tempo invalido", saida)
                self.assertIn("Nenhum pedido cadastrado", saida)
                self.assertNotIn("Pedido cadastrado com sucesso", saida)

    def test_tempo_fora_da_faixa_continua_recusado(self):
        for valor in [-2147483648, -1, 0, 3, 2147483647]:
            with self.subTest(valor=valor):
                saida = self.executar(f"1\n7\nBatata\n{valor}\n2\n0\n")
                self.assertIn("tempo de preparo deve ser entre 1 e 2", saida)
                self.assertNotIn("Pedido cadastrado com sucesso", saida)

    def test_inteiros_limites_zero_negativo_e_espacos(self):
        entrada = " \t+1 \t\n -2147483648 \nMinimo\n +1 \t\n"
        entrada += "1\n2147483647\nMaximo\n2\n1\n0\nZero\n1\n1\n-1\nNegativo\n1\n"
        entrada += "3\n-2147483648\n3\n2147483647\n3\n0\n3\n-1\n9\n0\n"
        saida = self.executar(entrada)
        self.assertEqual(saida.count("Pedido cadastrado com sucesso"), 4)
        for id_pedido in [-2147483648, 2147483647, 0, -1]:
            self.assertIn(f"ID: {id_pedido}\n", saida)
        self.assertEqual(self.pedidos.read_bytes(),
                         b"-2147483648;Minimo;1;0\n2147483647;Maximo;2;0\n"
                         b"0;Zero;1;0\n-1;Negativo;1;0\n")

    def test_linhas_numericas_longas_consumidas_por_inteiro(self):
        for valor in ["2" + " " * 400, " " * 1000, "9" * 10000]:
            with self.subTest(tamanho=len(valor)):
                saida = self.executar(valor + "\n1\n7\nBatata\n1\n9\n0\n")
                self.assertEqual(saida.count("Entrada invalida"), 1)
                self.assertEqual(saida.count("Pedido cadastrado com sucesso"), 1)
                self.assertEqual(self.pedidos.read_bytes(), b"7;Batata;1;0\n")

    def test_invalidos_seguidos_de_eof_nao_repetem_menu(self):
        for entrada in ["abc", "9" * 10000, "1\n1abc", "1\n7\nBatata\n1abc",
                        "3\n1abc", "4\n1abc", "5\n1abc", "6\n1abc",
                        "6\n1\n2abc", "8\n1abc", "1\n7\n" + "a" * 10000]:
            with self.subTest(entrada=entrada[:30]):
                saida = self.executar(entrada)
                self.assertEqual(saida.count(MENU), 1)
                self.assertNotIn("Pedido cadastrado com sucesso", saida)
                self.assertFalse(self.historico.exists())

    def test_descricoes_validas_vazia_limites_utf8_e_crlf(self):
        for descricao in ["", "a" * 98, "a" * 99, "á" * 49 + "a"]:
            for fim in ["\n", "\r\n"]:
                with self.subTest(bytes=len(descricao.encode("utf-8")), fim=repr(fim)):
                    entrada = fim.join(["1", "7", descricao, "1", "9", "0", ""])
                    saida = self.executar(entrada)
                    self.assertIn("Pedido cadastrado com sucesso", saida)
                    self.assertEqual(self.pedidos.read_bytes(),
                                     f"7;{descricao};1;0\n".encode("utf-8"))

    def test_descricoes_invalidas_nao_sao_truncadas_ou_reaproveitadas(self):
        for descricao in ["a" * 100, "a" * 10000, "á" * 50, "Batata;suco",
                          "Batata\rsuco", "Batata\x00suco", "\x00", "\rBatata"]:
            for fim in ["\n", "\r\n"]:
                with self.subTest(descricao=descricao[:30], fim=repr(fim)):
                    saida = self.executar(f"1\n7\n{descricao}{fim}2\n9\n0\n")
                    self.assertIn("Erro: descricao", saida)
                    self.assertIn("Nenhum pedido cadastrado", saida)
                    self.assertNotIn("Pedido cadastrado com sucesso", saida)
                    self.assertEqual(self.pedidos.read_bytes(), b"")

    def test_cr_interno_nao_e_removido_como_terminacao(self):
        for entrada in ["2\rresto\n0\n", "2\r\r\n0\n", "2\r"]:
            with self.subTest(entrada=entrada):
                saida = self.executar(entrada)
                self.assertIn("Entrada invalida", saida)
                self.assertNotIn("Nenhum pedido cadastrado", saida)

    def test_cadastro_com_ultimo_campo_sem_newline_conclui_sem_menu_extra(self):
        saida = self.executar("1\n7\nBatata\n1")
        self.assertIn("Pedido cadastrado com sucesso", saida)
        self.assertEqual(saida.count(MENU), 1)
        self.assertFalse(self.pedidos.exists())

    def test_consulta_com_id_final_sem_newline(self):
        saida = self.executar(self.carregar_par() + "3\n1")
        self.assertIn("Descricao: Batata", saida)
        self.assertEqual(saida.count(MENU), 2)

    def test_menu_final_sem_newline_executa_opcao(self):
        saida = self.executar("1\n7\nBatata\n1\n9")
        self.assertIn("1 pedido(s) salvo(s)", saida)
        self.assertEqual(self.pedidos.read_bytes(), b"7;Batata;1;0\n")
        self.assertEqual(saida.count(MENU), 2)
        self.assertIn("Saindo do sistema", self.executar("0"))

    def test_preparo_sequencial_e_processo_com_id_final_sem_newline(self):
        for opcao in [4, 5]:
            with self.subTest(opcao=opcao):
                self.historico.unlink(missing_ok=True)
                saida = self.executar(self.carregar_par() + f"{opcao}\n1")
                self.assertIn("Preparando pedido 1", saida)
                self.assertEqual(saida.count(MENU), 2)
                self.assertEqual(len(self.historico.read_bytes().splitlines()), 1)
                if opcao == 5:
                    self.assertIn("confirmado no processo pai", saida)
                self.assertEqual(self.pedidos.read_bytes(), b"1;Batata;1;0\n2;Suco;1;0\n")

    def test_par_de_threads_com_ultimo_id_sem_newline(self):
        saida = self.executar(self.carregar_par() + "6\n1\n2")
        self.assertIn("prontos apos preparo com threads", saida)
        self.assertEqual(saida.count(MENU), 2)
        self.assertEqual(len(self.historico.read_bytes().splitlines()), 2)

    def test_desempenho_com_id_final_sem_newline(self):
        saida = self.executar(self.carregar_par() + "8\n1")
        self.assertIn("DESEMPENHO DA CONSULTA", saida)
        self.assertIn("Media:", saida)
        self.assertEqual(saida.count(MENU), 2)
        self.assertFalse(self.historico.exists())

    @unittest.skipUnless(sys.platform == "linux", "requer descritor POSIX no Linux")
    def test_erro_real_com_stdin_fechado_encerra_com_falha(self):
        resultado = subprocess.run(
            [str(self.programa)], stdin=subprocess.DEVNULL, cwd=self.raiz,
            preexec_fn=lambda: os.close(0), capture_output=True, timeout=5,
        )
        self.assertNotEqual(resultado.returncode, 0)
        self.assertIn(b"Erro ao ler entrada", resultado.stderr)

    def test_erro_durante_leitura_ou_descarte_nao_usa_dados_parciais(self):
        casos = [("2\n", 0), ("2\n", 1), ("x" * 1000 + "\n", 500),
                 ("1\n7\nBatata\n1\n", 5),
                 ("1\n7\n" + "a" * 1000 + "\n", 500),
                 ("1\n7\nBatata\n1\n", 12)]
        for entrada, limite in casos:
            with self.subTest(limite=limite, entrada=entrada[:30]):
                saida = self.executar(entrada, falhar_apos=limite)
                self.assertNotIn("Pedido cadastrado com sucesso", saida)
                self.assertNotIn("Nenhum pedido cadastrado", saida)
                self.assertEqual(saida.count(MENU), 1)
                self.assertFalse(self.pedidos.exists())


if __name__ == "__main__":
    unittest.main(verbosity=2)
