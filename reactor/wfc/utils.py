import colorama
import numpy as np


def get_colour_output(wave, colors, tiles):

    # Hack so that numpy doesn't wrap lines.
    np.set_printoptions(edgeitems=30, linewidth=100000)

    # Convert collapsed states to symbols.
    reshaped = wave.reshape(wave.shape[0], -1)
    chars = []
    for index in range(reshaped.shape[1]):
        states = reshaped[(slice(None), index)]
        tile = tiles[np.argmax(states)]
        chars.append(tile)
    shaped = np.array(chars).reshape(*wave.shape[1:])

    # Convert symbols to coloured ascii characters. Converting the array to a
    # string means numpy to working out each 2d slice of the nd array for us
    # automatically.
    lines = []
    for line in str(shaped).split('\n'):
        for bad_char in ('[', ']', '\''):
            line = line.replace(bad_char, '').strip()
        new_line = ''
        for char in line.split():
            color = colors[char]
            new_line += color + char + colorama.Style.RESET_ALL
        lines.append(new_line)
    return '\n'.join(lines)