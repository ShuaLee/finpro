CONSTRAINT_TEMPLATES = {
    "string": [
        {
            "name": "max_length",
            "label": "Max Length",
            "type": "integer",
            "default": 100,
            "min": 1,
            "max": 255,
            "editable": False,
        },
    ],

    "decimal": [
        {
            "name": "decimal_places",
            "label": "Decimal Places",
            "type": "integer",
            "default": 4,
            "min": 0,
            "max": 20,
            "editable": True,
        },
        {
            "name": "max_value",
            "label": "Maximum Value",
            "type": "decimal",
            "default": None,
            "min": None,
            "max": None,
            "editable": False,
        },
        {
            "name": "min_value",
            "label": "Minimum Value",
            "type": "decimal",
            "default": None,
            "min": None,
            "max": None,
            "editable": False,
        },
    ],

    "integer": [
        {
            "name": "max_value",
            "label": "Maximum Value",
            "type": "integer",
            "default": None,
            "editable": False,
        },
        {
            "name": "min_value",
            "label": "Minimum Value",
            "type": "integer",
            "default": None,
            "editable": False,
        },
    ],

    "date": [
        {
            "name": "min_date",
            "label": "Earliest Date",
            "type": "date",
            "default": None,
            "editable": False,
        },
        {
            "name": "max_date",
            "label": "Latest Date",
            "type": "date",
            "default": None,
            "editable": False,
        },
    ],

    "boolean": [],

    "url": [
        {
            "name": "max_length",
            "label": "Max Length",
            "type": "integer",
            "default": 200,
            "min": 1,
            "max": 500,
            "editable": False,
        },
    ],
}
