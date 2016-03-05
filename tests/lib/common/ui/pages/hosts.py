from base import TowerPage


class Hosts(TowerPage):

    _path = '/#/home/hosts'

    def open(self, *args, **kwargs):
        self.wait_for_spinny()
        return super(Hosts, self).open(*args, **kwargs)
