import colorama

from reactor.wfc.adjacencywavefunction import AdjacencyWaveFunction
from reactor.wfc.utils import get_colour_output


TILE_COLOURS = {
    'L': colorama.Fore.GREEN,
    'X': colorama.Fore.WHITE,
}


if __name__ == '__main__':
    compatibilities = {
        (1, 0, 0): {
            ('X', 'L'),
            ('L', 'X'),
        },
        (-1, 0, 0): {
            ('X', 'L'),
            ('L', 'X'),
        },
        (0, 1, 0): {
            ('L', 'L'),
            ('X', 'X'),
        },
        (0, -1, 0): {
            ('L', 'L'),
            ('X', 'X'),
        },
        (0, 0, 1): {
            ('L', 'L'),
            ('X', 'X'),
        },
        (0, 0, -1): {
            ('L', 'L'),
            ('X', 'X'),
        },
    }
    shape = (5, 6, 7)
    weights = {'L': 1, 'S': 1, 'X': 1}
    wf = AdjacencyWaveFunction(compatibilities, shape, weights)
    wf.run()
    print(get_colour_output(wf.wave, TILE_COLOURS, wf.tiles))
