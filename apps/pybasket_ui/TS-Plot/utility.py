from pydantic import BaseModel, AnyHttpUrl, ValidationError


class ModelURL(BaseModel):
    """_summary_

    Args:
        BaseModel (_type_): _description_

    example usage:
    try:
        ModelURL(url='ftp://invalid.url')
    except ValidationError as e:
        print(e)
    """

    url: AnyHttpUrl


def get_labels(obj, variable):
    """docstring"""
    try:
        var_tooltip_label = str(obj.variable_metadata[variable]["long_name"])
    except KeyError:
        var_tooltip_label = str(obj.variable_metadata[variable]["standard_name"])
    try:
        units = list({"unit", "units"}.intersection(obj.variable_metadata[variable]))[0]
        y_axis_label = " ".join(
            [var_tooltip_label, "[", obj.variable_metadata[variable][units], "]"]
        )
    except IndexError:
        print("no units found")
        y_axis_label = var_tooltip_label
    var_label = "@{" + str(variable + "}")
    return [var_label, var_tooltip_label, y_axis_label]
