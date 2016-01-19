import urlparse

from clickable import Clickable


class Link(Clickable):

    @property
    def href(self):
        return self.root.get_attribute('href')

    @property
    def _href(self):
        return urlparse.urlparse(self.href, allow_fragments=False)


class ProjectsLink(Link):

    _spinny = True

    def after_click(self):
        super(ProjectsLink, self).after_click()

        return self.page._load_page('Projects')


class InventoriesLink(Link):

    _spinny = True

    def after_click(self):
        super(InventoriesLink, self).after_click()

        return self.page._load_page('Inventories')


class JobTemplatesLink(Link):

    _spinny = True

    def after_click(self):
        super(JobTemplatesLink, self).after_click()

        return self.page._load_page('JobTemplates')


class JobsLink(Link):

    _spinny = True

    def after_click(self):
        super(JobsLink, self).after_click()

        return self.page._load_page('Jobs')


class SetupLink(Link):

    _spinny = False

    def after_click(self):
        super(SetupLink, self).after_click()

        return self.page._load_page('SetupMenu')


class LogoutLink(Link):

    _spinny = False

    def after_click(self):
        super(LogoutLink, self).after_click()

        return self.page._load_page('Login')


class UserLink(Link):

    _spinny = True

    def after_click(self):
        super(UserLink, self).after_click()

        return self.page._load_page('User')


class DashboardLink(Link):

    _spinny = True

    def after_click(self):
        super(DashboardLink, self).after_click()

        return self.page._load_page('Dashboard')


class PageReference(Link):

    _spinny = True

    def before_click(self):
        super(PageReference, self).before_click()

        page_path = self._href.path

        if page_path.endswith('/'):
            page_path = page_path.rstrip('/')

        self._page_path = page_path

    def after_click(self):
        super(PageReference, self).after_click()

        return self.page._load_page(self._page_path)
