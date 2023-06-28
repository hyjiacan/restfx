import logging

from ..interface import MiddlewareBase
from ...http import NotFound, HttpRequest

logger = logging.getLogger('restfx')


class CheckRefererMiddleware(MiddlewareBase):
    def __init__(self, allowed_referer_hosts: list = None, block_response=NotFound):
        """

        :param allowed_referer_hosts: 允许列表.例: http://127.0.0.1:1357
        :param block_response: referer 不在允许列表中时，返回指定响应
        """
        self.allowed_referer_hosts = allowed_referer_hosts or []
        self.block_response_class = block_response

    def add_referer(self, *hosts):
        """
        添加一个或多个允许访问的 referer 主机
        :param hosts: 例: http://127.0.0.1:1357
        :return:
        """
        for host in hosts:
            if host not in self.allowed_referer_hosts:
                self.allowed_referer_hosts.append(host)

    def remove_referer(self, *hosts):
        """
        移除一个或多个允许访问的 referer 主机
        :param hosts: 例: http://127.0.0.1:1357
        :return:
        """
        for host in hosts:
            if host not in self.allowed_referer_hosts:
                self.allowed_referer_hosts.remove(host)

    def on_coming(self, request):
        referrer = request.referrer

        # 没有时不指定
        if not referrer:
            return

        host_url = request.host_url

        # 允许服务器地址
        if referrer.startswith(host_url):
            return

        if not self.allowed_referer_hosts:
            self.on_block(request)
            return self.block_response_class()

        # 检查允许的地址
        matched = False
        for host in self.allowed_referer_hosts:
            if referrer.startswith(host):
                matched = True
                break
        if matched:
            return

        self.on_block(request)
        return self.block_response_class()

    @staticmethod
    def on_block(request: HttpRequest):
        logger.warning('Unexpected Referer found from %r: %s' % (request.remote_addr, request.referrer))
