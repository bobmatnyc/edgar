"""Script to capture generated code for inspection."""
import asyncio
import os
from edgar.services import Sonnet4_5Service, OpenRouterClient, ContextManager


async def main():
    weather_strategy = {
        "data_source_type": "REST_API",
        "response_format": "JSON",
        "extraction_patterns": {
            "temperature": {
                "source_path": "$.main.temp",
                "description": "Temperature in Kelvin",
                "optional": False,
                "default_value": None,
            },
            "humidity": {
                "source_path": "$.main.humidity",
                "description": "Humidity percentage",
                "optional": False,
                "default_value": None,
            },
        },
        "transformations": [
            {
                "field": "temperature",
                "operation": "unit_conversion",
                "formula": "value - 273.15",
                "description": "Convert Kelvin to Celsius",
            }
        ],
        "validation_rules": {
            "temperature": {
                "type": "float",
                "constraints": {"required": True, "min": -50, "max": 50},
                "error_handling": "fail",
                "default_value": None,
            },
            "humidity": {
                "type": "int",
                "constraints": {"required": True, "min": 0, "max": 100},
                "error_handling": "fail",
                "default_value": None,
            },
        },
        "cross_field_validations": [],
        "error_handling": {
            "missing_fields": "fail",
            "invalid_types": "fail",
            "validation_failures": "fail",
        },
        "assumptions": ["Temperature is provided in Kelvin"],
    }

    api_key = os.getenv("OPENROUTER_API_KEY")
    client = OpenRouterClient(api_key=api_key)
    context = ContextManager()
    service = Sonnet4_5Service(client=client, context=context)

    print("Generating code...")
    code = await service.generate_code(strategy=weather_strategy)
    
    with open("generated_weather_extractor.py", "w") as f:
        f.write(code)
    
    print(f"✅ Generated {len(code)} chars")
    print("📝 Saved to generated_weather_extractor.py")


if __name__ == "__main__":
    asyncio.run(main())
