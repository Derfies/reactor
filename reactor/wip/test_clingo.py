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

    #extra = 'num_nodes()'

    return nodes_str + ' ' + edges_str# + extra

import random
# Load a map.
g = GEXFReader()(GRID_PATH).to_undirected()
asp_g = graph_to_asp(g)

clyngor.CLINGO_BIN_PATH = '../../bin/clingo-5.4.0-win64/clingo.exe'
answers = solve(
    '../../data/clingo/test2.lp',
    inline=asp_g,
    use_clingo_module=False,
    nb_model=1,
    constants={'num_nodes': len(g)},
    options=f'--seed={random.randint(0, 10000)} --rand-freq=1'# --sign-def=3'
)
print(answers.command)

answers = list(answers)
print('num answers:', len(answers))
for a in answers:
    print('-' * 25)
    for node_type in sorted(a):
        print('->', node_type)
if not len(answers):
    print('no answers')

# Check
num_nodes = len(g)
type_range = {
    'entrance': (1, 1),
    'courtyard': (0, 1),
    'chamber': (1, num_nodes / 3),
    'main_chamber': (1, 1),
    'hallway': (0, num_nodes)
}
print(type_range)

high_chambers = set()
for answer in answers:
    for p in answer:
        if p[0] != 'type_num':
            continue
        name, num = p[1]
        #print(name, '->', num)
        range = type_range[name]
        assert range[0] <= num <= range[1]

        if name == 'chamber' and num > 1:
            high_chambers.add(answer)
        # for k, v in type_range.items():
        #     name, num = p[1]
        #     print(v[name])
        #     assert v[name][0] < num < v[name][1]


print('num high chambers:', len(high_chambers))