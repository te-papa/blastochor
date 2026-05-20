class OutputRow():
    def __init__(self, **kwargs):
        self.data = kwargs.get("data")
        self.pointer = kwargs.get("pointer")
        self.write_pointer = kwargs.get("write_pointer")
        self.pid = kwargs.get("record_pid")
        self.explode = {"explode_on": kwargs.get("explode_on"),
                        "explode_ordinal": kwargs.get("explode_ordinal"),
                        "explode_parent_value": kwargs.get("explode_parent_value")}
        self.group_role = kwargs.get("group_role")

        self.rules = kwargs.get("rules")
        self.write_out = True

        self.values = {}