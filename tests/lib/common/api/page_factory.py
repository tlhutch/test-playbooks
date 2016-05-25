import factory
import pytest


class PageFactoryOptions(factory.base.FactoryOptions):
    """Configuration for PageFactory
    """
    def _build_default_options(self):
        options = super(PageFactoryOptions, self)._build_default_options()
        options.append(factory.base.OptionDefault(
            'get_or_create', (), inherit=True))
        return options


class PageFactory(factory.Factory):
    """Tower API Page Model Base Factory
    """
    _options_class = PageFactoryOptions

    @classmethod
    def _get_or_create(cls, model, request, **kwargs):
        """Create an instance of the model through its associated rest api
        endpoint if it doesn't already exist
        """
        key_fields = {}
        for field in cls._meta.get_or_create:
            if field not in kwargs:
                msg = "{0} initialization value '{1}' not found"
                msg = msg.format(cls.__name__, field)
                raise factory.errors.FactoryError(msg)
            key_fields[field] = kwargs[field]
        try:
            obj = model.get(**key_fields).results.pop()
        except IndexError:
            model.post(kwargs)
            obj = model.get(**key_fields).results.pop()
            request.addfinalizer(obj.silent_delete)
        return obj

    @classmethod
    def _create(cls, model_class, request, **kwargs):
        """Create data and post to the associated endpoint
        """
        testsetup = request.getfuncargvalue('testsetup')
        model = model_class(testsetup)
        if cls._meta.get_or_create:
            obj = cls._get_or_create(model, request, **kwargs)
        else:
            obj = model.post(kwargs)
            request.addfinalizer(obj.silent_delete)
        return obj


def factory_fixture(page_factory, scope='function', **kwargs):
    @pytest.fixture(scope=scope)
    def _factory(request):
        def _model(**inner_kwargs):
            model_kwargs = dict(kwargs.items() + inner_kwargs.items())
            return page_factory(request=request, **model_kwargs).get()
        return _model
    return _factory


def model_fixture(page_factory, scope='function', **kwargs):
    @pytest.fixture(scope=scope)
    def _model(request):
        return page_factory(request=request, **kwargs).get()
    return _model
