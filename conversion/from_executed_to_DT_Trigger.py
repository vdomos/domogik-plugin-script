def from_executed_to_DT_Trigger(x):
    # low - high translated to 0 - 1
    if x == "executed":
        return 1
    else:
        return 0

