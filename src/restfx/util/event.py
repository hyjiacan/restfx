class EventArgs(dict):
    def __init__(self, event_type: str, args: dict):
        self.__type__ = event_type
        self._args = args
        super(EventArgs, self).__init__()

    def __getattr__(self, item: str):
        return self._args.get(item)

    def __dict__(self):
        return self._args

    def __str__(self):
        return '<event %s ...>' % self.__type__


class Event:
    def __init__(self):
        self.events = {}

    def emit(self, event_type: str, **arguments):
        if event_type not in self.events:
            return

        e = EventArgs(event_type, arguments)

        for handler in self.events[event_type]:
            handler(e)

    def on(self, event_type: str, handler):
        if event_type not in self.events:
            self.events[event_type] = []

        self.events[event_type].append(handler)

    def off(self, event_type: str, handler=None):
        if event_type not in self.events:
            return

        handlers = self.events[event_type]

        if handler is None:
            handlers.clear()
            return

        handlers.remove(handler)
