import os
import sys
import gc
from typing import Optional
from app.core.logging import logger

try:
    import psutil
    _HAS_PSUTIL = True
except ImportError:
    _HAS_PSUTIL = False


def get_current_rss_mb() -> float:
    """
    Returns the current process Resident Set Size (RSS) in Megabytes.
    Works across Windows, Linux (Render), and macOS without hard dependency on psutil.
    """
    if _HAS_PSUTIL:
        try:
            proc = psutil.Process(os.getpid())
            return round(proc.memory_info().rss / (1024 * 1024), 2)
        except Exception:
            pass

    # Linux / Render procfs fallback
    if sys.platform.startswith("linux"):
        try:
            with open("/proc/self/status", "r") as f:
                for line in f:
                    if line.startswith("VmRSS:"):
                        # Format: VmRSS:     123456 kB
                        parts = line.split()
                        if len(parts) >= 2:
                            return round(float(parts[1]) / 1024.0, 2)
        except Exception:
            pass

    # Unix resource fallback
    try:
        import resource
        rusage = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        # On Linux ru_maxrss is in KiB; on macOS it is in bytes
        if sys.platform == "darwin":
            return round(rusage / (1024 * 1024), 2)
        return round(rusage / 1024, 2)
    except Exception:
        pass

    return 0.0


def log_memory(stage: str, extra: Optional[str] = None) -> float:
    """
    Log current memory consumption with a stage tag.
    Returns current RSS in MB.
    """
    rss = get_current_rss_mb()
    msg = f"[Memory Audit] {stage}: {rss:.1f} MB RSS"
    if extra:
        msg += f" ({extra})"
    logger.info(msg)
    return rss


def collect_garbage_and_log(stage: str) -> float:
    """
    Explicitly trigger Python garbage collection and log resulting memory.
    """
    gc.collect()
    return log_memory(stage)
