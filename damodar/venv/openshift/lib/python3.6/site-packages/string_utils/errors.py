# -*- coding: utf-8 -*-

from typing import Any


class InvalidInputError(TypeError):
    """
    Custom error raised when received object is not a string as expected.
    """

    def __init__(self, input_data: Any):
        """
        :param input_data: Any received object
        """
        type_name = type(input_data).__name__
        msg = 'Expected "str", received "{}"'.format(type_name)
        super().__init__(msg)
