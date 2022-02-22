"""
@author Flavius Abel Ciapsa, and Jorge Boticario Figueras
@licence MIT
"""

from nltk.corpus import wordnet as wn
import networkx as nx
import matplotlib.pyplot as plt
import json

# This class represents a node of a concept graph.
class ConceptNode:
    siguiente_id = 1

    # param 'descriptors': a set of synonyms
    # param 'name': the name of a WordNet synset which contains these synonyms
    def __init__(self, descriptors, name):
        self.id_networkx = ConceptNode.siguiente_id
        ConceptNode.siguiente_id += 1
        if not ConceptNode.valid_types(descriptors, name):
            raise Exception("ConceptNode constructor: invalid argument type")
        try:
            if not ConceptNode.valid_args(descriptors, name):
                raise Exception("ConceptNode constructor: invalid argument")
        except:
            raise Exception("ConceptNode constructor:" + name + " is not the name of a WordNet synset")
        else:
            #serialization to JSON cannot work with sets
            self.descriptors = list(descriptors)
            self.synset_name = name

    @staticmethod
    def valid_types(descriptors, name):
        return len(descriptors) != 0 \
                and type(name) == str and type(descriptors) == set \
                and all(map(lambda x: type(x) == str, list(descriptors)))

    @staticmethod
    # Exception on executing wn.synset(name) if 'name' is not that of a WordNet synset
    # wn.synsets(descriptor) evaluates to an empty list if descriptor not in WordNet
    def valid_args(descriptors, name):
        return len(descriptors) != 0\
                and wn.synset(name).pos() == 'n' \
                and all(map(lambda x: len(wn.synsets(x)) != 0 and wn.synset(name) in wn.synsets(x), list(descriptors)))

    # If all nodes are created using the methods defined here it is not possible
    # to create invalid nodes, so this method is not really necessary
    def is_valid(self):
        return ConceptNode.valid_types(self.descriptors, self.synset_name) \
               and ConceptNode.valid_args(self.descriptors, self.synset_name)

    # Alternative constructor attempts to create a new node from a descriptor
    # Exception with informative message if descriptor is a member of multiple WordNet synsets
    @classmethod
    def from_descriptor(cls, descriptor):
        synsets = wn.synsets(descriptor)
        num_synsets = len(synsets)
        if num_synsets == 0:
            # descriptors that are not in Wordnet are currently not allowed
            raise Exception("from_descriptor:" + descriptor + "not found in Wordnet")
        elif num_synsets == 1:
            name = synsets[0].name()
        else:
            all_synonyms = []
            for synset in synsets:
                synonyms = []
                for lemma_name in synset.lemma_names():
                    synonyms.append(lemma_name)
                all_synonyms.append(synset.name() + ": " + ", ".join(synonyms))
            message = "\n".join(all_synonyms)
            raise Exception("from_descriptor:" + descriptor + "has multiple meanings." \
                            + "Please create node using one of the following synset names:\n " \
                            + message)
        return cls({descriptor}, name)

    # Adds a new synonym to the current node
    # Exception if the new descriptor is not a synonym of the existing node descriptors
    def add_descriptor(self, descriptor):
        # Recall that self.descriptors is a list not a set
        if descriptor in self.descriptors:
            pass  # si descriptor ya presente, no hacer nada
        elif self.valid_add_descriptor(descriptor):
            self.descriptors.add(descriptor)

    def valid_add_descriptor(self, descriptor):
        if wn.synset(self.synset_name) not in wn.synsets(descriptor):
            raise Exception("valid_add_descriptor:" + descriptor + "not a synonym")
        return True

    def __str__(self):
        return str(self.id_networkx) + "( " + str(self.descriptors) + ", " + self.synset_name + " )"

    # Checks that the attributes are equal
    def __eq__(self,other):
        if isinstance(other, ConceptNode):
            return self.descriptors == other.descriptors and \
                   self.synset_name == other.synset_name
        else:
            return NotImplemented

    def __contains__(self,elem):
        contains = False
        if type(elem) == str:
            # string has syntax of a synset_name
            if len(elem.split('.')) == 3:
                contains = (elem == self.synset_name)
            else:
                contains = (elem in self.descriptors)
        return contains

    def __hash__(self):
        return hash(self.id_networkx)

# This class represents an edge of a concept graph.
class ConceptEdge:

    def __init__(self, node1, node2, info=None):
        if not isinstance(node1, ConceptNode) \
                or not isinstance(node2, ConceptNode):
            raise Exception("ConceptEdge constructor: invalid argument type")
        self.source = node1
        self.target = node2
        self.label = info

    def __str__(self):
        return str(self.source) + " --> " + str(self.target)

    def __eq__(self,other):
        if isinstance(other, ConceptEdge):
            return self.source == other.source and \
                   self.target == other.target and \
                   self.label == other.label if self.label is not None else True
        else:
            return NotImplemented

    def __contains__(self, elem):
        if type(elem) == ConceptNode:
            return elem == self.source or elem == self.target
        else:  # todavía no se ha definido un tipo para labels
            return elem == self.label

    def __hash__(self):
        return hash((self.source, self.target))


# This class is used to represent concept graphs
# A ConceptGraph object is currently a wrapper for a NetworkX DiGraph
class ConceptGraph:

    def __init__(self, nodes=set(), edges=set(), graph=nx.DiGraph()):
        self.nodes = nodes
        self.edges = edges
        self.graph = graph

    @classmethod
    def getNodeFromId(self, id_networkx, a_nodeset):
        for x in a_nodeset:
            if id_networkx == x.id_networkx:
                return x

    @classmethod
    def from_json(cls, json_data):
        # Read jason_data into a networkx graph
        # Create an empty ConceptGraph:
        netx_graph = nx.readwrite.json_graph.node_link_graph(json.loads(json_data), directed=True, multigraph=False)
        node_set = set()
        edge_set = set()

        for x in netx_graph.nodes:
            json_data = dict(netx_graph.nodes[x])
            d = json_data['descriptors']
            s = json_data['synset_name']
            new_node = ConceptNode(set(d), s)
            node_set.add(new_node)

        for x in netx_graph.edges:
            source = cls.getNodeFromId(x[0], node_set)
            target = cls.getNodeFromId(x[1], node_set)
            new_edge = ConceptEdge(source, target)
            edge_set.add(new_edge)

        return cls(node_set,edge_set,netx_graph)

    def write_to_json(self):
        # Write the wrapped networkx graph to json
        c = json.dumps(nx.readwrite.json_graph.node_link_data(self.graph))
        with open('networkdata10.json', 'w') as outfile1:
            outfile1.write(c)

    # Adds the node 'new_node' to the current graph
    def add_node(self, new_node):
        if self.valid_graph_node(new_node):
            self.graph.add_node(new_node.id_networkx, **new_node.__dict__)
            self.nodes.add(new_node)

    # Checks whether 'new_node' can be added to the current graph
    def valid_graph_node(self, new_node):
        if not isinstance(new_node, ConceptNode):
            raise Exception("valid_graph_node: invalid argument type")
        for descriptor in new_node.descriptors:
            if descriptor in self.graph:        # ************** NEEDS __contains__
                raise Exception("valid_graph_node: new node already in graph")
        if new_node.synset_name in self.graph:  # ************** NEEDS __contains__
            raise Exception("valid_graph_node: synonym of new node already in graph")
        return True

    # Adds the edge 'new_edge' to the current graph
    def add_edge(self, new_edge):
        if self.valid_graph_edge(new_edge):
            self.graph.add_edge(new_edge.source.id_networkx, new_edge.target.id_networkx)

        if len(list(enumerate(nx.topological_generations(self.graph)))[0][1]) > 1:
            self.graph.remove_edge(new_edge.source.id_networkx, new_edge.target.id_networkx)
            raise Exception("add_edge: adding edge would create another root")
        self.edges.add(new_edge)

    # Checks whether 'new_edge' can be added to the current graph
    def valid_graph_edge(self, new_edge):
        if not isinstance(new_edge, ConceptEdge):
            raise Exception("valid_graph_edge: invalid argument type")
        if new_edge.source not in self:
            raise Exception("valid_graph_edge: source node not in graph")
        if new_edge.target not in self:
            raise Exception("valid_graph_edge: target node not in graph")
        # the synset of source is not a WordNet hypernym of that of target
        # Note that hypernym_paths returns a list containing only one element which is a list of synsets
        # In the following code, could use list comprehension instead of map
        targetNode_hypernym_synset_names = list(map(lambda x: x.name(), wn.synset(new_edge.target.synset_name).hypernym_paths()[0]))
        if new_edge.source.synset_name not in targetNode_hypernym_synset_names:
            raise Exception("valid_graph_edge: the source is not a hypernym of the target")
        # the resulting graph would not be its own transitive reduction
        if new_edge.source.id_networkx in nx.algorithms.dag.ancestors(self.graph, new_edge.target.id_networkx):
            raise Exception("valid_graph_edge: the graph already contains a path between the source and the target")
        # the resulting graph would not be a DAG (would have a cycle)
        if new_edge.target.id_networkx in nx.algorithms.dag.ancestors(self.graph, new_edge.source.id_networkx):
            raise Exception("valid_graph_edge: the graph already contains a path between the target and the source")
        return True

    # Creates a new node from 'descriptor' and adds it to the current graph
    # as a childless child of the node 'parent_node'
    def add_descriptor_as_new_node(self, descriptor, parent_node):
        if type(descriptor) != str and not isinstance(parent_node, ConceptNode):
            raise Exception("add_descriptor_as_new_node: invalid argument type")
        if parent_node not in self:
            raise Exception("add_descriptor_as_new_node:" + str(parent_node) + "not in current graph")
        try:
            new_node = ConceptNode.from_descriptor(descriptor)
            new_edge = ConceptEdge(parent_node, new_node)
        except Exception as e:
            print(e)
        else:
            self.add_node(new_node)
            self.add_edge(new_edge)

    # Adds a new synonym to an existing node of the current graph
    def add_descriptor_to_node(self, descriptor, target_node):
        if target_node not in self.graph:
            raise Exception("add_descriptor:" + str(target_node) + "not in current graph")
        try:
            target_node.add_descriptor(descriptor)
        except Exception as e:
            print(e)
        self.graph.nodes[target_node.id_networkx]['descriptors'] \
            = self.graph.nodes[target_node.id_networkx]['descriptors'].add(descriptor)
            
    #Uses matplotlib.pyplot to show a representation of the ConceptGraph using synset names as node labels
    def show(self):
        levels = list(nx.topological_generations(self.graph))
        for i in range(len(levels)):
            for id in levels[i]:
                self.graph.nodes[id]['depth'] = -i
        layout = nx.multipartite_layout(self.graph, subset_key='depth', align='horizontal')
        
        id_to_synset = dict()
        id_to_data = dict(self.graph.nodes.data())
        for id in id_to_data.keys():
            id_to_synset[id] = id_to_data[id]['synset_name']
        
        nx.draw_networkx(self.graph, labels=id_to_synset, pos=layout)
        plt.show()
        plt.clf()

    def __contains__(self, elem):
        contains = False
        if type(elem) == str:
            words = elem.split('.')
            # if string has syntax of a synset_name
            if len(words) == 3:
                # contains = True if elem in synset_name from a node in graph
                if elem in self.graph.nodes.synset_name():
                    contains = True
            else:
                # contains = True if elem in descriptors from a node in graph
                if elem in self.graph.nodes.descriptors():
                    contains = True
        elif isinstance(elem, ConceptNode):
            contains = elem in self.nodes and elem.id_networkx in self.graph
        elif isinstance(elem, ConceptEdge):
            contains = elem in self.edges and self.graph.has_edge(elem.source.id_networkx, elem.target.id_networkx)
        return contains