import factory


class PageFactoryOptions(factory.base.FactoryOptions):
    """Configuration for PageFactory
    """
    def _build_default_options(self):
        options = super(PageFactoryOptions, self)._build_default_options()
        options.append(factory.base.OptionDefault('get_or_create', (), inherit=True))
        options.append(factory.base.OptionDefault('resources', (), inherit=True))
        return options


class PageFactory(factory.Factory):
    """Tower API Page Model Base Factory
    """
    _options_class = PageFactoryOptions

    @classmethod
    def _adjust_kwargs(cls, **kwargs):
        if 'request' not in kwargs:
            kwargs['request'] = False
        return kwargs

    @classmethod
    def _create(cls, model_class, request, **kwargs):
        """Create data and post to the associated endpoint
        """
        testsetup = request.getfuncargvalue('testsetup') if request else None
        model = model_class(testsetup)  # TODO: determine desired authentication behavior out of pytest context.
        # get or create the requested resource
        if cls._meta.get_or_create:
            obj = cls._get_or_create(model, request, **kwargs)
        else:
            obj = model.create(**kwargs)
            if request:
                request.addfinalizer(obj.silent_cleanup)
        return obj

    @classmethod
    def _get_or_create(cls, model, request, **kwargs):
        """Create an instance of the model through its associated endpoint
        if it doesn't already exist
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
            obj = model.create(**kwargs)
            if request:
                request.addfinalizer(obj.silent_cleanup)
        return obj

    @classmethod
    def payload(cls, request, **kwargs):
        kwargs['request'] = request
        # generate dependencies
        attrs = cls.attributes(create=True, extra=kwargs)
        attrs = cls._rename_fields(**attrs)
        # extract resource attributes
        resources = {}
        for key in cls._meta.resources:
            if key in attrs:
                resources[key] = attrs.get(key)
        # process resource attributes for payloads
        attrs = cls._adjust_kwargs(**attrs)
        # extract *args
        for key in cls._meta.inline_args:
            del attrs[key]
        # remove any remaining args tagged for exclusion
        for arg in cls._meta.exclude:
            attrs.pop(arg, None)
        # remove any defined parameters
        for arg in cls._meta.parameters:
            attrs.pop(arg, None)
        return attrs, resources
