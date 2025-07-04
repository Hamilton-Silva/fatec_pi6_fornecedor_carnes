import random
from datetime import datetime, timedelta
from faker import Faker
from psycopg2.extras import execute_values
import unicodedata
import time

from driver.psycopg2_connect import PostgresConnect 

db_connection = PostgresConnect(autocommit=False) 
if db_connection.conn is None or db_connection.conn.closed:
    print("Erro: Não foi possível estabelecer a conexão com o banco de dados. Saindo do script.")
    exit()

cursor = db_connection.get_cursor()
if cursor is None:
    print("Erro: Não foi possível obter um cursor para o banco de dados. Saindo do script.")
    db_connection.close_connection()
    exit()

fake = Faker("pt_BR")
regioes_sp = ["São Paulo", "Guarulhos", "Osasco", "Barueri", "Santo André", "São Bernardo do Campo"]

# Configurações
BATCH_SIZE_CLIENTES = 1000

print("Iniciando população do banco de dados...")
start_time = time.time()

# Inserir fornecedor fixo
print("Inserindo fornecedor fixo...")
cursor.execute("""
    INSERT INTO tb_fornecedor (nome_fornecedor, cnpj_fornecedor, telefone_fornecedor, email_fornecedor, endereco_fornecedor)
    VALUES (%s, %s, %s, %s, %s)
    RETURNING id_fornecedor;
""", (
    fake.company(), fake.cnpj(), f"(11) 9{random.randint(4000,9999)}-{random.randint(1000,9999)}", fake.company_email(),
    f"{fake.street_name()}, {fake.building_number()} - {random.choice(regioes_sp)}"
))
id_fornecedor_fixo = cursor.fetchone()[0]
db_connection.commit()
print(f"Fornecedor fixo inserido com ID: {id_fornecedor_fixo}")

# Produtos principais
produtos_para_inserir = [
    ("Tulipa de frango temperada com shoyu", "Tulipa", 40.00),
    ("Lombo fatiado", "Lombo", 47.00),
    ("Barriga", "Barriga", 53.00),
    ("Lagarto fatiado", "Lagarto", 65.00),
    ("Patinho fatiado", "Patinho", 65.00),
    ("Coxão mole", "Coxão mole", 65.00),
    ("Miolo de alcatra", "Alcatra", 85.00),
    ("Contra filé", "Contra filé", 89.00),
    ("Cupim", "Cupim", 89.00),
    ("Filé mignon", "Filé mignon", 129.00),
    ("Cordeiro temperado", "Cordeiro", 79.00),
    ("Carré", "Carré", 99.00),
    ("Ancho fatiado", "Ancho", 124.00),
    ("Chorizo fatiado", "Chorizo", 119.00)
]

# Produtos adicionais completos (do novo PDF) 
produtos_adicionais = [
    ("Tulipa de frango temperada com gengibre", "Tulipa", 40.00),
    ("Tulipa de frango temperada com missô", "Tulipa", 40.00),
    ("Tulipa de frango temperada com kimchi", "Tulipa", 40.00),
    ("Copa lombo fatiado", "Copa lombo", 47.00),
    ("Filé suíno", "Filé suíno", 47.00),
    ("Lombo (peça)", "Lombo", 42.00),
    ("Bisteca fatiada", "Bisteca", 40.00),
    ("Copa lombo (peça)", "Copa lombo", 42.00),
    ("Filé suíno sem tempero", "Filé suíno", 42.00),
    ("Filé suíno temperado", "Filé suíno", 43.00),
    ("Costela em ripas sem couro", "Costela", 38.00),
    ("Costela temperada com alho, limão e pimenta", "Costela", 40.00),
    ("Costela temperada com missô", "Costela", 40.00),
    ("Panceta com alho e pimenta", "Panceta", 49.00),
    ("Panceta com kimchi (1kg)", "Panceta", 49.00),
    ("Panceta com kimchi (500g)", "Panceta", 25.00),
    ("Panceta com missô (1kg)", "Panceta", 49.00),
    ("Panceta com missô (500g)", "Panceta", 25.00),
    ("Joelho suíno", "Joelho", 39.00),
    ("Linguiça alho tradicional (1kg)", "Linguiça", 42.00),
    ("Linguiça alho light (1kg)", "Linguiça", 42.00),
    ("Linguiça missô (1kg)", "Linguiça", 42.00),
    ("Linguiça gengibre (1kg)", "Linguiça", 42.00),
    ("Linguiça nirá (1kg)", "Linguiça", 42.00),
    ("Linguiça curry (1kg)", "Linguiça", 42.00),
    ("Linguiça wasabi (1kg)", "Linguiça", 42.00),
    ("Linguiça muçarela (1kg)", "Linguiça", 42.00),
    ("Linguiça codeguim (1kg)", "Linguiça", 42.00),
    ("Linguiça sortida (500g)", "Linguiça", 23.00),
    ("Manta de pernil temperada (1kg)", "Manta de pernil", 42.00),
    ("Manta de pernil temperada (500g)", "Manta de pernil", 23.00),
    ("Salame (peça 400g)", "Salame", 42.00),
    ("Salame fatiado (200g)", "Salame", 24.00),
    ("Banha de porco (450g)", "Banha", 27.00),
    ("Pé de porco", "Pé", 18.00),
    ("Pele de porco (courinho)", "Pele", 12.00),
    ("Picanha de novilho (acima 800g)", "Picanha", 129.00),
    ("Picanha de novilho (até 800g)", "Picanha", 139.00),
    ("Filé mignon de novilho", "Filé mignon", 124.00),
    ("Contra filé de novilho", "Contra filé", 85.00),
    ("Miolo da alcatra de novilho", "Alcatra", 82.00),
    ("Miolo da alcatra de novilho no sereno", "Alcatra", 82.00),
    ("Miolo da paleta de novilho", "Paleta", 55.00),
    ("Maminha de novilho", "Maminha", 82.00),
    ("Fraldinha de novilho sem tempero", "Fraldinha", 74.00),
    ("Fraldinha de novilho temperada", "Fraldinha", 76.00),
    ("Pacú da fraldinha de novilho", "Fraldinha", 74.00),
    ("Chuleta de novilho", "Chuleta", 70.00),
    ("Coxão mole de novilho", "Coxão mole", 55.00),
    ("Patinho de novilho", "Patinho", 55.00),
    ("Lagarto (peça)", "Lagarto", 55.00),
    ("Peixinho (moído ou peça)", "Peixinho", 50.00),
    ("Cupim de novilho sem tempero", "Cupim", 82.00),
    ("Cupim de novilho com missô", "Cupim", 84.00),
    ("Cupim de novilho com kimchi", "Cupim", 84.00),
    ("Cupim de novilho fatiado sem tempero", "Cupim", 83.00),
    ("Cupim de novilho temperado para churrasco", "Cupim", 84.00),
    ("Costelão de novilho", "Costela", 49.00),
    ("Costela de tiras novilho", "Costela", 49.00),
    ("Kafta mista (1kg)", "Kafta", 54.00),
    ("Músculo traseiro de novilho", "Músculo", 49.00),
    ("Acém de novilho", "Acém", 49.00),
    ("Rabo de novilho", "Rabo", 49.00),
    ("Picanha black angus", "Picanha", 184.00),
    ("Short rib black angus", "Short rib", 99.00),
    ("Chorizo black angus", "Chorizo", 124.00),
    ("Ancho black angus", "Ancho", 129.00),
    ("T-bone black angus", "T-bone", 119.00),
    ("Prime rib black angus", "Prime rib", 119.00),
    ("Tomahawk", "Tomahawk", 119.00),
    ("Denver steak", "Denver", 169.00),
    ("Baby beef", "Baby beef", 95.00),
    ("Shoulder steak", "Shoulder", 99.00),
    ("Fraldinha black angus", "Fraldinha", 94.00),
    ("Pacú da fraldinha black angus", "Fraldinha", 94.00),
    ("Entranha black angus", "Entranha", 94.00),
    ("Maminha black angus", "Maminha", 94.00),
    ("Lagarto black angus", "Lagarto", 60.00),
    ("Peixinho black angus", "Peixinho", 55.00),
    ("Brisket black angus", "Brisket", 55.00),
    ("Costela de tiras black angus", "Costela", 55.00),
    ("Rabo black angus", "Rabo", 49.00),
    ("Linguiça bovina angus (500g)", "Linguiça", 24.00),
    ("Linguiça bovina angus (1kg)", "Linguiça", 47.00),
    ("Manta bovina angus (500g)", "Manta bovina", 24.00),
    ("Manta bovina angus (1kg)", "Manta bovina", 47.00),
    ("Linguiça cuiabana angus (1kg)", "Linguiça cuiabana", 49.00),
    ("Linguiça cuiabana angus (500g)", "Linguiça cuiabana", 25.00),
    ("Linguiça mista angus + suína (1kg)", "Linguiça mista", 45.00),
    ("Linguiça mista angus + suína (500g)", "Linguiça mista", 23.00)
]

produtos_para_inserir += produtos_adicionais

# Inserção dos produtos
print("Inserindo produtos...")
produto_data_list = []
for nome, tipo, preco_venda in produtos_para_inserir:
    preco_compra = round(preco_venda * random.uniform(0.7, 0.9), 2)
    produto_data_list.append((nome, tipo, "Kg", preco_compra, preco_venda, id_fornecedor_fixo))

execute_values(cursor, """
    INSERT INTO tb_produto (nome_produto, tipo_corte, unidade_medida, preco_compra, preco_venda, id_fornecedor)
    VALUES %s
""", produto_data_list)
db_connection.commit()
print(f"{len(produto_data_list)} produtos inseridos.")

# Encerramento de conexão
db_connection.close_connection()
end_time = time.time()
print(f"Finalizado em {end_time - start_time:.2f} segundos.")