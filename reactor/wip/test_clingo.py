import abc
import random

import clyngor
from clyngor import solve

from reactor.readers.gexfreader import GEXFReader


GRID_PATH = '../../data/graphs/blood/e1m5.gexf'


class AspLevelTheme(metaclass=abc.ABCMeta):

    def __init__(self, g):
        self.g = g

    @staticmethod
    def format_fact(label, *args):
        args_str = ', '.join(map(str, args))
        return f'{label}({args_str}).'

    @property
    def num_nodes(self):
        return len(self.g)

    @property
    def node_facts(self):
        return [
            self.format_fact('node', node.lower())
            for node in self.g
        ]

    @property
    def edge_facts(self):
        return [
            self.format_fact('edge', head.lower(), tail.lower())
            for head, tail in self.g.edges()
        ]

    @property
    @abc.abstractmethod
    def zone_facts(self):
        """"""

    @property
    @abc.abstractmethod
    def adjacency_facts(self):
        """"""

    @property
    def facts(self):
        facts = []
        facts.extend(self.node_facts)
        facts.extend(self.edge_facts)
        facts.extend(self.zone_facts)
        facts.extend(self.adjacency_facts)
        return facts

    def get_clingo_kwargs(self):
        return {
            'constants': {
                'num_nodes': self.num_nodes
            },
            'inline': '\n'.join(self.facts)
        }


class CastleTheme(AspLevelTheme):

    @property
    def zone_facts(self):
        return [
            self.format_fact('type_range', 'entrance', 1, 1),
            self.format_fact('type_range', 'courtyard', 0, 1),
            self.format_fact('type_range', 'cellar', 0, 1),
            self.format_fact('type_range', 'chamber', 1, int(self.num_nodes / 3)),
            self.format_fact('type_range', 'main_chamber', 1, 1),
            self.format_fact('type_range', 'hallway', 0, 15),
            #self.format_fact('type_range', 'room', 0, 15),
        ]

    @property
    def adjacency_facts(self):
        return [
            self.format_fact('adjacency', 'entrance', 'hallway'),
            self.format_fact('adjacency', 'entrance', 'courtyard'),
            self.format_fact('adjacency', 'entrance', 'chamber'),

            self.format_fact('adjacency', 'cellar', 'hallway'),
            self.format_fact('adjacency', 'cellar', 'courtyard'),
            self.format_fact('adjacency', 'cellar', 'chamber'),

            self.format_fact('adjacency', 'chamber', 'chamber'),
            self.format_fact('adjacency', 'chamber', 'hallway'),

            self.format_fact('adjacency', 'main_chamber', 'hallway'),
            self.format_fact('adjacency', 'main_chamber', 'chamber'),

        ]


# Load a map.
g = GEXFReader()(GRID_PATH).to_undirected()
theme = CastleTheme(g)

# Run solver.
seed = random.randint(0, 999999999)
print(seed)
clyngor.CLINGO_BIN_PATH = '../../bin/clingo-5.4.0-win64/clingo.exe'
answers = solve(
    '../../data/clingo/theme.lp',
    use_clingo_module=False,
    nb_model=0,
    options=f'--rand-freq=1 --seed={seed}',
    delete_tempfile=False,
    **theme.get_clingo_kwargs()
)
#print(len(list(answers)))
#raise
answers = list(answers)
rand_index = random.randint(0, len(answers))
answer = answers[rand_index]
#print(answers.command)

#answers = list(answers)
print('num answers:', len(answers))

print('Facts:')
for f in theme.facts:
    print('    ->', f)

#for a in answers:
print('-' * 25)
for node_type in sorted(answer):
    print('->', node_type)
# if not len(answers):
#     print('no answers')
