import base64
import requests
from hashlib import md5
import lxml.etree
import lxml.builder

envs = {
    "prod": "https://nfps-e.pmf.sc.gov.br/api/v1/autenticacao/oauth/token",
    "dev": "http://nfps-e-hml.pmf.sc.gov.br/api/v1/autenticacao/oauth/token"
}


def get_token(client_id, client_secret, username, password, env):
    password_valid = md5(password.encode())
    password_req = password_valid.hexdigest()
    url = envs[env]
    auth = f"{client_id}:{client_secret}".encode("utf-8")
    encoded_auth = base64.b64encode(auth).decode("utf-8")
    header = {"Content-Type": "application/x-www-form-urlencoded", "Authorization": f"Basic {encoded_auth}"}
    body = {
        "grant_type": "password",
        "username": username,
        "password": password_req.upper(),
        "client_id": client_id,
        "client_secret": client_secret
        }
    response = requests.post(url=url, data=body, headers=header)
    return response.json()["access_token"]


def new_payment(token):
    header = {"Authorization": f"Bearer {token}"}

def gen_xml_payment():
    E = lxml.builder.ElementMaker()
    service_items = E.itemServico(
        E.aliquota(aliquota),
        E.baseCalculo(base_calc),
        E.cst(cst),
        E.descricaoServico(service_description),
        E.idCNAE(cnae),
        E.quantidade(quantity),
        E.valorTotal(total_value),
        E.valorUnitario(unity_value)
    )
    xml_doc = E.xmlNfpse(
        E.bairroTomador(client_neighborhood),
        E.baseCalculo(int(price)),
        E.baseCalculoSubstituicao(0),
        E.cfps(cfps),
        E.codigoPostalTomador(client_cep),
        E.dataEmissao(date),
        E.emailTomador(client_email),
        E.identificacaoTomador(client_cpf_or_cnpj),
        E.itensServico(service_items),
        E.logradouroTomador(client_street),
        E.numeroAEDF(aedf),
        E.razaoSocialTomador(client_store_name),
        E.valorISSQN(issqn),
        E.valorTotalServicos(total_value),
        E.Signature(signature)
    )

    print(lxml.etree.tostring(xml_doc, pretty_print=True))
