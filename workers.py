"""Worker setup only. Recognition and marking remain in ChilliMark.py."""
import copy
import os


def copy_parameters(params):
    """Isolate mutable calibration fields without copying the full template image.

    Recognition assigns page-specific arrays/values and mutates Python containers.
    Existing NumPy calibration contours and the template are only read by workers.
    """
    private = copy.copy(params)
    for name, value in vars(params).items():
        if isinstance(value, (list, dict, set)):
            setattr(private, name, copy.deepcopy(value))
    return private


def worker_count(page_count):
    # A 4800 x 6840 RGB scan alone is ~94 MiB, before OpenCV intermediates.
    return max(1, min(2, os.cpu_count() or 1, page_count))


def process_student(student):
    """Keep errors attached to the affected task without changing Student.get."""
    try:
        return student.get()
    except Exception as exc:
        raise RuntimeError(f'Page {student.index + 1}: {exc}') from exc
