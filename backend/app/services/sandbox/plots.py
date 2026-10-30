"""Bounded PNG-only transport for figures generated inside the student container."""

import base64
import binascii
import re
import struct
import json
import math

MAX_PLOTS = 3
MAX_PLOT_BYTES = 256 * 1024
MAX_PLOT_BASE64 = ((MAX_PLOT_BYTES + 2) // 3) * 4
MAX_PLOT_WIRE_BYTES = MAX_PLOTS * (MAX_PLOT_BASE64 + 64)
MAX_CHART_DATA_BYTES = 32 * 1024
MAX_PLOT_WIRE_BYTES += MAX_CHART_DATA_BYTES * 2
PREFIX = b"\x1eANALYTICS_PNG:"
FRAME = re.compile(re.escape(PREFIX) + rb"([A-Za-z0-9+/=]+)\n")
DATA_PREFIX = b"\x1eANALYTICS_CHART:"
DATA_FRAME = re.compile(re.escape(DATA_PREFIX) + rb"([A-Za-z0-9+/=]+)\n")


def validate_chart_data(value):
    if not isinstance(value, dict) or len(json.dumps(value).encode()) > MAX_CHART_DATA_BYTES:
        raise ValueError("Invalid chart metadata")
    series = value.get("series")
    if not isinstance(series, list) or len(series) > 10:
        raise ValueError("Invalid chart series")
    for item in series:
        if not isinstance(item, dict) or item.get("kind") not in {"bar", "line"}:
            raise ValueError("Invalid chart kind")
        labels, values = item.get("labels"), item.get("values")
        if not isinstance(labels, list) or not isinstance(values, list) or len(labels) != len(values) or len(values) > 100:
            raise ValueError("Invalid chart coordinates")
        if any(not isinstance(v, str) or len(v) > 256 for v in labels):
            raise ValueError("Invalid chart labels")
        if any(not isinstance(v, (int, float)) or isinstance(v, bool) or not math.isfinite(v) for v in values):
            raise ValueError("Invalid chart values")
        if any(not isinstance(item.get(key), str) or len(item[key]) > 256 for key in ("title", "xlabel", "ylabel")):
            raise ValueError("Invalid chart captions")
        if not isinstance(item.get("zero_baseline"), bool):
            raise ValueError("Invalid chart baseline")
    return value


def validate_png(value: str) -> str:
    if len(value) > MAX_PLOT_BASE64:
        raise ValueError("Plot exceeds PNG size limit")
    try:
        raw = base64.b64decode(value, validate=True)
    except (ValueError, binascii.Error):
        raise ValueError("Invalid PNG encoding") from None
    if len(raw) > MAX_PLOT_BYTES or len(raw) < 33 or raw[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError("Only PNG figures are supported")
    if raw[12:16] != b"IHDR":
        raise ValueError("Invalid PNG header")
    width, height = struct.unpack(">II", raw[16:24])
    if not (0 < width <= 2000 and 0 < height <= 2000):
        raise ValueError("Figure dimensions exceed limits")
    return value


def extract_plot_output(output: bytes) -> tuple[bytes, list[str], bool, list[dict]]:
    plots = []
    limited = False

    def consume(match):
        nonlocal limited
        try:
            value = validate_png(match[1].decode("ascii"))
            if len(plots) >= MAX_PLOTS:
                limited = True
            else:
                plots.append(value)
        except ValueError:
            limited = True
        return b""

    text = FRAME.sub(consume, output)
    chart_data = []

    def consume_data(match):
        nonlocal limited
        try:
            if len(match[1]) > MAX_CHART_DATA_BYTES * 2 or len(chart_data) >= MAX_PLOTS:
                raise ValueError("Too much chart data")
            value = json.loads(base64.b64decode(match[1], validate=True))
            chart_data.append(validate_chart_data(value))
        except (ValueError, binascii.Error, UnicodeDecodeError):
            limited = True
        return b""

    text = DATA_FRAME.sub(consume_data, text)
    return text, plots, limited, chart_data


def extract_plots(output: bytes) -> tuple[bytes, list[str], bool]:
    text, plots, limited, _ = extract_plot_output(output)
    return text, plots, limited


def python_with_plots(code: str) -> str:
    """This wrapper runs INSIDE the same restricted, disposable container.

    Figures cross stdout as PNG frames, not host files, paths, HTML or SVG.
    Like stdout, frames are untrusted student output, never trusted instructions.
    """
    return f'''
import sys as _sys
import io as _io
import base64 as _base64
import json as _json
import math as _math
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as _plt
_plot_count = 0

def _show(*args, **kwargs):
    global _plot_count
    for number in _plt.get_fignums():
        if _plot_count >= {MAX_PLOTS}:
            raise RuntimeError("Maximum {MAX_PLOTS} figures per run")
        figure = _plt.figure(number)
        width, height = figure.get_size_inches() * figure.dpi
        if max(width, height) > 2000:
            raise RuntimeError("Figure dimensions exceed 2000 pixels")
        image = _io.BytesIO()
        figure.savefig(image, format="png")
        if image.tell() > {MAX_PLOT_BYTES}:
            raise RuntimeError("Figure PNG exceeds {MAX_PLOT_BYTES} bytes")
        series = []
        for axis in figure.axes:
            for container in axis.containers:
                if not hasattr(container, "datavalues"):
                    continue
                horizontal = container.orientation == "horizontal"
                ticks = axis.get_yticklabels() if horizontal else axis.get_xticklabels()
                series.append(dict(kind="bar", labels=[tick.get_text() for tick in ticks],
                    values=[float(v) for v in container.datavalues], title=axis.get_title(),
                    xlabel=axis.get_xlabel(), ylabel=axis.get_ylabel(),
                    zero_baseline=_math.isclose(float(axis.get_xlim()[0] if horizontal else axis.get_ylim()[0]), 0, abs_tol=1e-8)))
            for line in axis.lines:
                series.append(dict(kind="line", labels=[str(v) for v in line.get_xdata()],
                    values=[float(v) for v in line.get_ydata()], title=axis.get_title(),
                    xlabel=axis.get_xlabel(), ylabel=axis.get_ylabel(), zero_baseline=False))
        metadata = _json.dumps(dict(series=series), ensure_ascii=False).encode("utf-8")
        if len(metadata) > {MAX_CHART_DATA_BYTES}:
            raise RuntimeError("Chart metadata exceeds limits")
        _sys.stdout.write("\\x1eANALYTICS_PNG:" + _base64.b64encode(image.getvalue()).decode("ascii") + "\\n")
        _sys.stdout.write("\\x1eANALYTICS_CHART:" + _base64.b64encode(metadata).decode("ascii") + "\\n")
        _sys.stdout.flush()
        _plot_count += 1
        _plt.close(figure)

_plt.show = _show
exec(compile({code!r}, "<student>", "exec"), {{"__name__": "__main__"}})
'''
