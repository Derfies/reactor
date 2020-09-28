from reactor.blocks.cyclicblock import CyclicBlock


class RootCyclicBlock(CyclicBlock):

    def get_permutations(self):
        angle_perms = self._calculate_angle_permutations()
        dirs = self.calculate_start_direction_permutations()
        faces = []
        for dir_ in dirs:
            faces.extend(self._calculate_face_permutations(angle_perms, dir_))

        # TODO: Remove once faces are made into graph objects.
        return self.to_faces(faces)