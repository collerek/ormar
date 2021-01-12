import sys
from typing import Any, TYPE_CHECKING

if sys.version_info < (3, 7):  # pragma: no cover
    if TYPE_CHECKING:

        class ForwardRef:

            _gorg = None

            def __init__(self, args: Any) -> None:
                pass

            def _eval_type(self, globalns: Any, localns: Any) -> Any:
                pass

    else:
        from typing import _ForwardRef as ForwardRef
else:
    from typing import ForwardRef

ForwardRef = ForwardRef
