from reactor.layouters.facelayouter import FaceLayouter


class RootFaceLayouter(FaceLayouter):

    def get_permutations(self):
        faces = []
        for dir_ in self.get_start_direction_permutations():
            faces.extend(self.get_face_permutations(dir_))
        return faces
