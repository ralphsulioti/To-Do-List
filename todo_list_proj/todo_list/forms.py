from typing import ClassVar

from django import forms

from .models import Item, List


class ListForm(forms.ModelForm):
    """Validates a new list's name: stripped, non-blank, at most 200 characters."""

    class Meta:
        model = List
        fields = ("list_name",)
        error_messages: ClassVar[dict[str, dict[str, str]]] = {
            "list_name": {
                "required": "Enter a list name.",
                "max_length": "List names can be at most %(limit_value)d characters "
                "(this one has %(show_value)d).",
            }
        }


class ItemForm(forms.ModelForm):
    """Validates a new item's description: stripped, non-blank, at most 200 characters."""

    class Meta:
        model = Item
        fields = ("item_descr",)
        error_messages: ClassVar[dict[str, dict[str, str]]] = {
            "item_descr": {
                "required": "Enter an item description.",
                "max_length": "Item descriptions can be at most %(limit_value)d "
                "characters (this one has %(show_value)d).",
            }
        }
