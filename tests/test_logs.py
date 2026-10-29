"""Testes da fase 4. Rodar na raiz: python3 tests/test_logs.py"""

import re
import shutil
import subprocess
import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path


RAIZ = Path(__file__).resolve().parents[1]

# Este programa existe so nos testes; nao adiciona pedidos ficticios ao sistema.
DRIVER = r'''
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include "log.h"

int main(int argc, char *argv[]) {
    if (argc == 2) {
        return exibirHistorico() ? 0 : 1;
    }
    if (argc == 4) {
        printf("PID_TESTE=%ld\n", (long) getpid());
        return registrarLog(atoi(argv[1]), atoi(argv[2]), strtod(argv[3], NULL)) ? 0 : 1;
    }
    return 2;
}
'''


class TestLogs(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if shutil.which("gcc") is None:
            raise unittest.SkipTest("gcc nao encontrado; execute no Codespaces/Linux com gcc")
        cls.compilacao = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.compilacao.cleanup)
        pasta = Path(cls.compilacao.name)
        cls.programa = pasta / "programa"
        cls.driver = pasta / "teste_log"
        fonte = pasta / "teste_log.c"
        fonte.write_text(DRIVER, encoding="utf-8")
        flags = ["gcc", "-Wall", "-Wextra", "-Werror", "-pthread"]
        subprocess.run(
            flags + ["-o", str(cls.programa)] +
            [str(RAIZ / nome) for nome in ("main.c", "pedido.c", "arquivo.c", "log.c", "processo.c", "thread.c")],
            check=True,
        )
        subprocess.run(
            flags + ["-I", str(RAIZ), "-o", str(cls.driver), str(fonte), str(RAIZ / "log.c")],
            check=True,
        )

    def setUp(self):
        self.pasta = tempfile.TemporaryDirectory()
        self.addCleanup(self.pasta.cleanup)
        self.raiz = Path(self.pasta.name)
        (self.raiz / "dados").mkdir()
        self.historico = self.raiz / "dados" / "historico.txt"

    def executar_driver(self, *argumentos):
        return subprocess.run(
            [str(self.driver)] + [str(arg) for arg in argumentos],
            cwd=self.raiz, capture_output=True, text=True, encoding="utf-8", timeout=5,
        )

    def executar_menu(self, entrada):
        resultado = subprocess.run(
            [str(self.programa)], input=entrada, cwd=self.raiz,
            capture_output=True, text=True, encoding="utf-8", timeout=5,
        )
        self.assertEqual(resultado.returncode, 0, resultado.stderr)
        return resultado.stdout + resultado.stderr

    def test_registro_completo_append_data_hora_e_pid(self):
        antes = datetime.now() - timedelta(seconds=1)
        primeiro = self.executar_driver(3, 1, "2.001")
        self.assertEqual(primeiro.returncode, 0, primeiro.stderr)
        conteudo = self.historico.read_bytes()
        segundo = self.executar_driver(4, 0, "0.125")
        self.assertEqual(segundo.returncode, 0, segundo.stderr)
        self.assertTrue(self.historico.read_bytes().startswith(conteudo))
        linhas = self.historico.read_text(encoding="utf-8").splitlines()
        self.assertEqual(len(linhas), 2)
        depois = datetime.now() + timedelta(seconds=1)
        padrao = (r"(\d{2}/\d{2}/\d{4} \d{2}:\d{2}:\d{2}) \| PID=(\d+)"
                  r" \| PEDIDO=(-?\d+) \| STATUS=(PRONTO|PENDENTE) \| TEMPO=(\d+\.\d{3}) s")
        casos = [(primeiro, "3", "PRONTO", "2.001"),
                 (segundo, "4", "PENDENTE", "0.125")]
        for linha, (resultado, pedido, status, tempo) in zip(linhas, casos):
            registro = re.fullmatch(padrao, linha)
            self.assertIsNotNone(registro, linha)
            horario, pid, id_salvo, status_salvo, tempo_salvo = registro.groups()
            self.assertIn(f"PID_TESTE={pid}\n", resultado.stdout)
            self.assertEqual((id_salvo, status_salvo, tempo_salvo), (pedido, status, tempo))
            data = datetime.strptime(horario, "%d/%m/%Y %H:%M:%S")
            self.assertLessEqual(antes, data)
            self.assertLessEqual(data, depois)

    def test_duracao_zero_e_id_aceito_pelo_cadastro(self):
        resultado = self.executar_driver(-1, 1, 0)
        self.assertEqual(resultado.returncode, 0, resultado.stderr)
        self.assertIn("PEDIDO=-1 | STATUS=PRONTO | TEMPO=0.000 s",
                      self.historico.read_text())

    def test_parametros_invalidos_nao_criam_historico(self):
        for status, tempo in [(2, "1"), (1, "-0.5"), (1, "nan"), (1, "inf")]:
            with self.subTest(status=status, tempo=tempo):
                resultado = self.executar_driver(1, status, tempo)
                self.assertEqual(resultado.returncode, 1)
                self.assertIn("invalido para o historico", resultado.stdout)
                self.assertFalse(self.historico.exists())

    def test_parametros_invalidos_preservam_historico(self):
        conteudo = b"Historico anterior\n"
        self.historico.write_bytes(conteudo)
        for status, tempo in [(2, "1"), (1, "-1"), (1, "nan"), (1, "inf")]:
            with self.subTest(status=status, tempo=tempo):
                self.assertEqual(self.executar_driver(1, status, tempo).returncode, 1)
                self.assertEqual(self.historico.read_bytes(), conteudo)

    def test_consulta_inexistente_e_vazia(self):
        resultado = self.executar_driver("exibir")
        self.assertEqual(resultado.returncode, 0)
        self.assertIn("Nenhum historico registrado", resultado.stdout)
        self.assertFalse(self.historico.exists())
        self.historico.touch()
        resultado = self.executar_driver("exibir")
        self.assertEqual(resultado.returncode, 0)
        self.assertIn("Nenhum historico registrado", resultado.stdout)
        self.assertEqual(self.historico.read_bytes(), b"")

    def test_opcao_7_ausente_e_vazia(self):
        self.assertIn("Nenhum historico registrado", self.executar_menu("7\n0\n"))
        self.assertFalse(self.historico.exists())
        self.historico.touch()
        self.assertIn("Nenhum historico registrado", self.executar_menu("7\n0\n"))

    def test_consulta_exibe_sem_alterar_arquivo(self):
        texto = ("28/10/2026 14:30:00 | PID=123 | PEDIDO=3 | STATUS=PRONTO | TEMPO=2.001 s\n"
                 "Texto com 100% e %s e sem quebra final")
        conteudo = texto.encode("utf-8")
        self.historico.write_bytes(conteudo)
        resultado = self.executar_driver("exibir")
        self.assertEqual(resultado.returncode, 0)
        self.assertIn(texto, resultado.stdout)
        self.assertIn(texto, self.executar_menu("7\n0\n"))
        self.assertEqual(self.historico.read_bytes(), conteudo)

    def test_outras_operacoes_nao_geram_logs_de_execucao(self):
        entrada = "1\n1\nBatata\n1\n9\n10\n2\n3\n1\n8\n7\n0\n"
        saida = self.executar_menu(entrada)
        self.assertIn("[Medir desempenho] sera implementado", saida)
        self.assertFalse(self.historico.exists())
        self.historico.write_bytes(b"Historico anterior\n")
        self.executar_menu(entrada)
        self.assertEqual(self.historico.read_bytes(), b"Historico anterior\n")

    def test_erro_de_abertura_para_registrar(self):
        self.historico.mkdir()
        resultado = self.executar_driver(1, 1, 1)
        self.assertEqual(resultado.returncode, 1)
        self.assertIn("Erro ao abrir historico para registrar", resultado.stderr)

    def test_erro_na_leitura(self):
        self.historico.mkdir()
        resultado = self.executar_driver("exibir")
        self.assertEqual(resultado.returncode, 1)
        self.assertIn("Erro ao", resultado.stderr)
        self.assertNotIn("Nenhum historico registrado", resultado.stdout)

    @unittest.skipUnless(Path("/dev/full").exists(), "requer /dev/full no Linux")
    def test_erro_no_fechamento_da_escrita(self):
        self.historico.symlink_to("/dev/full")
        resultado = self.executar_driver(1, 1, 1)
        self.assertEqual(resultado.returncode, 1)
        self.assertIn("Erro ao fechar historico", resultado.stderr)


if __name__ == "__main__":
    unittest.main(verbosity=2)
