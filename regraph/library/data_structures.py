"""Define data structures used by graph rewriting tool."""
import copy

import networkx as nx

from regraph.library.utils import (is_subdict,
                                   keys_by_value,
                                   valid_attributes)


def is_valid_homomorphism(source,
                          target,
                          dictionary,
                          ignore_types=False,
                          ignore_attrs=False):
    """Check if the homomorphism is valid (preserves edges,
    preserves types and attributes if requires)."""

    # check if there is mapping for all the nodes of source graph
    if set(source.nodes()) != set(dictionary.keys()):
        raise ValueError(
            "Invalid homomorphism: Mapping is not covering all the nodes of source graph!")
    if not set(dictionary.values()).issubset(target.nodes()):
        raise ValueError(
            "invalid homomorphism: image not in target graph"
        )

    # check connectivity
    for s_edge in source.edges():
        if not (dictionary[s_edge[0]], dictionary[s_edge[1]]) in target.edges():
            if not target.is_directed():
                if not (dictionary[s_edge[1]], dictionary[s_edge[0]]) in target.edges():
                    raise ValueError(
                        "Invalid homomorphism: Connectivity is not preserved!" +\
                        " Was expecting an edge %s->%s" %
                        (dictionary[s_edge[1]], dictionary[s_edge[0]]))
            else:
                raise ValueError(
                    "Invalid homomorphism: Connectivity is not preserved!" +\
                    " Was expecting an edge between %s and %s" %
                    (dictionary[s_edge[0]], dictionary[s_edge[1]]))
    # check nodes match with types
    for s, t in dictionary.items():
        if not ignore_types:
            if (source.node[s].type_ is not None) and\
               (source.node[s].type_ != target.node[t].type_):
                raise ValueError(
                    "Invalid homomorphism: Node types do not match (%s:%s and %s:%s)!" %
                    (s, str(source.node[s].type_), str(t), str(target.node[t].type_)))
        if not ignore_attrs:
            # check sets of attributes of nodes (here homomorphism = set inclusion)
            if type(source.node[s]) == dict:
                source_attrs = source.node[s]
            else:
                source_attrs = source.node[s].attrs_
            if type(target.node[t]) == dict:
                target_attrs = target.node[t]
            else:
                target_attrs = target.node[t].attrs_
            if not valid_attributes(source_attrs, target_attrs):
                raise ValueError(
                    "Invalid homomorphism: Attributes of nodes source:'%s' and target:'%s' do not match!" %
                    (str(s), str(t)))

    if not ignore_attrs:
        # check sets of attributes of edges (homomorphism = set inclusion)
        for s1, s2 in source.edges():
            try:
                source_edge_attrs = source.edge.get_edge(s1, s2)
            except:
                source_edge_attrs = source.edge[s1][s2]
            try:
                target_edge_attrs = target.get_edge(dictionary[s1],
                                                    dictionary[s2])
            except:
                target_edge_attrs = target.edge[dictionary[s1]][dictionary[s2]]
            if not is_subdict(source_edge_attrs, target_edge_attrs):
                raise ValueError(
                    "Invalid homomorphism: Attributes of edges (%s)-(%s) and (%s)-(%s) do not match!" %
                    (s1, s2, dictionary[s1],
                        dictionary[s2]))
    return True


def compose_homomorphisms(hom1, hom2):
    # Strategy: if hom1 and hom2
    # are typing homomorphisms or one of them is typing and
    # another is type-preserving, we construct a new typing
    # homomorphism and convert the node types to the
    # corresponding new types. Otherwise we create
    # a homomorphism which is a composition of
    # the previous two (hom2 * hom1)
    source = copy.deepcopy(hom1.source_)
    converted_types = {}

    if type(hom1) == TypingHomomorphism:
        if type(hom2) == TypingHomomorphism:
            # change the types of the newly typed graphs
            for new_type in hom2.target_.nodes():
                old_types = keys_by_value(
                    hom2.mapping_,
                    new_type
                )
                for t in old_types:
                    source.convert_type(t, new_type)
                    converted_types.update({t: new_type})
            # update meta-model of the corresponding graph
            source.update_metamodel(hom2.target_)
            composed_hom = TypingHomomorphism(
                source,
                hom2.target_,
                ignore_attrs=(hom1.ignore_attrs or hom2.ignore_attrs)
            )
        else:
            if hom2.ignore_types is False:
                # change the types of the newly typed graphs
                for new_type in hom2.target_.nodes():
                    old_types = keys_by_value(
                        hom2.mapping_,
                        new_type
                    )
                    for t in old_types:
                        source.convert_type(t, new_type)
                        converted_types.update({t: new_type})
                # update meta-model of the corresponding graph
                source.update_metamodel(hom2.target_)
                composed_hom = TypingHomomorphism(
                    source,
                    hom2.target_,
                    ignore_attrs=(hom1.ignore_attrs or hom2.ignore_attrs)
                )
            else:
                mapping = dict(
                    [(key, hom2.mapping_[value]) for key, value in hom1.mapping_.items()]
                )
                composed_hom = Homomorphism(
                    source,
                    hom2.target_,
                    mapping,
                    ignore_types=True,
                    ignore_attrs=(hom1.ignore_attrs or hom2.ignore_attrs)
                )
    else:
        if type(hom2) == TypingHomomorphism:
            if hom1.ignore_types is False:
                # change the types of the newly typed graphs
                for new_type in hom2.target_.nodes():
                    old_types = keys_by_value(
                        hom2.mapping_,
                        new_type
                    )
                    for t in old_types:
                        source.convert_type(t, new_type)
                        converted_types.update({t: new_type})
                # update meta-model of the corresponding graph
                source.update_metamodel(hom2.target_)
                composed_hom = TypingHomomorphism(
                    source,
                    hom2.target_,
                    ignore_attrs=(hom1.ignore_attrs or hom2.ignore_attrs)
                )
            else:
                mapping = dict(
                    [(key, hom2.mapping_[value]) for key, value in hom1.mapping_.items()]
                )
                composed_hom = Homomorphism(
                    source,
                    hom2.target_,
                    mapping,
                    ignore_types=True,
                    ignore_attrs=(hom1.ignore_attrs or hom2.ignore_attrs)
                )
        else:
            mapping = dict(
                [(key, hom2.mapping_[value]) for key, value in hom1.mapping_.items()]
            )
            composed_hom = Homomorphism(
                source,
                hom2.target_,
                mapping,
                ignore_types=True,
                ignore_attrs=(hom1.ignore_attrs or hom2.ignore_attrs)
            )
    return (composed_hom, converted_types)


class Homomorphism(object):
    """Define graph homomorphism data structure."""

    def __init__(self, source, target, dictionary, ignore_types=False, ignore_attrs=False):
        if is_valid_homomorphism(source, target, dictionary, ignore_types, ignore_attrs):
            self.source_ = source
            self.target_ = target
            self.mapping_ = dictionary
            self.ignore_types = ignore_types
            self.ignore_attrs = ignore_attrs
        else:
            raise ValueError("Homomorphism is not valid!")

    def __str__(self):
        return "Source :\n%sTarget :\n%sMapping :\n%s" % \
            (str(self.source_), str(self.target_), str(self.mapping_))

    def __getitem__(self, index):
        return self.mapping_.__getitem__(index)

    def __setitem__(self, index, value):
        self.mapping_.__setitem__(index, value)

    def __delitem__(self, index):
        self.mapping_.__delitem__(index)

    def __len__(self):
        return self.mapping_.__len__()

    def __missing__(self, index):
        self.mapping_.__missing__(index)

    def is_monic(self):
        """Check if the homomorphism is monic."""
        return len(set(self.mapping_.keys())) ==\
            len(set(self.mapping_.values()))

    @staticmethod
    def identity(a, b, ignore_types=False, ignore_attrs=False):
        """ Tries to create the identity homomorphism of A from A to B,
            fails if some nodes of A aren't found in B
        """
        dic = {}
        for n in a.nodes():
            if n in b.nodes():
                dic[n] = n
            else:
                raise ValueError(
                    "Node %s not found in the second graph" % n
                )
        return Homomorphism(a, b, dic, ignore_types, ignore_attrs)

    @staticmethod
    def compose(h1, h2):
        """ Returns h1.h2 : A -> C given h1 : B -> C and h2 : A -> B"""
        return Homomorphism(
            h2.source_,
            h1.target_,
            dict([(n, h1.mapping_[h2.mapping_[n]]) for n in h2.mapping_.keys()]),
        )


class TypingHomomorphism(Homomorphism):
    """This class implements a typing homomorphism: e.g. node_name:type_name -> type_name:meta_type_name"""
    def __init__(self, source, target, ignore_attrs=False):
        dictionary = {n: source.node[n].type_ for n in source.nodes()}
        if is_valid_homomorphism(
            source,
            target,
            dictionary,
            ignore_types=True,
            ignore_attrs=ignore_attrs,
        ):
            # check that types of the nodes in the source
            # match id of the nodes in the target
            for s, t in dictionary.items():
                if (source.node[s].type_ is not None) and\
                   (source.node[s].type_ != t):
                    raise ValueError(
                        "Invalid homomorphism: Node types do not form a chain (%s:%s and %s:%s)!" %
                        (s, str(source.node[s].type_), str(t), str(target.node[t].type_)))
            self.source_ = source
            self.target_ = target
            self.mapping_ = dictionary
            self.ignore_attrs = ignore_attrs
        else:
            raise ValueError("TypingHomomorphism is not valid!")


class Hierarchy(nx.DiGraph):
    """."""
    def __init__(self, directed=True):
        nx.DiGraph.__init__(self)
        self.hierarchy_attrs = dict()
        self.directed = directed
        return

    def __str__(self):
        res = ""
        res += "\nGraphs (directed == %s): \n" % self.directed
        for n in self.nodes():
            res += str(n) + " "
        res += "\n"
        res += "Homomorphisms : \n"
        for n1, n2 in self.edges():
            res +=\
                str((n1, n2))
            if type(self.edge[n1][n2]) == TypingHomomorphism:
                res += " : typing homomorphism, "
            else:
                res += " : ignore_types == %s, " %\
                    str(self.edge[n1][n2].ignore_types)

            res += "ignore_attrs == " +\
                str(self.edge[n1][n2].ignore_attrs) +\
                "\n"
        res += "\n"
        res += "attributes : \n"
        res += str(self.hierarchy_attrs)
        res += "\n"

        return res

    def add_graph(self, graph_id, graph):
        """Add graph to the hierarchy."""
        if self.directed != graph.is_directed():
            if self.directed:
                raise ValueError("Hierarchy is defined for directed graphs!")
            else:
                raise ValueError("Hierarchy is defined for undirected graphs!")
        self.add_node(graph_id)
        self.node[graph_id] = copy.deepcopy(graph)
        return

    def add_homomorphism(self,
                         source_id,
                         target_id,
                         mapping=None,
                         typing=False,
                         ignore_types=False,
                         ignore_attrs=False):
        """Add homomorphism to the hierarchy."""
        if source_id not in self.nodes():
            raise ValueError(
                "Graph %s is not defined in the hierarchy!" % source_id)
        if target_id not in self.nodes():
            raise ValueError(
                "Graph %s is not defined in the hierarchy!" % target_id)
        if typing:
            homomorphism = TypingHomomorphism(
                self.node[source_id],
                self.node[target_id],
                ignore_attrs=ignore_attrs
            )
        else:
            if mapping:
                homomorphism = Homomorphism(
                    self.node[source_id],
                    self.node[target_id],
                    mapping,
                    ignore_types=ignore_types,
                    ignore_attrs=ignore_attrs
                )
            else:
                # If mapping is not specified -- try to create identity
                homomorphism = Homomorphism.identity(
                    self.node[source_id],
                    self.node[target_id],
                    ignore_types=ignore_types,
                    ignore_attrs=ignore_attrs
                )
        self.add_edge(source_id, target_id)
        self.edge[source_id][target_id] = homomorphism
        return

    def remove_graph(self, graph_id, reconnect=False):
        """Remove graph from the hierarchy and map the children
           homomorphisms of this graph to its parents."""
        if graph_id not in self.nodes():
            raise ValueError(
                "Graph %s is not defined in the hierarchy!" % graph_id)

        if reconnect:
            pass
            # out_graphs = self.successors(graph_id)
            # in_graphs = self.predecessors(graph_id)

            # updated_nodes = set(out_graphs + [graph_id] + in_graphs)
            # edges_to_add = dict()
            # for source in in_graphs:
            #     for target in out_graphs:

            #         # compose two homomorphisms
            #         (new_homomorphism, converted_types) = compose_homomorphisms(
            #             self.edge[source][graph_id],
            #             self.edge[graph_id][target]
            #         )

            #         # update a source graph
            #         self.node[source] = new_homomorphism.source_

            #         # BFS for updates in the graphs
            #         if converted_types:
            #             updated_nodes.add(source)
            #             for u, v in nx.bfs_edges(self, source):
            #                 if u in updated_nodes and v not in updated_nodes:
            #                     if type(self.edge[u][v]) == Homomorphism:
            #                         if self.edge[u][v].ignore_types is False:
            #                             for old, new in converted_types.items():
            #                                 self.node[v].convert_type(old, new)
            #                                 updated_nodes.add(v)
            #                 elif u not in updated_nodes and v in updated_nodes:
            #                     if type(self.edge[u][v]) == Homomorphism:
            #                         if self.edge[u][v].ignore_types is False:
            #                             for old, new in converted_types.items():
            #                                 self.node[u].convert_type(old, new)
            #                                 updated_nodes(u)

            #         # Add edges corresponding to constructed homomorphisms
            #         edges_to_add[(source, target)] = new_homomorphism

            # for edge, hom in edges_to_add.items():
            #     if (edge[0], edge[1]) not in self.edges():
            #         print(edge[0], edge[1])
            #         print(hom)
            #         self.add_edge(edge[0], edge[1])
            #         self.edge[edge[0]][edge[1]] = hom

        self.remove_node(graph_id)
