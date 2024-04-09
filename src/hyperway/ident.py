
class IDFunc(object):
    _id = None

    def set_id(self, v):
        self._id = v

    def id(self):
        return self._id or id(self)
