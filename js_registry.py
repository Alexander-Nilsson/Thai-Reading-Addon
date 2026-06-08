import os


class JsRegistry:
    def __init__(self, js_dir):
        self._js_dir = js_dir
        self._cache = {}

    def load(self, name):
        if name not in self._cache:
            path = os.path.join(self._js_dir, name)
            with open(path, "r", encoding="utf-8") as f:
                self._cache[name] = f.read()
        return self._cache[name]
