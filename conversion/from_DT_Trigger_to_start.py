def from_DT_Trigger_to_start(x):
    # 0 - 1 translated to low / high
    if str(x) == "1":
        return "start"
    else:
        return "stop"

