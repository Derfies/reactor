import colorama

from reactor.wfc.adjacencywavefunction import AdjacencyWaveFunction
from reactor.wfc.utils import get_colour_output


TILE_COLOURS = {
    'L': colorama.Fore.GREEN,
    'S': colorama.Fore.BLUE,
    'C': colorama.Fore.YELLOW,
}

INPUT_MATRIX = [
    ['L', 'L', 'L', 'L'],
    ['L', 'L', 'L', 'L'],
    ['L', 'L', 'L', 'L'],
    ['L', 'C', 'C', 'L'],
    ['C', 'S', 'S', 'C'],
    ['S', 'S', 'S', 'S'],
    ['S', 'S', 'S', 'S'],
]


if __name__ == '__main__':
    wf = AdjacencyWaveFunction.create_from_input_matrix(INPUT_MATRIX, (10, 50))
    wf.run()
    print(get_colour_output(wf.wave, TILE_COLOURS, wf.tiles))
