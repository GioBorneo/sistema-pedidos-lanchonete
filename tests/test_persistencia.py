"""Testes da fase 3. Rodar na raiz: python3 tests/test_persistencia.py"""

import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


RAIZ = Path(__file__).resolve().parents[1]


class TestPersistencia(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if shutil.which("gcc") is None:
            raise unittest.SkipTest("gcc nao encontrado; execute no Codespaces/Linux com gcc")
        cls.compilacao = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.compilacao.cleanup)
        cls.programa = Path(cls.compilacao.name) / "programa"
        subprocess.run(
            ["gcc", "-Wall", "-Wextra", "-Werror", "-pthread", "-o", str(cls.programa),
             str(RAIZ / "main.c"), str(RAIZ / "pedido.c"), str(RAIZ / "arquivo.c")],
            check=True,
        )

    def setUp(self):
        self.pasta = tempfile.TemporaryDirectory()
        self.addCleanup(self.pasta.cleanup)
        self.raiz = Path(self.pasta.name)
        (self.raiz / "dados").mkdir()
        self.arquivo = self.raiz / "dados" / "pedidos.txt"

    def executar(self, entrada):
        # Cada chamada abre uma sessao nova; o zero evita depender de EOF no menu.
        resultado = subprocess.run(
            [str(self.programa)], input=entrada, cwd=self.raiz,
            capture_output=True, text=True, encoding="utf-8", timeout=5,
        )
        self.assertEqual(resultado.returncode, 0, resultado.stderr)
        return resultado.stdout + resultado.stderr

    def gravar(self, texto):
        self.arquivo.write_bytes(texto.encode("utf-8"))

    def test_salvar_fechar_e_carregar(self):
        saida = self.executar("1\n1\nX-burger e suco\n2\n1\n2\nPorção de batata\n1\n9\n0\n")
        self.assertIn("2 pedido(s) salvo(s)", saida)
        self.assertEqual(self.arquivo.read_text(encoding="utf-8"),
                         "1;X-burger e suco;2;0\n2;Porção de batata;1;0\n")
        saida = self.executar("10\n2\n3\n2\n0\n")
        self.assertIn("2 pedido(s) carregado(s)", saida)
        self.assertIn("Descricao: Porção de batata", saida)
        self.assertIn("X-burger e suco", saida)

    def test_carregar_substitui_lista_e_preserva_status(self):
        self.gravar("1;Batata;2;1\n")
        saida = self.executar("1\n99\nPedido atual\n1\n10\n3\n99\n3\n1\n9\n0\n")
        self.assertIn("Pedido com ID 99 nao encontrado", saida)
        self.assertIn("Status: PRONTO", saida)
        self.assertEqual(self.arquivo.read_text(), "1;Batata;2;1\n")

    def test_arquivo_inexistente_preserva_lista(self):
        saida = self.executar("1\n99\nPedido atual\n1\n10\n3\n99\n0\n")
        self.assertIn("Erro ao abrir arquivo para carregar", saida)
        self.assertIn("Descricao: Pedido atual", saida)
        self.assertNotIn("pedido(s) carregado(s)", saida)

    def test_arquivo_invalido_preserva_lista(self):
        casos = [
            "2;Parcial;1;0\nlinha invalida\n",
            "2;Batata;1\n", "2;Batata;1;0;extra\n",
            "2;Batata;1;3\n", "2x;Batata;1;0\n",
            "2;Batata;;0\n", ";Batata;1;0\n",
            "9999999999999999999999;Batata;1;0\n",
            "2;Batata;9999999999999999999999;0\n",
            "2;Batata;1;0\n2;Duplicado;2;1\n",
            "2;" + "a" * 100 + ";1;0\n",
            "2;" + "a" * 300 + ";1;0\n", "\n",
        ]
        for texto in casos:
            with self.subTest(texto=texto[:80]):
                self.gravar(texto)
                saida = self.executar("1\n99\nPedido atual\n1\n10\n3\n99\n0\n")
                self.assertIn("Os pedidos atuais foram mantidos", saida)
                self.assertIn("Descricao: Pedido atual", saida)
                self.assertNotIn("pedido(s) carregado(s)", saida)

    def test_limite_de_pedidos(self):
        linhas = "".join(f"{i};Pedido {i};1;0\n" for i in range(50))
        self.gravar(linhas)
        self.assertIn("50 pedido(s) carregado(s)", self.executar("10\n0\n"))
        self.gravar(linhas + "50;Pedido extra;1;0\n")
        saida = self.executar("1\n99\nPedido atual\n1\n10\n3\n99\n0\n")
        self.assertIn("excede o limite de 50 pedidos", saida)
        self.assertIn("Descricao: Pedido atual", saida)

    def test_vazio_substitui_lista_por_zero_pedidos(self):
        self.gravar("")
        saida = self.executar("1\n99\nPedido atual\n1\n10\n2\n0\n")
        self.assertIn("0 pedido(s) carregado(s)", saida)
        self.assertIn("Nenhum pedido cadastrado", saida)

    def test_crlf_sem_quebra_final_e_descricao_vazia(self):
        self.gravar("1;;2;0\r\n2;Suco de limão;1;1")
        saida = self.executar("10\n9\n0\n")
        self.assertIn("2 pedido(s) carregado(s)", saida)
        self.assertEqual(self.arquivo.read_text(encoding="utf-8"),
                         "1;;2;0\n2;Suco de limão;1;1\n")

    def test_descricao_no_limite_de_99_bytes(self):
        descricao = "a" * 99
        saida = self.executar(f"1\n1\n{descricao}\n1\n9\n0\n")
        self.assertIn("Pedido cadastrado com sucesso", saida)
        saida = self.executar("10\n9\n0\n")
        self.assertIn("1 pedido(s) carregado(s)", saida)
        self.assertEqual(self.arquivo.read_text(), f"1;{descricao};1;0\n")

    def test_cadastro_rejeita_descricao_longa_e_separador(self):
        for descricao in ["Batata;suco", "a" * 100]:
            with self.subTest(descricao=descricao):
                saida = self.executar(f"1\n1\n{descricao}\n2\n0\n")
                self.assertIn("Erro: descricao", saida)
                self.assertIn("Nenhum pedido cadastrado", saida)

    def test_salvar_sobrescreve_inclusive_lista_vazia(self):
        self.gravar("1;Pedido antigo;1;1\n2;Outro pedido;2;0\n")
        self.executar("1\n3\nNovo\n1\n9\n0\n")
        self.assertEqual(self.arquivo.read_text(), "3;Novo;1;0\n")
        self.executar("9\n0\n")
        self.assertEqual(self.arquivo.read_bytes(), b"")

    def test_erro_ao_salvar_nao_informa_sucesso(self):
        self.arquivo.mkdir()  # fopen nao pode gravar sobre um diretorio.
        saida = self.executar("9\n0\n")
        self.assertIn("Erro ao abrir arquivo para salvar", saida)
        self.assertNotIn("pedido(s) salvo(s)", saida)

    @unittest.skipUnless(Path("/dev/full").exists(), "requer /dev/full no Linux")
    def test_erro_de_escrita_no_fechamento(self):
        self.arquivo.symlink_to("/dev/full")
        saida = self.executar("1\n1\nBatata\n1\n9\n0\n")
        self.assertIn("Erro ao fechar arquivo de pedidos", saida)
        self.assertNotIn("pedido(s) salvo(s)", saida)

    def test_valores_inteiros_aceitos_pelo_cadastro(self):
        # Nao restringir somente na carga os valores que o cadastro aceita.
        self.gravar("-1;Pedido;0;0\n")
        saida = self.executar("10\n9\n0\n")
        self.assertIn("1 pedido(s) carregado(s)", saida)
        self.assertEqual(self.arquivo.read_text(), "-1;Pedido;0;0\n")


if __name__ == "__main__":
    unittest.main(verbosity=2)
