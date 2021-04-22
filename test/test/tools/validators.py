import re

from restfx import val


class MyValidator(val):
    @classmethod
    def _all_a(cls, msg, param_name, args: dict):
        value = args.get(param_name)
        if value is None:
            return False

        return None if re.match('^a+$', value) else msg

    def all_a(self, msg='只能包含 a 字符'):
        self._append_rule(self._all_a, (msg,))
        return self
