none = 0
handle_coming = 1 << 0
handle_leaving = 1 << 2
handle_request = 1 << 3
before_invoke = 1 << 4
after_return = 1 << 5

all = handle_coming | handle_leaving | handle_request | before_invoke | after_return
