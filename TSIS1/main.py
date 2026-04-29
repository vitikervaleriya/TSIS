import psycopg2 # type: ignore
import json
import csv
from functions import functions
from procedures import procedures

# Load database configuration from JSON file
with open("config.json", "r") as f:
    json_config = json.load(f)

# Establish connection to PostgreSQL database
conn = psycopg2.connect(
    host=json_config["host"],
    database=json_config["db_name"],
    user=json_config["user"],
    password=json_config["password"]
)


def create_table_if_not_exists() -> None:
    # SQL queries to create tables if they do not already exist
    queries = [
        """
        CREATE TABLE IF NOT EXISTS groups (
            id SERIAL PRIMARY KEY,
            name VARCHAR UNIQUE
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS contacts (
            id SERIAL PRIMARY KEY,
            name VARCHAR,
            email VARCHAR,
            birthday DATE,
            group_id INTEGER REFERENCES groups(id),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS phones (
            id SERIAL PRIMARY KEY,
            contact_id INTEGER REFERENCES contacts(id),
            phone VARCHAR,
            type VARCHAR
        )
        """
    ]

    # Execute all table creation queries
    with conn.cursor() as cursor:
        for q in queries:
            cursor.execute(q)
        conn.commit()


def create_all_functions_and_procedures() -> None:
    # Create all SQL functions and stored procedures
    try:
        with conn.cursor() as cursor:
            for i in functions + procedures:
                cursor.execute(i)
            conn.commit()
    except (psycopg2.DatabaseError, Exception) as error:
        # Print any database-related error
        print(error)


def print_contacts(contacts: list[tuple], group_filter: str = "") -> None:
    print()

    # If no contacts found, show message
    if not contacts:
        print("(no contacts found)")
        return

    # Print table header
    print(f"{'ID':<4} | {'Name':<15} | {'Email':<20} | {'Birthday':<12} | {'Group':<10} | {'Phones'}")
    print("-" * 80)

    # Iterate through contacts and display them
    for c in contacts:

        # Extract group name (if exists)
        c_group = c[4] if c[4] else "(blank)"

        # Apply group filter if provided
        if not group_filter or group_filter.lower() in c_group.lower():
            print(f"[{c[0]:<2}]. {c[1]:<15} - {c[2]:<20} - {c[3]} - {c_group:<10} - {c[5]}")


def get_all_contacts(sort_type: str) -> list[tuple]:
    # Validate sorting type (n = name, b = birthday, d = date added)
    if not any(sort_type == i for i in "nbd"):
        sort_type = "n"

    # Call SQL function to get contacts
    return call_function("search_contacts", "", sort_type)


def call_function(name: str, *args: tuple[object]) -> object:
    # Call PostgreSQL function
    with conn.cursor() as cursor:
        cursor.callproc(name, args)
        data = cursor.fetchall()

    return data


def call_procedure(name: str, *args: tuple[object]) -> None:
    # Build SQL CALL statement dynamically
    command = f"CALL {name}(" + ("%s, " * len(args)).strip(", ") + ")"

    try:
        with conn.cursor() as cursor:
            cursor.execute(command, args)
            conn.commit()
    except (psycopg2.DatabaseError, Exception) as error:
        print(error)


def search_contacts(pattern: str, sort_type: str) -> list[tuple]:
    # Validate sort type
    if not any(sort_type == i for i in "nbd"):
        sort_type = "n"

    # Search contacts in database
    return call_function("search_contacts", pattern, sort_type)


def add_from_terminal() -> None:
    # Add or update contact from terminal input
    action = input("(A)dd new contact or add (p)hone number to existing one: ").lower()

    if action == "a":

        name = input("Name: ")

        phone = [input("Phone: ")]

        phone_type = input("(M)obile or (w)ork: ").lower()

        # Normalize phone type
        if phone_type == "w":
            phone_type = ["work"]
        else:
            phone_type = ["mobile"]

        email = input("Email: ")
        birthday = input("Birthday date: ")
        group = input("Group: ")

        # Insert full contact
        call_procedure("mass_insert_contacts", name, email, birthday, group, phone, phone_type)

    elif action == "p":

        name = input("Name: ")
        phone = input("New phone: ")

        phone_type = input("(M)obile or (w)ork: ").lower()

        if phone_type == "w":
            phone_type = "work"
        else:
            phone_type = "mobile"

        # Add phone to existing contact
        call_procedure("add_phone", name, phone, phone_type)

    else:
        print("Choose valid action")


def import_from_csv(file_path: str) -> None:
    # Import contacts from CSV file
    with open(file_path, 'r') as f:

        reader = csv.reader(f)
        cur = conn.cursor()

        for row in reader:

            # Parse CSV structure
            name, phones_raw, types_raw, email, birthday, group = row

            # Convert string lists into Python lists
            phones = phones_raw.strip("()").split()
            types = types_raw.strip("()").split()

            try:
                call_procedure("mass_insert_contacts", name, email, birthday, group, phones, types)
            except Exception as e:
                print(f"Error inserting {name}: {e}")
                conn.rollback()
            else:
                conn.commit()

        cur.close()


def import_from_json(file_path):
    # Import contacts from JSON file
    with open(file_path, 'r') as f:
        data = json.load(f)

    for item in data:

        with conn.cursor() as cur:

            # Check if contact already exists
            cur.execute(
                "SELECT id FROM contacts WHERE name = %s",
                (item['name'],)
            )

            exists = cur.fetchone()

            # If exists, ask user what to do
            if exists:
                choice = input(f"Contact '{item['name']}' exists. (S)kip / (O)verwrite: ").lower()

                if choice == 's':
                    continue
                elif choice == 'o':
                    cur.execute("DELETE FROM contacts WHERE name = %s", (item['name'],))

            try:
                # Insert contact via stored procedure
                cur.execute(
                    "CALL mass_insert_contacts(%s, %s, %s, %s, %s, %s)",
                    (
                        item['name'],
                        item['email'],
                        item['birthday'],
                        item['group'],
                        item['phones'],
                        item['types']
                    )
                )
                conn.commit()

            except Exception as e:
                print(f"Error importing {item['name']}: {e}")
                conn.rollback()


def export_to_json(file_path: str) -> None:
    # Export contacts to JSON file
    cur = conn.cursor()

    cur.execute("SELECT name, email, birthday, group_name, phone_list FROM search_contacts('')")
    rows = cur.fetchall()

    contacts = []

    for row in rows:

        phones = []
        types = []

        # Parse phone data if exists
        if row[4]:
            phone_info = map(lambda x: x.split("("), row[4].split(","))

            for p, t in phone_info:
                phones.append(p.strip())
                types.append(t.strip().strip(")"))

        contacts.append({
            "name": row[0],
            "email": row[1],
            "birthday": str(row[2]),
            "group": row[3],
            "phones": phones,
            "types": types
        })

    # Write to JSON file
    with open(file_path, 'w') as f:
        json.dump(contacts, f, indent=4)

    cur.close()


def get_contacts_with_pagination(limit: int, offset: int) -> list[tuple]:
    # Get paginated contacts
    return call_function("select_with_pagination", limit, offset)


def delete_contact(pattern: str) -> None:
    # Delete contact by name or phone
    call_procedure("delete_contact", pattern)


def add_phone_to_contact(contact_name: str, phone: str, phone_type: str) -> None:
    # Add phone to existing contact
    call_procedure("add_phone", contact_name, phone, phone_type)


def move_contact_to_group(contact_name: str, group_name: str) -> None:
    # Move contact to another group
    call_procedure("move_to_group", contact_name, group_name)


def pagination_loop() -> None:
    # Pagination menu loop
    limit = int(input("Show how many contacts per page? ") or 5)
    current_offset = 0

    while True:

        data = get_contacts_with_pagination(limit=limit, offset=current_offset)

        print(f"\n--- Page (Offset: {current_offset}) ---")

        print_contacts(data)

        nav = input("\n[N]ext Page, [P]revious Page, [B]ack to Menu: ").lower()

        if nav == 'n':

            if len(data) < limit:
                print(">> You are at the end of the list.")
            else:
                current_offset += limit

        elif nav == 'p':
            current_offset = max(0, current_offset - limit)

        elif nav == 'b':
            break


# Debug print of all contacts
print(call_function("search_contacts", "", "n"))


def main() -> None:

    # Initialize database
    create_table_if_not_exists()
    create_all_functions_and_procedures()

    # Main menu loop
    while True:

        print()
        print("--- PhoneBook ---")
        print("1(s). Show all contacts in group")
        print("2(p). Show contacts with pagination")
        print("3(a). Add or update contact (from terminal)")
        print("4(i). Import from Json")
        print("5(e). Export to Json")
        print("6(f). Find contacts")
        print("7(d). Delete contact")
        print("8(g). Change contact's group")
        print("9(q). Exit")

        choice = input("\nChoice: ")

        if choice == "1" or choice == "s":
            group = input("Group name(leave blank to include all groups): ")
            sort_type = input("Sort by (N)ame, (B)irthday or (D)ate added: ").lower().strip()
            print_contacts(get_all_contacts(sort_type), group)

        elif choice == "2" or choice == "p":
            pagination_loop()

        elif choice == "3" or choice == "a":
            add_from_terminal()

        elif choice == "4" or choice == "i":
            filename = input("Json file path: ")
            import_from_json(filename)

        elif choice == "5" or choice == "e":
            filename = input("Json file path: ")
            export_to_json(filename)

        elif choice == "6" or choice == "f":
            pattern = input("Find: ")
            group = input("Group name(leave blank to include all groups): ")
            sort_type = input("Sort by (N)ame, (B)irthday or (D)ate added: ").lower().strip()
            print_contacts(search_contacts(pattern, sort_type), group)

        elif choice == "7" or choice == "d":
            pattern = input("Name or phone: ")
            delete_contact(pattern)

        elif choice == "8" or choice == "g":
            name = input("Contact's name: ")
            group_name = input("Group name: ")
            move_contact_to_group(name, group_name)

        elif choice == "9" or choice == "q":
            break

        else:
            print("Please choose valid option")

    # Close database connection on exit
    conn.close()


if __name__ == "__main__":
    main()