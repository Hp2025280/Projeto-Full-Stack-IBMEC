
from componentes.base_tela import TelaBase
import streamlit as st
from connection.base_api import BaseAPI
import pandas as pd


class AlunoTela(TelaBase):

    def __init__(self):
        self.base = BaseAPI()
        self.titulo = "Tela de Aluno"
        self.descricao = "Essa tela é usada para gerenciar alunos"

    def consultar(self):
        endpoint = "/alunos/pegar-dados-alunos"
        return self.base.get(endpoint)

    def consultar_por_id(self, id):
        endpoint = f"/alunos/pegar-dados-alunos-por-id/{id}"
        return self.base.get(endpoint)

    def criar(self, params):
        endpoint = "/alunos/criar-aluno"
        return self.base.post(endpoint, params)

    def atualizar(self, id, params):
        endpoint = f"/alunos/atualizar-aluno/{id}"
        return self.base.put(endpoint, params)

    def deletar(self, id):
        endpoint = f"/alunos/deletar-aluno/{id}"
        return self.base.delete(endpoint)

    def criar_dataframe(self, dados):
        if dados is None or dados == []:
            st.info("Nenhum aluno encontrado.")
            return

        if isinstance(dados, dict):
            dados = [dados]

        df = pd.DataFrame(dados)
        st.dataframe(df)

    def renderizar(self):
        super().cabecalho(self.titulo, self.descricao)

        abas = st.tabs([
            "Consultar todos",
            "Consultar por ID",
            "Criar Aluno",
            "Atualizar Aluno",
            "Deletar Aluno"
        ])

        # CONSULTAR TODOS
        with abas[0]:
            st.subheader("Todos os alunos")

            if st.button("Consultar todos"):
                try:
                    dados = self.consultar()
                    self.criar_dataframe(dados)
                except Exception as erro:
                    st.error(f"Erro ao consultar: {erro}")

        # CONSULTAR POR ID
        with abas[1]:
            st.subheader("Consultar aluno por ID")

            id = st.text_input(
                "Digite o ID do aluno:",
                key="consultar_id"
            )

            if st.button("Consultar aluno por ID"):
                if not id.strip().isdigit():
                    st.error("Digite um ID válido.")
                else:
                    try:
                        dados = self.consultar_por_id(int(id))
                        self.criar_dataframe(dados)
                    except Exception as erro:
                        st.error(f"Erro ao consultar: {erro}")

        # CRIAR ALUNO
        with abas[2]:
            st.subheader("Cadastrar novo aluno")

            with st.form("form_criar_aluno"):
                matricula = st.text_input("Matrícula")
                nome = st.text_input("Nome do aluno")
                email = st.text_input("Email")
                endereco_id = st.text_input("ID do endereço")

                cadastrar = st.form_submit_button("Criar aluno")

                if cadastrar:
                    if not all([
                        matricula.strip(),
                        nome.strip(),
                        email.strip(),
                        endereco_id.strip()
                    ]):
                        st.warning("Preencha todos os campos.")

                    elif not endereco_id.strip().isdigit():
                        st.error("O ID do endereço deve ser numérico.")

                    else:
                        params = {
                            "matricula": matricula.strip(),
                            "nome_aluno": nome.strip(),
                            "email": email.strip(),
                            "endereco_id": int(endereco_id)
                        }

                        try:
                            retorno = self.criar(params)

                            if retorno.status_code in (200, 201):
                                st.success("Aluno criado com sucesso!")
                                st.json(retorno.json())
                            else:
                                st.error(
                                    f"Erro {retorno.status_code}: "
                                    f"{retorno.text}"
                                )

                        except Exception as erro:
                            st.error(f"Erro ao criar aluno: {erro}")

        # ATUALIZAR ALUNO
        with abas[3]:
            st.subheader("Atualizar aluno")

            st.info(
                "Preencha apenas os campos que deseja alterar. "
                "Deixe os outros vazios."
            )

            with st.form("form_atualizar_aluno"):
                id = st.text_input(
                    "ID do aluno que deseja atualizar"
                )

                matricula = st.text_input(
                    "Nova matrícula (opcional)"
                )

                nome = st.text_input(
                    "Novo nome (opcional)"
                )

                email = st.text_input(
                    "Novo email (opcional)"
                )

                endereco_id = st.text_input(
                    "Novo ID do endereço (opcional)"
                )

                atualizar = st.form_submit_button("Atualizar aluno")

                if atualizar:
                    if not id.strip().isdigit():
                        st.error("Digite um ID de aluno válido.")

                    elif (
                        endereco_id.strip()
                        and not endereco_id.strip().isdigit()
                    ):
                        st.error("O ID do endereço deve ser numérico.")

                    else:
                        params = {}

                        if matricula.strip():
                            params["matricula"] = matricula.strip()

                        if nome.strip():
                            params["nome_aluno"] = nome.strip()

                        if email.strip():
                            params["email"] = email.strip()

                        if endereco_id.strip():
                            params["endereco_id"] = int(endereco_id)

                        if not params:
                            st.warning(
                                "Preencha pelo menos um campo "
                                "para atualizar."
                            )

                        else:
                            try:
                                retorno = self.atualizar(
                                    int(id),
                                    params
                                )

                                if retorno.status_code == 200:
                                    st.success(
                                        "Aluno atualizado com sucesso!"
                                    )
                                    st.json(retorno.json())
                                else:
                                    st.error(
                                        f"Erro {retorno.status_code}: "
                                        f"{retorno.text}"
                                    )

                            except Exception as erro:
                                st.error(
                                    f"Erro ao atualizar aluno: {erro}"
                                )

        # DELETAR ALUNO
        with abas[4]:
            st.subheader("Deletar aluno")

            id = st.text_input(
                "Digite o ID do aluno que deseja deletar",
                key="deletar_id"
            )

            if st.button("Deletar aluno"):
                if not id.strip().isdigit():
                    st.error("Digite um ID válido.")

                else:
                    try:
                        retorno = self.deletar(int(id))

                        if retorno.status_code == 200:
                            st.success("Aluno deletado com sucesso!")
                        else:
                            st.error(
                                f"Erro {retorno.status_code}: "
                                f"{retorno.text}"
                            )

                    except Exception as erro:
                        st.error(f"Erro ao deletar aluno: {erro}")

        super().rodape()


AlunoTela().renderizar()
