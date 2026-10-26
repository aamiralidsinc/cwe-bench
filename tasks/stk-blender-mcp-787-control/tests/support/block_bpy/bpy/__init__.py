"""Offline stand-in for Blender's bundled ``bpy`` module.

Only the surface the add-on touches at import time and on the asset-download paths is
implemented.  Operator calls are recorded in ``bpy.calls`` so a caller can observe what
the product passed to Blender; a few operators also emulate their filesystem effect.
"""

import contextlib
import os

calls = []
op_hook = None


class _Vec:
    def __init__(self, values):
        self._v = [float(x) for x in values]

    def __iter__(self):
        return iter(self._v)

    def __len__(self):
        return len(self._v)

    def __getitem__(self, i):
        return self._v[i]

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
        return "_Vec(%r)" % (self._v,)


class _Mat:
    def __matmul__(self, other):
        if isinstance(other, _Vec):
            return _Vec(other)
        return other


class _Image:
    def __init__(self, name="image"):
        self.name = name
        self.size = (64, 64)
        self.file_format = "PNG"
        self.colorspace_settings = _Permissive()

    def scale(self, w, h):
        self.size = (w, h)

    def save(self):
        return None

    def pack(self):
        return None

    def reload(self):
        return None


class _Permissive:
    def __getattr__(self, name):
        if name.startswith("__"):
            raise AttributeError(name)
        return None

    def __setattr__(self, name, value):
        object.__setattr__(self, name, value)


class _Objects:
    def __init__(self):
        self._objs = []

    def __iter__(self):
        return iter(list(self._objs))

    def get(self, name):
        for o in self._objs:
            if o.name == name:
                return o
        return None

    def add(self, obj):
        self._objs.append(obj)
        return obj

    def remove(self, obj):
        if obj in self._objs:
            self._objs.remove(obj)

    def clear(self):
        self._objs[:] = []


class _Images:
    def __init__(self):
        self._imgs = []

    def __iter__(self):
        return iter(list(self._imgs))

    def load(self, path):
        img = _Image(os.path.basename(str(path)))
        self._imgs.append(img)
        return img

    def remove(self, img):
        if img in self._imgs:
            self._imgs.remove(img)

    def clear(self):
        self._imgs[:] = []


class _CollectionObjects:
    def link(self, obj):
        return None


class _Collection:
    def __init__(self):
        self.objects = _CollectionObjects()


class _DataSet:
    def __init__(self, factory=None):
        self._items = []
        self._factory = factory

    def new(self, *a, **k):
        item = self._factory(*a, **k) if self._factory else _Permissive()
        self._items.append(item)
        return item

    def __iter__(self):
        return iter(list(self._items))

    def __len__(self):
        return len(self._items)

    def clear(self):
        self._items[:] = []


class _Data:
    def __init__(self):
        self.objects = _Objects()
        self.images = _Images()
        self.materials = _DataSet()
        self.worlds = _DataSet()
        self.libraries = _Permissive()


class _Area:
    type = "VIEW_3D"


class _Screen:
    def __init__(self):
        self.areas = [_Area()]


class _ViewLayer:
    def update(self):
        return None


class _Context:
    def __init__(self):
        self.scene = _Scene()
        self.collection = _Collection()
        self.preferences = _Permissive()
        self.preferences.addons = {}
        self.selected_objects = []
        self.view_layer = _ViewLayer()
        self.screen = _Screen()

    @contextlib.contextmanager
    def temp_override(self, **kwargs):
        yield self


class _Scene(_Permissive):
    def __init__(self):
        object.__setattr__(self, "blendermcp_use_polyhaven", True)
        object.__setattr__(self, "blendermcp_use_hyper3d", True)
        object.__setattr__(self, "blendermcp_use_sketchfab", True)
        object.__setattr__(self, "blendermcp_use_hunyuan3d", False)
        object.__setattr__(self, "blendermcp_hyper3d_mode", "MAIN_SITE")
        object.__setattr__(self, "blendermcp_hyper3d_api_key", "test-hyper3d-key")
        object.__setattr__(self, "blendermcp_sketchfab_api_key", "test-sketchfab-key")
        object.__setattr__(self, "blendermcp_hunyuan3d_secret_id", "")
        object.__setattr__(self, "blendermcp_hunyuan3d_secret_key", "")
        object.__setattr__(self, "blendermcp_port", 9876)
        object.__setattr__(self, "blendermcp_server_running", False)


class _MeshObject:
    def __init__(self, name="ImportedMesh", type="MESH"):
        self.name = name
        self.type = type
        self.location = _Vec((0.0, 0.0, 0.0))
        self.rotation_euler = _Vec((0.0, 0.0, 0.0))
        self.scale = _Vec((1.0, 1.0, 1.0))
        self.bound_box = [
            (-1.0, -1.0, -1.0), (1.0, -1.0, -1.0), (1.0, 1.0, -1.0), (-1.0, 1.0, -1.0),
            (-1.0, -1.0, 1.0), (1.0, -1.0, 1.0), (1.0, 1.0, 1.0), (-1.0, 1.0, 1.0),
        ]
        self.matrix_world = _Mat()
        self.children = []
        self.parent = None
        self.dimensions = _Vec((2.0, 2.0, 2.0))
        self.data = _MeshData(self.name + "_data")


class _MeshData:
    def __init__(self, name):
        self.name = name


class _OpCall:
    def __init__(self, name):
        self.name = name

    def __call__(self, *args, **kwargs):
        calls.append((self.name, dict(kwargs)))
        if op_hook is not None:
            op_hook(self.name, dict(kwargs))
        if self.name == "screen.screenshot_area":
            path = kwargs.get("filepath")
            if path:
                try:
                    with open(path, "wb") as fh:
                        fh.write(b"fake-png")
                except OSError:
                    pass
        elif self.name in ("import_scene.gltf", "import_scene.fbx", "import_scene.obj",
                           "wm.obj_import"):
            obj = _MeshObject()
            context.scene  # noqa: B018 - touch to keep the stub coherent
            data.objects.add(obj)
            context.selected_objects = [obj]
        return {"FINISHED"}


class _OpGroup:
    def __init__(self, prefix):
        self._prefix = prefix

    def __getattr__(self, name):
        if name.startswith("__"):
            raise AttributeError(name)
        return _OpCall(self._prefix + name if not self._prefix else self._prefix + "." + name)


class _Ops:
    def __getattr__(self, name):
        if name.startswith("__"):
            raise AttributeError(name)
        return _OpGroup(name)


class _Timers:
    def register(self, fn, first_interval=0.0, persistent=False):
        fn()
        return object()

    def unregister(self, fn):
        return None


class _App:
    background = False
    version = (4, 2, 0)
    timers = _Timers()


class _Utils:
    def register_class(self, cls):
        return None

    def unregister_class(self, cls):
        return None


class _Types:
    class AddonPreferences:
        pass

    class Panel:
        pass

    class Operator:
        pass

    class Scene:
        pass


app = _App()
data = _Data()
context = _Context()
ops = _Ops()
utils = _Utils()
types = _Types()


def reset():
    """Test hook: clear recorded calls and imported objects."""
    global op_hook
    op_hook = None
    calls[:] = []
    data.objects.clear()
    data.images.clear()
    context.selected_objects = []
    context.scene = _Scene()


reset()
