from base import Base

class HomePage(Base):
    """This Page Object models the QMO Home Page (https://quality.mozilla.org/)."""

    # The title of this page, which is used by is_the_current_page() in page.py
    _page_title = u'QMO \u2013 quality.mozilla.org | The Home of Mozilla QA'

    # Locators for the home page
    #_tagline_locator = (By.ID, 'tagline')
    #_news_items_locator = (By.TAG_NAME, 'article')
