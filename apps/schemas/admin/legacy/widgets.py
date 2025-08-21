# from django import forms


# class DisabledOptionSelect(forms.Select):
#     def __init__(self, *args, disabled_values=None, **kwargs):
#         self.disabled_values = set(disabled_values or [])
#         super().__init__(*args, **kwargs)

#     def create_option(self, name, value, label, selected, index, subindex=None, attrs=None):
#         option = super().create_option(name, value, label, selected,
#                                        index, subindex=subindex, attrs=attrs)
#         if value in self.disabled_values:
#             option['attrs']['disabled'] = True
#         return option
