from networkx.readwrite.gexf import GEXFReader as GEXFReader_

from reactor.const import POSITION
from reactor.geometry.vector import Vector2


class GEXFReader(GEXFReader_):

    def make_graph(self, graph_xml):

        # Remove attribute data element with no class which breaks networkx
        # loader.
        for attr in graph_xml.findall(f'{{{self.NS_GEXF}}}attributes'):
            if not attr.get('class'):
                print('Removing attributes:', attr)
                graph_xml.remove(attr)
        g = super(GEXFReader, self).make_graph(graph_xml)

        # Replace viz: position: x, x with position: Vector2(x, y).
        for node in g:
            pos = g.nodes[node]['viz']['position']
            g.nodes[node][POSITION] = Vector2(pos['x'], pos['y'])

        return g