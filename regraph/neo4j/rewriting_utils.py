import regraph.neo4j.cypher_utils as cypher


def propagate_up(rewritten_graph, predecessor):
    """Generate the queries for propagating the changes up from H-->G.

    Returns
    -------
    query1 : str
        Generated query for cloning nodes in H
    query2 : str
        Generated query for removing nodes from H
    query3 : str
        Generated query for removing nodes from H
    """
    # We clone the nodes that have more than 1 image and
    # reassign the typing edges
    carry_vars = set()
    query1 = (
        "// Matching of the nodes to clone in '{}'\n".format(predecessor) +
        "OPTIONAL MATCH (node_to_clone:node:{})-[t:typing]->(n:node:{})\n".format(
            predecessor, rewritten_graph) +
        "WITH node_to_clone, collect(n) as sucs, collect(t) as typ_sucs, "
        "size(collect(n)) as number_of_img\n" +
        "WHERE number_of_img >= 2 AND node_to_clone IS NOT NULL\n"
        )
    query1 += (
        "FOREACH(t IN typ_sucs | DELETE t)\n" +
        "WITH node_to_clone, sucs, number_of_img-1 as number_of_clone\n"
        )
    carry_vars.update(['node_to_clone', 'sucs'])
    query1 += (
        cypher.multiple_cloning_query(
                    original_var='node_to_clone',
                    clone_var='cloned_node',
                    clone_id='clone_id',
                    clone_id_var='clone_id',
                    number_of_clone_var='number_of_clone',
                    node_label='node:'+predecessor,
                    preserv_typing=True,
                    carry_vars=carry_vars,
                    ignore_naming=True,
                    multiple_rows=True)[0]
    )
    carry_vars.difference_update(['cloned_node', 'clone_id'])
    query1 += (
        "WITH collect(cloned_node)+[node_to_clone] as nodes_to_typ, " +
        "collect(clone_id) as clone_ids, " +
        ", ".join(carry_vars) + "\n" +
        "FOREACH (i IN range(0, size(sucs)-1) |\n" +
        "\tFOREACH(source in [nodes_to_typ[i]] |\n"
        "\t\tFOREACH(target in [sucs[i]] |\n"
        "\t\t\t" + cypher.create_edge(
                    edge_var='restored_typing',
                    source_var='source',
                    target_var='target',
                    edge_label='typing') + ")))\n"
        )
    query1 += "RETURN clone_ids"

    # We remove the nodes of H without image in G
    query2 = (
        "// Removal of nodes in '{}'\n".format(predecessor) +
        "OPTIONAL MATCH (n:node:{})\n".format(predecessor) +
        "WHERE NOT (n)-[:typing]->(:node:{})\n".format(rewritten_graph) +
        "DETACH DELETE n\n\n"
        )

    # We remove the edges without image in G
    query3 = (
        "// Removal of edges in '{}'\n".format(predecessor) +
        "OPTIONAL MATCH (n:node:{})-[rel_pred:edge]->(m:node:{})\n".format(
            predecessor, predecessor) +
        "OPTIONAL MATCH (n)-[:typing]->(:node:{})-[rel:edge]->(:node:{})<-[:typing]-(m)\n".format(
            rewritten_graph, rewritten_graph) +
        "WITH rel_pred WHERE rel IS NULL\n" +
        "WITH DISTINCT rel_pred\n" +
        "DELETE rel_pred\n\n"
        )

    return query1, query2, query3


def propagate_up_v2(rewritten_graph, predecessor):
    """Generate the queries for propagating the changes up from H-->G.

    Returns
    -------
    query : str
        Generated query for propagating the changes down
    """
    # We remove the nodes of H without image in G
    query = (
        "// Removal of nodes in '{}'\n".format(predecessor) +
        "OPTIONAL MATCH (n:node:{})\n".format(predecessor) +
        "WHERE NOT (n)-[:typing]->(:node:{})\n".format(rewritten_graph) +
        "DETACH DELETE n\n\n" +
        "WITH DISTINCT [] as removed_nodes\n"
    )

    # We remove the edges without image in G
    query += (
        "\n// Removal of edges in '{}'\n".format(predecessor) +
        "OPTIONAL MATCH (n:node:{})-[rel_pred:edge]->(m:node:{})\n".format(
            predecessor, predecessor) +
        "WHERE NOT (n)-[:typing]->(:node:{})-[:edge]->(:node:{})<-[:typing]-(m)\n".format(
            rewritten_graph, rewritten_graph) +
        "DELETE rel_pred\n" +
        "WITH DISTINCT [] as removed_edges\n"
    )

    # We clone the nodes that have more than 1 image and
    # reassign the typing edges
    carry_vars = set()
    query += (
        "// Matching of the nodes to clone in '{}'\n".format(predecessor) +
        "OPTIONAL MATCH (node_to_clone:node:{})-[t:typing]->(n:node:{})\n".format(
            predecessor, rewritten_graph) +
        "WITH node_to_clone, collect(n) as sucs, collect(t) as typ_sucs, "
        "size(collect(n)) as number_of_img\n" +
        "WHERE number_of_img >= 2 AND node_to_clone IS NOT NULL\n"
        )
    query += (
        "FOREACH(t IN typ_sucs | DELETE t)\n" +
        "WITH node_to_clone, sucs, number_of_img-1 as number_of_clone\n"
        )
    carry_vars.update(['node_to_clone', 'sucs'])
    query += (
        cypher.multiple_cloning_query(
                    original_var='node_to_clone',
                    clone_var='cloned_node',
                    clone_id='clone_id',
                    clone_id_var='clone_id',
                    number_of_clone_var='number_of_clone',
                    node_label='node:'+predecessor,
                    preserv_typing=True,
                    carry_vars=carry_vars,
                    ignore_naming=True,
                    multiple_rows=True)[0]
    )
    carry_vars.difference_update(['cloned_node', 'clone_id'])
    query += (
        "WITH collect(cloned_node)+[node_to_clone] as nodes_to_typ, " +
        "collect(clone_id) as clone_ids, " +
        ", ".join(carry_vars) + "\n" +
        "FOREACH (i IN range(0, size(sucs)-1) |\n" +
        "\tFOREACH(source in [nodes_to_typ[i]] |\n"
        "\t\tFOREACH(target in [sucs[i]] |\n"
        "\t\t\t" + cypher.create_edge(
                    edge_var='restored_typing',
                    source_var='source',
                    target_var='target',
                    edge_label='typing') + ")))\n"
        )
    query += "RETURN clone_ids"

    return query


def propagate_down(rewritten_graph, successor):
    """Generate the queries for propagating the changes down from G-->T.

    Returns
    -------
    query1 : str
        Generated query for merging nodes in H
    query2 : str
        Generated query for adding nodes in T
    query3 : str
        Generated query for adding edges in T
    """
    # add nodes in T for each node without image in G
    carry_vars = set()

    # match nodes of T with the same pre-image in G and merge them
    carry_vars.add('merged_nodes')
    query1 = (
        "\n// Matching of the nodes to merge in '{}'\n".format(successor) +
        "WITH [] as merged_nodes\n"
        "OPTIONAL MATCH (n:node:{})-[:typing]->(node_to_merge:node:{})\n".format(
            rewritten_graph, successor) +
        "WITH n, collect(node_to_merge) as nodes_to_merge, " +
        ", ".join(carry_vars) + "\n"
        "WHERE n IS NOT NULL AND size(nodes_to_merge) >= 2\n" 
    )
    carry_vars.add('n')
    carry_vars.add('nodes_to_merge')
    query1 += (
        cypher.merging_from_list(
                        list_var='nodes_to_merge',
                        merged_var='merged_node',
                        merged_id='id',
                        merged_id_var='merged_id',
                        node_label='node:'+successor,
                        edge_label='edge',
                        merge_typing=True,
                        carry_vars=carry_vars,
                        ignore_naming=True,
                        multiple_rows=True,
                        multiple_var='n')[0]
        )
    carry_vars.remove('merged_node')
    carry_vars.remove('merged_id')
    query1 += "RETURN collect(merged_id) as merged_nodes"

    carry_vars = set()

    query2 = (
        "// Addition of nodes in '{}'\n".format(successor) +
        "OPTIONAL MATCH (n:node:{})".format(rewritten_graph) +
        "WHERE NOT (n)-[:typing]->(:node:{})\n".format(successor) +
        "WITH n WHERE n IS NOT NULL\n" +
        "MERGE (n)-[:typing]->(new_node:node:{})\n".format(successor) +
        "ON CREATE SET new_node += properties(n)\n" +
        "ON CREATE SET new_node.id = toString(id(new_node))\n"
        )
    query2 += "RETURN collect(new_node.id) as added_nodes\n"

    # add edges in T for each edge without image in G
    query3 = (
        "\n// Addition of edges in '{}'\n".format(successor) +
        "OPTIONAL MATCH (n:node:{})-[rel:edge]->(m:node:{})\n".format(
            rewritten_graph, rewritten_graph) +
        "WHERE {source: n.id, target:m.id} IN $added_edges_list\n" +
        "WITH n, m, rel WHERE n IS NOT NULL AND m IS NOT NULL\n" +
        "OPTIONAL MATCH (n)-[:typing]->(x:node:{}), (m)-[:typing]->(y:node:{})\n".format(
            successor, successor) +
        "MERGE (x)-[rel_img:edge]->(y)\n"
    )
    carry_vars.update(['x', 'y'])
    query3 += (
        cypher.merge_properties(
                    var_list=['rel', 'rel_img'],
                    new_props_var='new_props',
                    carry_vars=carry_vars) +
        "SET rel_img += new_props\n"
        )
    query3 += "RETURN collect({source:x.id, target:y.id}) as added_edges\n"

    return query1, query2, query3


def propagate_down_v2(rewritten_graph, successor):
    """Generate the query for propagating the changes down from G-->T.

    Returns
    -------
    query : str
        Generated query for propagating the changes down
    """
    carry_vars = set()

    query = (
        "// Addition of nodes in '{}'\n".format(successor) +
        "OPTIONAL MATCH (n:node:{})\n".format(rewritten_graph) +
        "WHERE NOT (n)-[:typing]->(:node:{})\n".format(successor) +
        "FOREACH(dumy IN CASE WHEN n IS NOT NULL THEN [1] ELSE [] END |\n"
        "\tMERGE (n)-[:typing]->(new_node:node:{})\n".format(successor) +
        "\tON CREATE SET new_node += properties(n)\n" +
        "\tON CREATE SET new_node.id = toString(id(new_node)))\n"
        )
    query += "WITH collect(n.id) as added_nodes\n"

    # add edges in T for each edge without image in G
    query += (
        "\n// Addition of edges in '{}'\n".format(successor) +
        "OPTIONAL MATCH (n:node:{})-[rel:edge]->(m:node:{})\n".format(
            rewritten_graph, rewritten_graph) +
        "WHERE {source: n.id, target:m.id} IN $added_edges_list\n" +
        "OPTIONAL MATCH (n)-[:typing]->(x:node:{}), (m)-[:typing]->(y:node:{})\n".format(
            successor, successor)
    )
    carry_vars.update(['x', 'y', 'rel'])
    query += (
        "FOREACH(dumy IN CASE WHEN rel IS NOT NULL THEN [1] ELSE [] END |\n"
        "\tMERGE (x)-[rel_img:edge]->(y))\n" +
        "WITH " + ", ".join(carry_vars) + "\n" +
        "OPTIONAL MATCH (x)-[rel_img:edge]->(y)\n" +
        cypher.merge_properties(
                    var_list=['rel', 'rel_img'],
                    new_props_var='new_props',
                    carry_vars=carry_vars) +
        "FOREACH(dumy IN CASE WHEN rel_img IS NOT NULL THEN [1] ELSE [] END |\n"
        "\tSET rel_img += new_props)\n"
        )
    carry_vars.difference_update(['rel', 'rel_img', 'x', 'y', 'new_props'])
    query += (
        "WITH collect({source: x.id, target:y.id}) as added_edges\n"
    )
    carry_vars.add('added_edges')

    # match nodes of T with the same pre-image in G and merge them
    query += (
        "\n// Matching of the nodes to merge in '{}'\n".format(successor) +
        "OPTIONAL MATCH (n:node:{})-[:typing]->(node_to_merge:node:{})\n".format(
            rewritten_graph, successor) +
        "WITH n, collect(node_to_merge) as nodes_to_merge, " +
        ", ".join(carry_vars) + "\n"
        "WHERE n IS NOT NULL AND size(nodes_to_merge) >= 2\n"
    )
    carry_vars.add('n')
    carry_vars.add('nodes_to_merge')
    query += (
        cypher.merging_from_list(
                        list_var='nodes_to_merge',
                        merged_var='merged_node',
                        merged_id='id',
                        merged_id_var='merged_id',
                        node_label='node:'+successor,
                        edge_label='edge',
                        merge_typing=True,
                        carry_vars=carry_vars,
                        ignore_naming=True,
                        multiple_rows=True,
                        multiple_var='n')[0]
        )
    carry_vars.remove('merged_node')
    carry_vars.remove('merged_id')
    query += (
        "WITH collect('merged_id') as merged_nodes, " +
        ", ".join(carry_vars) + "\n" +
        "RETURN added_edges\n"
    )

    return query
