import ast
import copy
import heapq
import multiprocessing
import multiprocessing.pool
from pathlib import Path
import random
import sys
import threading
import time
from types import SimpleNamespace
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from workers import copy_parameters, worker_count, process_student


class WorkerTests(unittest.TestCase):
    def test_parameters_are_private_without_copying_template(self):
        template = object()
        params = SimpleNamespace(template=template, key={0: 'A'}, row_avg=[1, 2], nested=[[3]])
        first, second = copy_parameters(params), copy_parameters(params)
        first.key[0] = 'B'
        first.row_avg.append(4)
        first.nested[0][0] = 9
        self.assertEqual(second.key, {0: 'A'})
        self.assertEqual(params.row_avg, [1, 2])
        self.assertEqual(second.nested, [[3]])
        self.assertIs(first.template, template)

    def test_worker_limit(self):
        for cpus, expected in ((None, 1), (1, 1), (8, 2), (64, 2)):
            with patch('workers.os.cpu_count', return_value=cpus):
                self.assertEqual(worker_count(100), expected)
                self.assertEqual(worker_count(1), 1)

    def test_errors_include_page_and_keep_cause(self):
        cause = ValueError('failed rendering')
        def fail():
            raise cause
        with self.assertRaisesRegex(RuntimeError, 'Page 8: failed rendering') as caught:
            process_student(SimpleNamespace(index=7, get=fail))
        self.assertIs(caught.exception.__cause__, cause)

    def run_main(self, seed=0, failing_page=None):
        """Exercise the actual main() with real threads and a simulated Tk event loop.

        GUI/native rendering are replaced; recognition code is never executed or edited.
        Every simulated Tk method enforces main-thread access.
        """
        main_thread = threading.get_ident()
        events, errors, delivered, finished = [], [], [], []
        active = peak = 0
        lock = threading.Lock()
        params = SimpleNamespace(key={0: 'A'}, row_avg=[0], template=object())

        def on_main():
            self.assertEqual(threading.get_ident(), main_thread)

        class Root:
            clock = 0
            sequence = 0
            def after(self, delay, callback):
                on_main()
                self.sequence += 1
                heapq.heappush(events, (self.clock + delay, self.sequence, callback))
            def mainloop(self):
                on_main()
                deadline = time.monotonic() + 10
                while not delivered and not errors:
                    if time.monotonic() > deadline:
                        raise AssertionError('Workers or GUI callback stalled')
                    if events:
                        self.clock, _, callback = heapq.heappop(events)
                        callback()
                    time.sleep(.001)

        root = Root()
        gui = SimpleNamespace(root=root, filename='exam.pdf', home=on_main, marking=on_main,
                              poll_progress=on_main)

        class Document:
            def __enter__(self): return self
            def __exit__(self, *args): pass
            def __len__(self): return 24

        class Student:
            def __init__(self, filename, index, private, queue):
                on_main()
                self.index, self.params = index, private
            def get(self):
                nonlocal active, peak
                self_outer.assertNotEqual(threading.get_ident(), main_thread)
                with lock:
                    active += 1
                    peak = max(peak, active)
                try:
                    self.params.row_avg[0] = self.index
                    time.sleep(random.Random(seed * 100 + self.index).random() / 200)
                    if self.index == failing_page:
                        raise ValueError('worker failed')
                    self_outer.assertEqual(self.params.row_avg, [self.index])
                    with lock:
                        finished.append(self.index)
                    return (self.index, self.params.row_avg[0])
                finally:
                    with lock: active -= 1

        self_outer = self
        def handle_results(result, students, received_gui, received_params):
            on_main()
            self.assertIs(received_gui, gui)
            self.assertIs(received_params, params)
            delivered.extend(result)
        def showerror(title, message):
            on_main()
            errors.append(message)

        source = Path(__file__).resolve().parents[1] / 'ChilliMark.py'
        node = next(n for n in ast.parse(source.read_text()).body
                    if isinstance(n, ast.FunctionDef) and n.name == 'main')
        namespace = dict(Gui=SimpleNamespace(Gui=lambda: gui), load_inputs=lambda g: params,
                         pymupdf=SimpleNamespace(open=lambda filename: Document()),
                         tkinter=SimpleNamespace(messagebox=SimpleNamespace(showerror=showerror)),
                         multiprocessing=multiprocessing, Student=Student,
                         copy_parameters=copy_parameters, worker_count=worker_count,
                         process_student=process_student, handle_results=handle_results)
        exec(compile(ast.Module(body=[node], type_ignores=[]), str(source), 'exec'), namespace)
        namespace['main']()
        self.assertEqual(params.row_avg, [0])
        self.assertLessEqual(peak, 2)
        return delivered, errors, finished

    def test_completion_order_does_not_change_recorded_results(self):
        orders = []
        for seed in range(4):
            result, errors, finished = self.run_main(seed)
            self.assertEqual(result, [(i, i) for i in range(24)])
            self.assertFalse(errors)
            orders.append(finished)
        self.assertGreater(len({tuple(order) for order in orders}), 1)

    def test_worker_error_is_reported_on_gui_thread_without_export(self):
        result, errors, _ = self.run_main(failing_page=7)
        self.assertEqual(result, [])
        self.assertEqual(len(errors), 1)
        self.assertIn('Page 8: worker failed', errors[0])


if __name__ == '__main__':
    unittest.main()
