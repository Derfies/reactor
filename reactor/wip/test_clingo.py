import clyngor
from clyngor import solve

from reactor.readers.gexfreader import GEXFReader


GRID_PATH = '../../data/reactor1.gexf'


def graph_to_asp(g):

    nodes_str = ' '.join([
        f'node({node.lower()}).'
        for node in g.nodes()
    ])

    edges_str = ' '.join([
        f'edge({head.lower()}, {tail.lower()}).'
        for head, tail in g.edges()
    ])

    return nodes_str + ' ' + edges_str


# Load a map.
g = GEXFReader()(GRID_PATH).to_undirected()
asp_g = graph_to_asp(g)

clyngor.CLINGO_BIN_PATH = '../../bin/clingo-5.4.0-win64/clingo.exe'
answers = solve(
    '../../data/clingo/test2.lp',
    inline=asp_g,
    use_clingo_module=False,
    nb_model=1
)
for a in answers:
    for node_type in a:
        print('->', node_type)
