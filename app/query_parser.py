import re


# This function parses a query and returns a dictionary with each of the clauses and its predicates as a key-value pair
def parse_sql_query(input):

    sql_query = input.lower()

    # Define regular expressions to match each clause
    select_pattern = re.compile(r'select (.+?) from', re.DOTALL)
    from_pattern = re.compile(r'from (.+?) (?:where|group by|having|order by|limit|$)', re.DOTALL)
    where_pattern = re.compile(r'where (.+?) (?:group by|having|order by|limit|$)', re.DOTALL)
    group_by_pattern = re.compile(r'group by (.+?) (?:having|order by|limit|$)', re.DOTALL)
    having_pattern = re.compile(r'having (.+?) (?:order by|limit|$)', re.DOTALL)
    order_by_pattern = re.compile(r'order by (.+?) (?:limit|$)', re.DOTALL)
    limit_pattern = re.compile(r'limit (.+?)$', re.DOTALL)

    # Find the matches for each clause
    select_match = select_pattern.search(sql_query)
    from_match = from_pattern.search(sql_query)
    where_match = where_pattern.search(sql_query)
    group_by_match = group_by_pattern.search(sql_query)
    having_match = having_pattern.search(sql_query)
    order_by_match = order_by_pattern.search(sql_query)
    limit_match = limit_pattern.search(sql_query)

    # Initialise dictionary for the query
    dict = {}

    # If a match was found, split the clause into its components and add them to the dictionary
    if select_match:
        select_clause = select_match.group(1).strip().split(',')

        for i in range(len(select_clause)):
            select_clause[i] = select_clause[i].strip()

        dict['SELECT'] = select_clause
        
    if from_match:
        from_clause = from_match.group(1).strip().split(',')
        
        for i in range(len(from_clause)):
            from_clause[i] = from_clause[i].strip()
        
        dict['FROM'] = from_clause

    if where_match:
        where_clause = where_match.group(1).strip().split('and')

        for i in range(len(where_clause)):
            where_clause[i] = " ".join(where_clause[i].split())

        dict['WHERE'] = where_clause

    if group_by_match:
        group_by_clause = group_by_match.group(1).strip().split(',')

        for i in range(len(group_by_clause)):
            group_by_clause[i] = group_by_clause[i].strip()
        
        dict['GROUP BY'] = group_by_clause

    if having_match:
        having_clause = having_match.group(1).strip().split(',')

        for i in range(len(having_clause)):
            having_clause[i] = having_clause[i].strip()
        
        dict['HAVING'] = having_clause
    
    
    if order_by_match:
        order_by_clause = order_by_match.group(1).strip().split(',')

        for i in range(len(order_by_clause)):
            order_by_clause[i] = order_by_clause[i].strip()

        dict['ORDER BY'] = order_by_clause
    
    if limit_match:
        limit_clause = limit_match.group(1).strip().split(',')

        for i in range(len(limit_clause)):
            limit_clause[i] = limit_clause[i].strip()

        dict['LIMIT'] = limit_clause

    return dict 


def query_compare(query1, query2):

    query_1_dict = parse_sql_query(query1)
    query_2_dict = parse_sql_query(query2)

    # Just for testing purposes, simpler to see
    query_1_dict = {
        'SELECT': ['column1', 'column2', 'column3'],
        'FROM': ['table1', 'table2', 'table3'],
        'WHERE': ['column1 > 10', 'column2 = "example"'],
        'GROUP BY': ['column1', 'column2'],
        'ORDER BY': ['column1 DESC', 'column2 ASC']
    }

    query_2_dict = {
        'SELECT': ['column1', 'column3'],
        'FROM': ['table1', 'table3'],
        'GROUP BY': ['column1', 'column2'],
        'ORDER BY': ['column1 DESC', 'column3 ASC'],
        'LIMIT': ['100']
    }

    for key in ['SELECT', 'FROM', 'WHERE', 'GROUP BY', 'HAVING', 'ORDER BY', 'LIMIT']:
        # Case 1: key exists in both queries
        if key in query_1_dict and key in query_2_dict:
            # Case 1.1: value in key is unchanged
            if query_1_dict[key] == query_2_dict[key]:
                print(f"\nPredicates for the {key} clause remained the same")
            # Case 1.2: value in key has changed
            else:
                old_value = query_1_dict[key]
                new_value = query_2_dict[key]
                present_in_old_not_new = []
                present_in_new_not_old = []
                # Iterate over each element in the old and new values
                for i, elem in enumerate(old_value):
                    # Check if the element was present in the new value
                    if elem not in new_value:
                        present_in_old_not_new.append(f"{elem}")
                for i, elem in enumerate(new_value):
                    # Check if the element was present in the old value
                    if elem not in old_value:
                        present_in_new_not_old.append(f"{elem}")
                
                changes = []
                if present_in_old_not_new:
                    changes.append("Was present in Query 1 but not Query 2: " + ", ".join(present_in_old_not_new))
                if present_in_new_not_old:
                    changes.append("Was not present in Query 1 but is now present in Query 2: " + ", ".join(present_in_new_not_old))
                print(f"\nPredicates for the {key} clause have changed:")
                if changes:
                    for change in changes:
                        print(change)

        # Case 2: keys not present in one of the two
        else:
            # Case 2.1: key present in query1 but not query2
            if key in query_1_dict and key not in query_2_dict:
                print(f"\nThe {key} clause was present in Query 1 but is now not present in Query 2")
            # Case 2.2: key present in query2 but not query1
            if key in query_2_dict and key not in query_1_dict:
                print(f"\nThe {key} clause was not present in Query 1 but is now present in Query 2")


if __name__ == "__main__":

    # query1 and query2 should be taken from front-end user input, presumably same input for the qep generation
    query1 = "SELECT\
        c_custkey,\
        c_name,\
        sum(l_extendedprice * (1 - l_discount)) as revenue,\
        c_acctbal,\
        n_name,\
        c_address,\
        c_phone,\
        c_comment\
    FROM\
        customer,\
        orders,\
        lineitem,\
        nation\
    WHERE\
        c_custkey = o_custkey\
        and l_orderkey = o_orderkey\
        and o_orderdate >= date ':1'\
        and o_orderdate < date ':1' + interval '3' month\
        and l_returnflag = 'R'\
        and c_nationkey = n_nationkey\
    GROUP BY\
        c_custkey,\
        c_name,\
        c_acctbal,\
        c_phone,\
        n_name,\
        c_address,\
        c_comment\
    ORDER BY\
        revenue desc;\
    "

    # Changed select, where, group by
    # Need to test diff number of clauses too
    query2 = "SELECT\
        n_name,\
        c_address,\
        c_phone,\
        c_comment\
    FROM\
        customer,\
        orders,\
        lineitem,\
        nation\
    WHERE\
        and l_returnflag = 'R'\
        and c_nationkey = n_nationkey\
    GROUP BY\
        n_name,\
        c_address,\
        c_comment\
    ORDER BY\
        revenue desc;\
    "

    query_compare(query1, query2)











































