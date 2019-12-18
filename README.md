# Cerebro
Gerenciador de contratos e acessos

## Uso
É necessário permissão para a utilização das ferramentas administrativas

### Database
Para acessar alguns dados pessoais, é necessário um banco de dados protegido. Por conta disso, o programa necessita que seja criado uma variável de ambiente com o link de acesso ao banco.

### Linux
```
make setup
export DATABASE_URI=<url do banco>
export SECRET_KEY=blabla
make run
```

### Final
Visitar http://localhost:5000
