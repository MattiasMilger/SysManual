# sysmanual_schema.py

SYS_MANUAL_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "required": ["id", "name", "description", "categories"],
    "properties": {
        "id": {"type": "string"},
        "name": {"type": "string"},
        "description": {"type": "string"},
        "theme": {
            "type": "object",
            "properties": {
                "primary": {"type": "string"},
                "accent": {"type": "string"}
            }
        },
        "categories": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["id", "name", "entries"],
                "properties": {
                    "id": {"type": "string"},
                    "name": {"type": "string"},
                    "entries": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "required": ["id", "name", "description"],
                            "properties": {
                                "id": {"type": "string"},
                                "name": {"type": "string"},
                                "description": {"type": "string"},
                                "content": {"type": "object"},
                                "examples": {
                                    "type": "array",
                                    "items": {
                                        "oneOf": [
                                            {"type": "string"},
                                            {
                                                "type": "object",
                                                "required": ["command"],
                                                "properties": {
                                                    "command": {"type": "string"},
                                                    "description": {"type": "string"}
                                                }
                                            }
                                        ]
                                    }
                                },
                                "details": {
                                    "type": "array",
                                    "items": {
                                        "type": "object",
                                        "properties": {
                                            "label": {"type": "string"},
                                            "value": {"type": "string"}
                                        }
                                    }
                                },
                                "notes": {"type": "string"}
                            }
                        }
                    }
                }
            }
        }
    }
}