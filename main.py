import sqlite3  # Importa a biblioteca para trabalhar com banco de dados SQLite
import os  # Permite executar comandos no sistema operacional (como limpar o terminal)
import time  # Permite usar funções relacionadas a tempo, como `sleep()`

# Conectar ao banco de dados (cria o arquivo "studenty.db" se ele não existir)
conn = sqlite3.connect("studenty.db")
cursor = conn.cursor()  # Cria um cursor para executar comandos SQL

# Criar a tabela se ela ainda não existir
def create_table():
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS studenty (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            semester INTEGER NOT NULL,
            email TEXT NOT NULL UNIQUE,
            registration INTEGER NOT NULL UNIQUE,
            password TEXT NOT NULL
        )
    """)
    conn.commit()  # Salva as mudanças no banco de dados

create_table()


# Função para verificar e validar o nome do usuário
def verify_name():
    global name
    while True:
        name = input("Enter the name of the studenty: ")  # Solicita o nome do usuário
        name = name.upper()
        if not name:  # Verifica se está vazio
            print("Name cannot be empty.")
            continue
        if any(char.isdigit() for char in name):  # Verifica se contém números
            print("The name can only have letters.")
            continue
        break  # Sai do loop se o nome for válido

# Função para verificar e validar a idade do usuário
def verify_semester():
    global semester
    while True:
        try:
            semester = int(input(f"Enter the {name}'s semester: "))  # Solicita a idade e converte para inteiro
            if semester <= 0:  # Verifica se a idade é positiva
                print("Age must be a positive number.")
                continue
            break
        except ValueError:
            print("Invalid input. Age must be an integer.")  # Trata erro se o usuário digitar algo inválido

# Função para verificar e validar o saldo do usuário
def verify_registration():
    global registration
    while True:
        try:
            registration = int(input(f"Enter the {name}'s registration: "))
            if registration.bit_length() != 32:
                print("The registration cannot have more than 8 digit")
                continue
            break
        except ValueError:
            print("Invalid input. registration must be a number.")  # Trata erro se o usuário digitar algo inválido

# Função para verificar e validar o email do usuário
def verify_email():
    global email
    while True:
        email = input(f"Enter {name}'s email: ")
        email = email
        if not email:  # Verifica se o email está vazio
            print("The email cannot be empty.")
            continue
        if not (email.endswith("@gmail.com") or email.endswith("@hotmail.com")):
            print("Invalid email. Email must end with @gmail.com or @hotmail.com.")  # Valida domínios específicos
            continue
        break

def verify_password():
    global password
    while True:
        password = input("Enter your password: ")
        passwordConfim = input("confirm your password: ")
        if not password:
            print("password cannot be empty.")
            continue
        if password != passwordConfim:
            print("Password doesn't match, try again.")
            continue
        break

# Função para inserir um novo usuário no banco de dados
def studenty_insert():
    os.system("cls" if os.name == "nt" else "clear")
    repeatstudentyCreation = "y"
    while repeatstudentyCreation == "y":
        verify_name()
        verify_semester()
        verify_email()
        verify_registration()
        verify_password()
        
        # Insere os dados no banco de dados
        cursor.execute("INSERT INTO studenty (name, semester, email, registration, password) VALUES (?, ?, ?, ?, ?)",(name, semester, email, registration, password))
        conn.commit()  # Salva as mudanças no banco de dados
        print("studenty successfully created!")

        repeatstudentyCreation = input("Want to add another studenty in the DB? (Y/N): ").lower()

# Função para exibir todos os usuários cadastrados
def print_table():
    os.system("cls" if os.name == "nt" else "clear")
    cursor.execute("SELECT * FROM studenty")  # Seleciona todos os registros da tabela
    records = cursor.fetchall()  # Obtém todos os registros
    
    column_names = [description[0] for description in cursor.description]  # Obtém os nomes das colunas
    
    print(" | ".join(column_names))  # Imprime os nomes das colunas
    print("-" * 40)

    for record in records:  # Itera sobre os registros e imprime os valores
        print(" | ".join(map(str, record)))

# Função para buscar usuários pelo nome ou email
def search():
    os.system("cls" if os.name == "nt" else "clear")
    searchInput = input("Want to search by name or email? ").lower()
    if searchInput == "name":
        sName = input("Enter the name: ")
        cursor.execute("SELECT * FROM studenty WHERE name = ?", (sName,))
    elif searchInput == "email":
        sEmail = input("Enter the email: ")
        cursor.execute("SELECT * FROM studenty WHERE email = ?", (sEmail,))
    else:
        print("Invalid option. Closing operation.")
        return
    
    records = cursor.fetchall()
    column_names = [description[0] for description in cursor.description]

    print(" | ".join(column_names))
    print("-" * 40)
    for record in records:
        print(" | ".join(map(str, record)))

def studenty_delete():
    os.system("cls" if os.name == "nt" else "clear") # Limpa a tela antes de iniciar a função
    print("\n======studenty DELETE======")
    choice = input("Do you want to remove by Registration or by Name? ").strip()
    if choice.lower() == "registration":
        try:
                studentyID = int(input("Input the studenty Registration: "))
                cursor.execute("DELETE FROM studenty WHERE registration = ?",(studentyID,)) # Deleta o studenty com base no id fornecido anteriormente.
        except ValueError:
            print("Invalid ID input, please try again using a existing id")
            time.sleep(2.0)
            return
    elif choice.lower() == "name":
        while True:
            studentyName = input("Enter the studenty name: ")
            if not studentyName:
                print("studenty Name cannot be null or empty")
                continue
            if any(char.isdigit() for char in studentyName): # Verifica se o studentyName(Nome do usuario) fornecido contém numeros.
                print("The studenty name cannot have numberss")
                continue
            break
        cursor.execute("DELETE FROM studenty WHERE name = ?",(studentyName.upper(),)) # Deleta o studenty com base no nome fornecido anteriormente.
        conn.commit()
        print('studenty {} has been deleted.'.format(studentyName))
        time.sleep(2.5)
# Menu do sistema
def menu():
    create_table()  # Garante que a tabela exista antes de interagir com o usuário
    while True:
        os.system("cls" if os.name == "nt" else "clear")  # Limpa o terminal
        answer = input(
            "What would you like to do in the storage center system?\n"
            "1 - Insert a new studenty.\n"
            "2 - Print the table.\n"
            "3 - Search for a studenty.\n"
            "4 - Delete a studenty.\n"
            "5 - Exit.\n"
            "Input a command: "
        )
        match answer:
            case "1":
                studenty_insert()
            case "2":
                print_table()
                aws2 = input("Want to return to the menu? Y/N \n")
                if aws2.lower() == "y":
                    os.system("cls" if os.name == "nt" else "clear")
            case "3":
                search()
                aws3 = input("Want to return to the menu? Y/N \n")
                if aws3.lower() == "y":
                    os.system("cls" if os.name == "nt" else "clear")
            case "4":
                studenty_delete()
            case "5":
                print("Exiting the system...")
                conn.commit()
                conn.close()# Fecha a conexão com o banco de dados antes de sair
                time.sleep(1.5)
                break
            case _:
                print("Invalid command.")
                time.sleep(1.5)  # Aguarda 1.5 segundos antes de continuar
                os.system("cls" if os.name == "nt" else "clear")

# Inicia o menu do sistema
menu()
