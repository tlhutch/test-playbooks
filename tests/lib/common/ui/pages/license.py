from base import TowerPage


class License(TowerPage):

    _path = '/#/license'

    def open(self, *args, **kwargs):
        self.wait_for_spinny()
        return super(License, self).open(*args, **kwargs)
