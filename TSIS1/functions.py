functions = [
    """
    CREATE OR REPLACE FUNCTION search_contacts(
        p_query TEXT,
        p_sort_by TEXT DEFAULT 'name' -- Options: (n)ame, (b)irthday, (d)ate
    )
    RETURNS TABLE (
        contact_id INTEGER,
        name VARCHAR,
        email VARCHAR,
        birthday DATE,
        group_name VARCHAR,
        phone_list TEXT,
        created_at TIMESTAMP
    ) AS $$
    BEGIN
        RETURN QUERY
        SELECT 
            c.id, 
            c.name, 
            c.email, 
            c.birthday, 
            g.name AS group_name,
            string_agg(p.phone || ' (' || p.type || ')', ', ') AS phone_list,
            c.created_at
        FROM contacts c
        LEFT JOIN groups g ON c.group_id = g.id
        LEFT JOIN phones p ON c.id = p.contact_id
        WHERE c.name ILIKE '%' || p_query || '%'
           OR c.email ILIKE '%' || p_query || '%'
           OR p.phone ILIKE '%' || p_query || '%'
        GROUP BY c.id, g.name, c.created_at, c.birthday
        ORDER BY 
            CASE WHEN p_sort_by = 'n' THEN c.name END ASC,
            CASE WHEN p_sort_by = 'b' THEN c.birthday END ASC,
            CASE WHEN p_sort_by = 'd' THEN c.created_at END DESC;
    END;
    $$ LANGUAGE plpgsql;    
    """,

    """
    CREATE OR REPLACE FUNCTION select_with_pagination(lim INTEGER, offs INTEGER)
    RETURNS TABLE (
        id INTEGER, 
        name VARCHAR, 
        email VARCHAR, 
        birthday DATE, 
        group_name VARCHAR, 
        phones TEXT,
        created_at TIMESTAMP  -- Added this to match print_contacts expectations
    ) AS $$
        BEGIN
        RETURN QUERY
        SELECT 
            c.id, 
            c.name, 
            c.email, 
            c.birthday, 
            g.name,
            string_agg(p.phone, ', '),
            c.created_at
        FROM contacts c
        LEFT JOIN groups g ON c.group_id = g.id
        LEFT JOIN phones p ON c.id = p.contact_id
        GROUP BY c.id, g.name, c.created_at
        ORDER BY c.name
        LIMIT lim OFFSET offs;
    END;
    $$ LANGUAGE plpgsql;
    """
]