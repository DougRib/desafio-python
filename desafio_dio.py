from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Optional


def menu():
    menu_texto = """
================ MENU ================
[d] Depositar
[s] Sacar
[e] Extrato
[nu] Novo Usuário
[nc] Nova Conta
[lc] Listar Contas
[q] Sair
=> """
    return input(menu_texto)


# Interfaces e transações
class Transacao(ABC):
    @abstractmethod
    def executar(self, conta):
        pass

    @abstractmethod
    def descricao(self) -> str:
        pass


@dataclass
class Deposito(Transacao):
    valor: float

    def executar(self, conta):
        if self.valor > 0:
            conta.saldo += self.valor
            conta.historico.registrar(self.descricao())
            return True
        return False

    def descricao(self) -> str:
        return f"Depósito:\tR$ {self.valor:.2f}"


@dataclass
class Saque(Transacao):
    valor: float

    def executar(self, conta):
        if self.valor <= 0:
            return False, "valor_invalido"
        if self.valor > conta.saldo:
            return False, "saldo_insuficiente"
        if self.valor > conta.limite:
            return False, "excede_limite"
        if conta.numero_saques >= conta.limite_saques:
            return False, "excede_numero_saques"

        # efetua saque
        conta.saldo -= self.valor
        conta.numero_saques += 1
        conta.historico.registrar(self.descricao())
        return True, None

    def descricao(self) -> str:
        return f"Saque:\t\tR$ {self.valor:.2f}"


# Histórico de transações
@dataclass
class Historico:
    registros: List[str] = field(default_factory=list)

    def registrar(self, linha: str):
        self.registros.append(linha)

    def esta_vazio(self) -> bool:
        return len(self.registros) == 0

    def texto(self) -> str:
        if self.esta_vazio():
            return ""
        return "\n".join(self.registros) + "\n"


# Clientes e pessoas
@dataclass
class Cliente:
    nome: str
    endereco: str


@dataclass
class PessoaFisica(Cliente):
    cpf: str
    data_nascimento: str


# Contas
class Conta:
    def __init__(self, agencia: str, numero_conta: int, cliente: Cliente,
                 saldo: float = 0.0, limite: float = 500.0, limite_saques: int = 3):
        self.agencia = agencia
        self.numero_conta = numero_conta
        self.cliente = cliente
        self.saldo = saldo
        self.limite = limite
        self.limite_saques = limite_saques
        self.numero_saques = 0
        self.historico = Historico()

    def executar_transacao(self, transacao: Transacao):
        if isinstance(transacao, Deposito):
            sucesso = transacao.executar(self)
            return {"sucesso": sucesso}
        if isinstance(transacao, Saque):
            sucesso, motivo = transacao.executar(self)
            return {"sucesso": sucesso, "motivo": motivo}
        return {"sucesso": False, "motivo": "transacao_desconhecida"}

    def exibir_extrato(self):
        print("\n================ EXTRATO ================")
        print("Não foram realizadas movimentações." if self.historico.esta_vazio() else self.historico.texto())
        print(f"\nSaldo:\t\tR$ {self.saldo:.2f}")
        print("==========================================")


# Funções auxiliares para gestão de usuários/contas
def filtrar_usuario_por_cpf(cpf: str, usuarios: List[PessoaFisica]) -> Optional[PessoaFisica]:
    for u in usuarios:
        if u.cpf == cpf:
            return u
    return None


def criar_usuario(usuarios: List[PessoaFisica]):
    cpf = input("Informe o CPF (somente números): ").strip()
    if filtrar_usuario_por_cpf(cpf, usuarios):
        print("\n@@@ Já existe usuário com esse CPF! @@@")
        return

    nome = input("Informe o nome completo: ").strip()
    data_nascimento = input("Informe a data de nascimento (dd-mm-aaaa): ").strip()
    endereco = input("Informe o endereço (logradouro, nro - bairro - cidade/sigla estado): ").strip()

    pf = PessoaFisica(nome=nome, endereco=endereco, cpf=cpf, data_nascimento=data_nascimento)
    usuarios.append(pf)
    print("=== Usuário criado com sucesso! ===")


def criar_conta(agencia: str, numero_conta: int, usuarios: List[PessoaFisica]) -> Optional[Conta]:
    cpf = input("Informe o CPF do usuário: ").strip()
    usuario = filtrar_usuario_por_cpf(cpf, usuarios)
    if usuario:
        conta = Conta(agencia=agencia, numero_conta=numero_conta, cliente=usuario)
        print("\n=== Conta criada com sucesso! ===")
        return conta

    print("\n@@@ Usuário não encontrado, fluxo de criação de conta encerrado! @@@")
    return None


def listar_contas(contas: List[Conta]):
    if not contas:
        print("\n@@@ Não há contas cadastradas. @@@")
        return
    for conta in contas:
        linha = f"""Agência:\t{conta.agencia}
C/C:\t\t{conta.numero_conta}
Titular:\t{conta.cliente.nome}
"""
        print("=" * 60)
        print(linha)


# Programa principal (CLI)
def main():
    LIMITE_SAQUES = 3
    AGENCIA = "0001"

    usuarios: List[PessoaFisica] = []
    contas: List[Conta] = []
    numero_conta_seq = 1

    while True:
        opcao = menu().strip().lower()

        if opcao == "d":
            if not contas:
                print("\n@@@ Não há contas. Crie uma conta primeiro. @@@")
                continue
            try:
                n = int(input("Informe o número da conta: "))
            except ValueError:
                print("\n@@@ Número de conta inválido. @@@")
                continue
            conta = next((c for c in contas if c.numero_conta == n), None)
            if not conta:
                print("\n@@@ Conta não encontrada. @@@")
                continue
            try:
                valor = float(input("Informe o valor do depósito: "))
            except ValueError:
                print("\n@@@ Valor inválido. @@@")
                continue

            trans = Deposito(valor=valor)
            resultado = conta.executar_transacao(trans)
            if resultado["sucesso"]:
                print(f"\n=== Depósito de R$ {valor:.2f} realizado com sucesso! ===")
            else:
                print("\n@@@ Operação falhou! O valor informado é inválido. @@@")

        elif opcao == "s":
            if not contas:
                print("\n@@@ Não há contas. Crie uma conta primeiro. @@@")
                continue
            try:
                n = int(input("Informe o número da conta: "))
            except ValueError:
                print("\n@@@ Número de conta inválido. @@@")
                continue
            conta = next((c for c in contas if c.numero_conta == n), None)
            if not conta:
                print("\n@@@ Conta não encontrada. @@@")
                continue
            try:
                valor = float(input("Informe o valor do saque: "))
            except ValueError:
                print("\n@@@ Valor inválido. @@@")
                continue

            conta.limite_saques = LIMITE_SAQUES  # mantém consistência caso queira ajustar por conta
            trans = Saque(valor=valor)
            resultado = conta.executar_transacao(trans)
            if resultado["sucesso"]:
                print(f"\n=== Saque de R$ {valor:.2f} realizado com sucesso! ===")
            else:
                motivo = resultado.get("motivo")
                if motivo == "saldo_insuficiente":
                    print("\n@@@ Operação falhou! Você não tem saldo suficiente. @@@")
                elif motivo == "excede_limite":
                    print("\n@@@ Operação falhou! O valor do saque excede o limite. @@@")
                elif motivo == "excede_numero_saques":
                    print("\n@@@ Operação falhou! Número máximo de saques excedido. @@@")
                else:
                    print("\n@@@ Operação falhou! O valor informado é inválido. @@@")

        elif opcao == "e":
            if not contas:
                print("\n@@@ Não há contas. Crie uma conta primeiro. @@@")
                continue
            try:
                n = int(input("Informe o número da conta para extrato: "))
            except ValueError:
                print("\n@@@ Número de conta inválido. @@@")
                continue
            conta = next((c for c in contas if c.numero_conta == n), None)
            if not conta:
                print("\n@@@ Conta não encontrada. @@@")
                continue
            conta.exibir_extrato()

        elif opcao == "nu":
            criar_usuario(usuarios)

        elif opcao == "nc":
            conta = criar_conta(AGENCIA, numero_conta_seq, usuarios)
            if conta:
                contas.append(conta)
                numero_conta_seq += 1

        elif opcao == "lc":
            listar_contas(contas)

        elif opcao == "q":
            break

        else:
            print("\n@@@ Operação inválida, por favor selecione novamente a operação desejada. @@@")

if __name__ == "__main__":
    main()