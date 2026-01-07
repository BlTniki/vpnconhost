import pytest
from vpnconhost.db import get_db_executor, DBExecutor, auto_transaction
import threading

def test_get_db_executor_returns_executor():
    executor = get_db_executor()
    assert isinstance(executor, DBExecutor)


def test_get_db_executor_thread_local():
    # Проверяем, что для одного потока возвращается один и тот же объект
    executor1 = get_db_executor()
    executor2 = get_db_executor()
    assert executor1 is executor2



def test_get_db_executor_different_threads():
    # Проверяем, что для разных потоков возвращаются разные объекты
    import threading
    results = []
    def worker():
        results.append(get_db_executor())
    t1 = threading.Thread(target=worker)
    t2 = threading.Thread(target=worker)
    t1.start()
    t2.start()
    t1.join()
    t2.join()
    assert len(results) == 2
    assert results[0] is not results[1]


def patch_executor(monkeypatch, calls=None, results=None):
    """Monkeypatch методы транзакций для отслеживания вызовов."""
    executor = get_db_executor()
    if calls is not None:
        monkeypatch.setattr(executor, 'open', lambda: calls.append('open'))
        monkeypatch.setattr(executor, 'commit_and_close', lambda: calls.append('commit'))
        monkeypatch.setattr(executor, 'rollback_and_close', lambda: calls.append('rollback'))
    if results is not None:
        monkeypatch.setattr(executor, 'open', lambda: results.append(threading.get_ident()))
        monkeypatch.setattr(executor, 'commit_and_close', lambda: results.append('commit'))
        monkeypatch.setattr(executor, 'rollback_and_close', lambda: results.append('rollback'))
    return executor


def test_auto_transaction_one_level_of_call_depth(monkeypatch):
    calls = []
    patch_executor(monkeypatch, calls=calls)

    @auto_transaction()
    def func():
        return 'ok'

    result = func()
    assert result == 'ok'
    assert calls == ['open', 'commit']

def test_auto_transaction_multiple_levels_of_call_depth(monkeypatch):
    calls = []
    patch_executor(monkeypatch, calls=calls)

    @auto_transaction()
    def inner():
        return 'ok'

    @auto_transaction()
    def outer():
        return inner()

    result = outer()
    assert result == 'ok'
    # Должен быть только один open и один commit
    assert calls == ['open', 'commit']


def test_auto_transaction_error_on_multiple_levels_of_call_depth(monkeypatch):
    calls = []
    patch_executor(monkeypatch, calls=calls)

    @auto_transaction()
    def inner_exc():
        raise ValueError('fail')

    @auto_transaction()
    def outer_exc():
        inner_exc()

    try:
        outer_exc()
    except ValueError:
        pass
    # Должен быть только один open и один rollback
    assert calls == ['open', 'rollback']

def test_auto_transaction_depth_multi_thread(monkeypatch):
    calls = []
    results = []
    def worker():
        patch_executor(monkeypatch, calls=calls, results=results)
        @auto_transaction()
        def inner():
            return 'ok'
        @auto_transaction()
        def outer():
            return inner()
        outer()

    number_of_threads = 5
    threads = [threading.Thread(target=worker) for _ in range(number_of_threads)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert results.count('commit') == number_of_threads
    assert len([r for r in results if isinstance(r, int)]) == number_of_threads


def test_auto_transaction_always_rollback(monkeypatch):
    calls = []
    patch_executor(monkeypatch, calls=calls)

    @auto_transaction()
    def inner():
        return 'ok'

    @auto_transaction(always_rollback=True)
    def outer():
        return inner()

    result = outer()
    assert result == 'ok'
    assert calls == ['open', 'rollback']
