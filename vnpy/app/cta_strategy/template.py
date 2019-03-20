""""""
from abc import ABC
from typing import Any, Callable

from vnpy.trader.constant import Interval, Status
from vnpy.trader.object import BarData, TickData, OrderData, TradeData

from .base import CtaOrderType, StopOrder, EngineType


class CtaTemplate(ABC):
    """"""

    author = ""
    parameters = []
    variables = []
    # 这里parameters就是策略需要提前提供的参数，variables是后面相应的计算出来的指标

    def __init__(
        self,
        cta_engine: Any,
        strategy_name: str,
        vt_symbol: str,
        setting: dict,):
        """"""
        self.cta_engine = cta_engine
        self.strategy_name = strategy_name
        self.vt_symbol = vt_symbol

        self.inited = False
        self.trading = False
        self.pos = 0

        self.variables.insert(0, "inited")
        self.variables.insert(1, "trading")
        self.variables.insert(2, "pos")

        self.update_setting(setting)
    #     遍历setting中的元素，然后进行赋值进去

    def update_setting(self, setting: dict):
        """
        Update strategy parameter wtih value in setting dict.
        """
        for name in self.parameters:
            if name in setting:
                setattr(self, name, setting[name])

    # @classmethod不需要实例化，注意cls
    # get_class_parameters和get_parameters两个函数功能一致
    @classmethod
    def get_class_parameters(cls):
        """
        Get default parameters dict of strategy class.
        """
        class_parameters = {}
        for name in cls.parameters:
            class_parameters[name] = getattr(cls, name)
        return class_parameters

    def get_parameters(self):
        """
        Get strategy parameters dict.
        """
        strategy_parameters = {}
        for name in self.parameters:
            strategy_parameters[name] = getattr(self, name)
        return strategy_parameters

    # 与上一个函数别无二致，基本差不多
    def get_variables(self):
        """
        Get strategy variables dict.
        """
        strategy_variables = {}
        for name in self.variables:
            strategy_variables[name] = getattr(self, name)
        return strategy_variables

    # 把这个类的基本信息汇总到一个字典中，再返回
    def get_data(self):
        """
        Get strategy data.
        """
        strategy_data = {
            "strategy_name": self.strategy_name,
            "vt_symbol": self.vt_symbol,
            "class_name": self.__class__.__name__,
            "author": self.author,
            "parameters": self.get_parameters(),
            "variables": self.get_variables(),
        }
        return strategy_data

    def on_init(self):
        """
        Callback when strategy is inited.
        在engine中，被成员函数call_strategy_func调用
        会在engine中被调用，用于处理parameters
        """
        pass

    def on_start(self):
        """
        Callback when strategy is started.
        同理，在engine中，被成员函数call_strategy_func调用
        """
        pass

    def on_stop(self):
        """
        Callback when strategy is stopped.
        """
        pass

    def on_tick(self, tick: TickData):
        """
        Callback of new tick data update.
        """
        pass
    # on_tick和on_bar在自己类里面被load_tick和load_bar中被调用
    # 然后在进一步通过cta_engine去调用该on_bar或者on_tick函数
    def on_bar(self, bar: BarData):
        """
        Callback of new bar data update.
        """
        pass

    def on_trade(self, trade: TradeData):
        """
        Callback of new trade data update.
        在cross_limit_order等函数中被调用
        """
        pass

    def on_order(self, order: OrderData):
        """
        Callback of new order data update.
        在cross_limit_order等函数中被调用
        """
        pass

    def on_stop_order(self, stop_order: StopOrder):
        """
        Callback of stop order update.
        """
        pass

    def buy(self, price: float, volume: float, stop: bool = False):
        """
        Send buy order to open a long position.
        """
        return self.send_order(CtaOrderType.BUY, price, volume, stop)

    def sell(self, price: float, volume: float, stop: bool = False):
        """
        Send sell order to close a long position.
        """
        return self.send_order(CtaOrderType.SELL, price, volume, stop)

    def short(self, price: float, volume: float, stop: bool = False):
        """
        Send short order to open as short position.
        """
        return self.send_order(CtaOrderType.SHORT, price, volume, stop)

    def cover(self, price: float, volume: float, stop: bool = False):
        """
        Send cover order to close a short position.
        """
        return self.send_order(CtaOrderType.COVER, price, volume, stop)

    def send_order(
        self,
        order_type: CtaOrderType,
        price: float,
        volume: float,
        stop: bool = False,
    ):
        """
        Send a new order.
        """
        if self.trading:
            vt_orderid = self.cta_engine.send_order(self, order_type, price, volume, stop)
        else:
            vt_orderid = ""
        return vt_orderid

    def cancel_order(self, vt_orderid: str):
        """
        Cancel an existing order.
        """
        self.cta_engine.cancel_order(self, vt_orderid)

    def cancel_all(self):
        """
        Cancel all orders sent by strategy.
        """
        self.cta_engine.cancel_all(self)

    def write_log(self, msg: str):
        """
        Write a log message.
        """
        self.cta_engine.write_log(msg, self)

    def get_engine_type(self):
        """
        Return whether the cta_engine is backtesting or live trading.
        """
        return self.cta_engine.get_engine_type()

    def load_bar(
        self,
        days: int,
        interval: Interval = Interval.MINUTE,
        callback: Callable = None,):
        """
        Load historical bar data for initializing strategy.
        """
        if not callback:
            callback = self.on_bar

        self.cta_engine.load_bar(self.vt_symbol, days, interval, callback)

    def load_tick(self, days: int):
        """
        Load historical tick data for initializing strategy.
        """
        self.cta_engine.load_tick(self.vt_symbol, days, self.on_tick)

    def put_event(self):
        """
        Put an strategy data event for ui update.
        """
        # 调用cta_engine的时间注册函数
        # 这里的cta_engine由构造函数初始化，也就是
        # 在策略继承template后，由策略代码选择相应的引擎
        # 但是奇怪的是，策略中使用的super函数，确实使用父类
        # 的构造函数，父类构造函数也就是当前类，template，并
        # 没有指定具体的引擎
        self.cta_engine.put_strategy_event(self)
    #     这里put_strategy_event(self)的self就是当前的策略模板本身

    def send_email(self, msg):
        """
        Send email to default receiver.
        """
        self.cta_engine.send_email(msg, self)

    def sync_data(self):
        """
        Sync strategy variables value into disk storage.
        """
        if self.trading:
            self.cta_engine.sync_strategy_data(self)


class CtaSignal(ABC):
    """"""

    def __init__(self):
        """"""
        self.signal_pos = 0

    def on_tick(self, tick: TickData):
        """
        Callback of new tick data update.
        """
        pass

    def on_bar(self, bar: BarData):
        """
        Callback of new bar data update.
        """
        pass

    def set_signal_pos(self, pos):
        """"""
        self.signal_pos = pos

    def get_signal_pos(self):
        """"""
        return self.signal_pos


class TargetPosTemplate(CtaTemplate):
    """暂时不是很清楚，应该是某种策略交易的模板类，从CtaTemplate继承而来，并重写部分函数"""

    author = '量衍投资'

    tick_add = 1
    last_tick = None
    last_bar = None
    target_pos = 0
    orderList = []

    variables = ['target_pos']

    def __init__(self, cta_engine, strategy_name, vt_symbol, setting):
        """"""
        super(TargetPosTemplate, self).__init__(
            cta_engine, strategy_name, vt_symbol, setting
        )

    def on_tick(self, tick: TickData):
        """
        Callback of new tick data update.
        """
        self.last_tick = tick

        if self.trading:
            self.trade()

    def on_bar(self, bar: BarData):
        """
        Callback of new bar data update.
        """
        self.last_bar = bar

    def on_order(self, order: OrderData):
        """
        Callback of new order data update.
        """
        if order.status == Status.ALLTRADED or order.status == Status.CANCELLED:
            if order.vt_orderid in self.orderList:
                self.orderList.remove(order.vt_orderid)

    def set_target_pos(self, target_pos):
        """"""
        self.target_pos = target_pos
        self.trade()

    def trade(self):
        """"""
        self.cancel_all()

        pos_change = self.target_pos - self.pos
        if not pos_change:
            return

        long_price = 0
        short_price = 0

        if self.last_tick:
            if pos_change > 0:
                long_price = self.last_tick.ask_price_1 + self.tick_add
                if self.last_tick.limit_up:
                    long_price = min(long_price, self.last_tick.limit_up)
            else:
                short_price = self.last_tick.bid_price_1 - self.tick_add
                if self.last_tick.limit_down:
                    short_price = max(short_price, self.last_tick.limit_down)

        else:
            if pos_change > 0:
                long_price = self.last_bar.close_price + self.tick_add
            else:
                short_price = self.last_bar.close_price - self.tick_add

        if self.get_engine_type() == EngineType.BACKTESTING:
            if pos_change > 0:
                vt_orderid = self.buy(long_price, abs(pos_change))
            else:
                vt_orderid = self.short(short_price, abs(pos_change))
            self.orderList.append(vt_orderid)

        else:
            if self.orderList:
                return

            if pos_change > 0:
                if self.pos < 0:
                    if pos_change < abs(self.pos):
                        vt_orderid = self.cover(long_price, pos_change)
                    else:
                        vt_orderid = self.cover(long_price, abs(self.pos))
                else:
                    vt_orderid = self.buy(long_price, abs(pos_change))
            else:
                if self.pos > 0:
                    if abs(pos_change) < self.pos:
                        vt_orderid = self.sell(short_price, abs(pos_change))
                    else:
                        vt_orderid = self.sell(short_price, abs(self.pos))
                else:
                    vt_orderid = self.short(short_price, abs(pos_change))
            self.orderList.append(vt_orderid)
