"""Offline stand-in for Blender's ``mathutils`` module."""


class Vector:
    def __init__(self, values=()):
        self._v = [float(x) for x in values]

    def __iter__(self):
        return iter(self._v)

    def __len__(self):
        return len(self._v)

    def __getitem__(self, i):
        return self._v[i]

    def __matmul__(self, other):
        return other

    @property
    def x(self):
        return self._v[0]

    @x.setter
    def x(self, value):
        self._v[0] = float(value)

    @property
    def y(self):
        return self._v[1]

    @y.setter
    def y(self, value):
        self._v[1] = float(value)

    @property
    def z(self):
        return self._v[2]

    @z.setter
    def z(self, value):
        self._v[2] = float(value)

    def __repr__(self):
        return "Vector(%r)" % (self._v,)


class Matrix:
    def __matmul__(self, other):
        return other


def Vector_(values=()):
    return Vector(values)
