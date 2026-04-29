procedures = [
    """
    CREATE OR REPLACE PROCEDURE delete_contact(pattern VARCHAR(255))
    AS
    $$
    BEGIN
        DELETE FROM contacts WHERE contacts.name ILIKE pattern OR contacts.phone ILIKE pattern;
    END;
    $$
    LANGUAGE plpgsql;
    """,

    """
    CREATE OR REPLACE PROCEDURE add_or_update(new_name VARCHAR(255), new_phone VARCHAR(255))
    AS
    $$
    BEGIN
        IF EXISTS (SELECT 1 FROM contacts WHERE name = new_name) THEN
            UPDATE contacts SET phone = new_phone
            WHERE name = new_name;
        ELSEIF EXISTS (SELECT 1 FROM contacts WHERE phone = new_phone) THEN
            UPDATE contacts SET name = new_name
            WHERE phone = new_phone;
        ELSE
            INSERT INTO contacts(name, phone)
            VALUES(new_name, new_phone);
        END IF;
    END;
    $$
    LANGUAGE plpgsql;
    """,

    r"""
    CREATE OR REPLACE PROCEDURE mass_insert_contacts(
        p_name VARCHAR,
        p_email VARCHAR,
        p_birthday DATE,
        p_group_name VARCHAR,
        p_phones VARCHAR[], -- Array of phone numbers
        p_phone_types VARCHAR[] -- Array of types (mobile, work, etc.)
    ) AS $$
    DECLARE
        v_group_id INTEGER;
        v_contact_id INTEGER;
            i INTEGER;
    BEGIN
        -- 1. Handle the Group (Insert if it doesn't exist)
        IF p_group_name IS NOT NULL THEN
            INSERT INTO groups (name)
            VALUES (p_group_name)
            ON CONFLICT (name) DO NOTHING;
            
            SELECT id INTO v_group_id FROM groups WHERE name = p_group_name;
        END IF;
    
        -- 2. Insert the Contact
        INSERT INTO contacts (name, email, birthday, group_id)
        VALUES (p_name, p_email, p_birthday, v_group_id)
        RETURNING id INTO v_contact_id;
    
        -- 3. Insert Multiple Phones
        IF p_phones IS NOT NULL THEN
            FOR i IN 1 .. array_upper(p_phones, 1) LOOP
                INSERT INTO phones (contact_id, phone, type)
                VALUES (v_contact_id, p_phones[i], p_phone_types[i]);
            END LOOP;
        END IF;
    END;
    $$ LANGUAGE plpgsql;
    """,

    """
    CREATE OR REPLACE PROCEDURE add_phone(
        p_contact_name VARCHAR, 
        p_phone VARCHAR, 
        p_type VARCHAR
    ) AS $$
    DECLARE
        v_contact_id INTEGER;
    BEGIN
        SELECT id INTO v_contact_id FROM contacts WHERE name = p_contact_name;
        
        IF v_contact_id IS NULL THEN
            RAISE EXCEPTION 'Contact % not found', p_contact_name;
        END IF;
    
        INSERT INTO phones (contact_id, phone, type)
        VALUES (v_contact_id, p_phone, p_type);
    END;
    $$ LANGUAGE plpgsql;
    """,

    """
    CREATE OR REPLACE PROCEDURE move_to_group(
        p_contact_name VARCHAR, 
        p_group_name VARCHAR
    ) AS $$
    DECLARE
        v_group_id INTEGER;
    BEGIN
        -- 1. Ensure the group exists
        INSERT INTO groups (name)
        VALUES (p_group_name)
        ON CONFLICT (name) DO NOTHING;
    
        -- 2. Get the group_id
        SELECT id INTO v_group_id FROM groups WHERE name = p_group_name;
    
        -- 3. Update the contact
        UPDATE contacts 
        SET group_id = v_group_id 
        WHERE name = p_contact_name;
        
        IF NOT FOUND THEN
            RAISE EXCEPTION 'Contact % not found', p_contact_name;
        END IF;
    END;
    $$ LANGUAGE plpgsql;
    """
]