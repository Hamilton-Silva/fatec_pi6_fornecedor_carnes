import random
from datetime import datetime, timedelta
from faker import Faker
from psycopg2.extras import execute_values
from driver.psycopg2_connect import PostgresConnect

fake = Faker("pt_BR")
db = PostgresConnect(autocommit=False)
cursor = db.get_cursor()

# === 1. Gerar 1000 Clientes ===
print("Inserindo 1000 clientes...")
regioes_sp = ["São Paulo", "Guarulhos", "Osasco", "Barueri", "Santo André", "São Bernardo do Campo"]
clientes = []
for _ in range(1000):
    nome = fake.name()
    email = f"{nome.lower().replace(' ', '.')}{random.randint(1,999)}@email.com"
    clientes.append((
        nome,
        fake.cnpj(),
        f"(11) 9{random.randint(4000,9999)}-{random.randint(1000,9999)}",
        email,
        f"{fake.street_name()}, {fake.building_number()} - {random.choice(regioes_sp)}",
        random.choice(["Atacado", "Varejo", "Restaurante", "Mercado"])
    ))

execute_values(cursor, """
    INSERT INTO tb_cliente (nome_cliente, cnpj_cliente, telefone_cliente, email_cliente, endereco_cliente, tipo_cliente)
    VALUES %s
""", clientes)
db.commit()
print("Clientes inseridos.")

# === 2. Gerar 10.000 Entradas ===
print("Gerando entradas de produto...")
cursor.execute("SELECT id_produto, preco_compra FROM tb_produto")
produtos = cursor.fetchall()

cursor.execute("SELECT id_fornecedor FROM tb_fornecedor LIMIT 1")
id_fornecedor = cursor.fetchone()[0]

entradas = []
for _ in range(10000):
    data = datetime.now() - timedelta(days=random.randint(1, 120))
    entradas.append((data, id_fornecedor))

execute_values(cursor, """
    INSERT INTO tb_entrada (data_entrada, id_fornecedor)
    VALUES %s RETURNING id_entrada, data_entrada
""", entradas)
entrada_ids = cursor.fetchall()
db.commit()

# === 3. Produto Entrada e Estoque ===
print("Gerando produto_entrada e estoque...")
produto_entrada = []
estoque = []
estoque_disponivel = {}

for id_entrada, data in entrada_ids:
    for _ in range(random.randint(2, 5)):
        prod_id, preco = random.choice(produtos)
        qtd = random.randint(50, 300)
        total = round(qtd * preco, 2)
        validade = data + timedelta(days=random.randint(15, 90))
        lote = f"L{id_entrada}P{prod_id}"
        produto_entrada.append((id_entrada, prod_id, qtd, total, validade, lote))

execute_values(cursor, """
    INSERT INTO tb_produto_entrada (id_entrada, id_produto, quantidade, preco_total, validade, lote)
    VALUES %s RETURNING id_item_entrada, id_produto, quantidade
""", produto_entrada)
entradas_result = cursor.fetchall()
db.commit()

for id_item, id_produto, qtd in entradas_result:
    qtd_disp = random.randint(qtd // 2, qtd)
    estoque.append((id_item, qtd_disp, random.choice(["Freezer", "Câmara Fria", "Prateleira"])))
    estoque_disponivel[id_item] = {'id_produto': id_produto, 'quantidade': qtd_disp}

execute_values(cursor, """
    INSERT INTO tb_estoque (item_entrada, quantidade_disponivel, localizacao)
    VALUES %s
""", estoque)
db.commit()

# === 4. Gerar 80.000 Pedidos ===
print("Gerando pedidos e itens...")
cursor.execute("SELECT id_cliente FROM tb_cliente")
clientes_ids = [row[0] for row in cursor.fetchall()]

pedido_data = []
pedido_itens = []
pedido_item_count = 0
estoque_ids = list(estoque_disponivel.keys())
random.shuffle(estoque_ids)

for _ in range(80000):
    cliente_id = random.choice(clientes_ids)
    data = datetime.now() - timedelta(days=random.randint(1, 60))
    status = random.choice(["Pendente", "Faturado", "Entregue"])
    total_pedido = 0
    itens = []
    for _ in range(random.randint(3, 6)):
        if not estoque_ids:
            break
        item_id = random.choice(estoque_ids)
        if estoque_disponivel[item_id]['quantidade'] <= 0:
            estoque_ids.remove(item_id)
            continue
        qtd = random.randint(1, min(estoque_disponivel[item_id]['quantidade'], 20))
        estoque_disponivel[item_id]['quantidade'] -= qtd
        if estoque_disponivel[item_id]['quantidade'] <= 0:
            estoque_ids.remove(item_id)
        cursor.execute("SELECT preco_venda, unidade_medida FROM tb_produto WHERE id_produto = %s",
                       (estoque_disponivel[item_id]['id_produto'],))
        preco, unidade = cursor.fetchone()
        total = round(preco * qtd, 2)
        total_pedido += total
        itens.append((None, estoque_disponivel[item_id]['id_produto'], qtd, unidade, preco))
    if not itens:
        continue
    pedido_data.append((cliente_id, data, status, total_pedido))
    pedido_itens.append(itens)
    pedido_item_count += len(itens)

# Inserir pedidos e itens
execute_values(cursor, """
    INSERT INTO tb_pedido (id_cliente, data_pedido, status, valor_total)
    VALUES %s RETURNING id_pedido
""", pedido_data)
pedido_ids = cursor.fetchall()
db.commit()

final_itens = []
for i, (pid,) in enumerate(pedido_ids):
    for item in pedido_itens[i]:
        final_itens.append((pid,) + item[1:])

execute_values(cursor, """
    INSERT INTO tb_item_pedido (id_pedido, id_produto, quantidade, unidade_medida, preco_unitario)
    VALUES %s
""", final_itens)
db.commit()

print(f"Total de pedidos: {len(pedido_ids)}")
print(f"Total de itens expedidos: {pedido_item_count}")

# Fechamento
cursor.close()
db.close_connection()

