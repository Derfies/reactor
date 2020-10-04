from reactor.blocks.cyclicblock import CyclicBlock


class RootCyclicBlock(CyclicBlock):

    def get_permutations(self):
        faces = []
        for dir_ in self.get_start_direction_permutations():
            faces.extend(self.get_face_permutations(dir_))
        return faces