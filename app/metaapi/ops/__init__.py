from app.metaapi.ops.closing import (
    close_all_positions,
    close_partial,
)
from app.metaapi.ops.modification import (
    modify_position,
    move_to_breakeven,
)
from app.metaapi.ops.trailing import implement_trailing_stop


class PositionManager:
    """
    Manages position modifications and advanced position operations.
    Refactored to delegate to sub-modules.
    """

    modify_position = staticmethod(modify_position)
    move_to_breakeven = staticmethod(move_to_breakeven)
    implement_trailing_stop = staticmethod(implement_trailing_stop)
    close_partial = staticmethod(close_partial)
    close_all_positions = staticmethod(close_all_positions)
