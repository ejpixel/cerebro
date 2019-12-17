import base64
import requests
from hashlib import md5
import lxml.etree
import lxml.builder
import os

import signxml
from OpenSSL import crypto
from signxml import XMLSigner, XMLVerifier


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


def new_payment(token, xml_as_string):
    # print(token)
    # header = {"Authorization": f"Bearer {token}"}
    response = requests.post("http://nfps-e-hml.pmf.sc.gov.br/api/v1/processamento/notas/valida-processamento", data=xml_as_string)#, headers=header)
    print(response.text)


def gen_xml_payment(client_neighborhood, price, client_cep, date_iso_format, client_email, client_cpf_or_cnpj, client_street, client_store_name, service_description, quantity, aliquota, aedf, cst, cfps, cnae, baseCalcSubst):
    token = get_token(os.environ["CLIENT_ID"], os.environ["CLIENT_SECRET"], os.environ["CMC"], os.environ["PASSWORD"], "prod")
    E = lxml.builder.ElementMaker()
    service_items = E.itemServico(
        E.aliquota(str(aliquota * 100)),
        E.baseCalculo(str(price * quantity)),
        E.cst(str(cst)),
        E.descricaoServico(service_description),
        E.idCNAE(str(cnae)),
        E.quantidade(str(quantity)),
        E.valorTotal(str(price * quantity)),
        E.valorUnitario(str(price))
    )
    xml_doc = E.xmlProcessamentoNfpse(
        E.bairroTomador(client_neighborhood),
        E.baseCalculo(str(price * quantity)),
        E.baseCalculoSubstituicao(str(baseCalcSubst)),
        E.cfps(str(cfps)),
        E.codigoPostalTomador(client_cep),
        E.dataEmissao(date_iso_format),
        E.emailTomador(client_email),
        E.identificacaoTomador(client_cpf_or_cnpj),
        E.itensServico(service_items),
        E.logradouroTomador(client_street),
        E.numeroAEDF(str(aedf)),
        E.razaoSocialTomador(client_store_name),
        E.valorISSQN(str(aliquota * price * quantity)),
        E.valorTotalServicos(str(price * quantity))
    )
    xml_doc = insert_signature(xml_doc, os.environ["CERTIFIED"], os.environ["CERTIFIED_PASSWORD"])

    print(lxml.etree.tostring(xml_doc, pretty_print=True).decode())
    new_payment(token, lxml.etree.tostring(xml_doc, pretty_print=True).decode())

def insert_signature(root, pfx, password):
    pfx_file = open(pfx, "rb")
    pfx = crypto.load_pkcs12(pfx_file.read(), password)
    # PEM formatted private key
    key = crypto.dump_privatekey(crypto.FILETYPE_PEM,
                                 pfx.get_privatekey())
    # PEM formatted certificate
    cert = crypto.dump_certificate(crypto.FILETYPE_PEM,
                                   pfx.get_certificate())

    pfx_file.close()
    cert = cert
    key = key
    signed_root = XMLSigner(method=signxml.methods.enveloped, signature_algorithm="rsa-sha1",
                            digest_algorithm='sha1',
                            c14n_algorithm='http://www.w3.org/TR/2001/REC-xml-c14n-20010315').sign(root, key=key, cert=cert)
    return signed_root
