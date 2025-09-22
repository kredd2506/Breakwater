import asyncio
from fastmcp import Client

# Create client for the enhanced server
client = Client("http://localhost:8001/mcp")

async def test_enhanced_server():
    """Test all capabilities of the enhanced server"""

    # Sample data for testing
    sample_data = {
        "user": {
            "name": "Alice Smith",
            "age": 28,
            "email": "alice@example.com",
            "preferences": {
                "theme": "dark",
                "notifications": True,
                "language": "en"
            }
        },
        "project": {
            "name": "FastMCP Demo",
            "version": "1.0.0",
            "status": "active",
            "tags": ["demo", "mcp", "formatting"]
        },
        "null_value": None,
        "empty_string": ""
    }

    async with client:
        print("Testing Enhanced FastMCP Server")
        print("=" * 50)

        # Test 1: YAML formatting with metadata
        print("\n1. YAML Formatting with Metadata:")
        yaml_result = await client.call_tool("format_data_yaml", {
            "data": sample_data,
            "indent": 4,
            "sort_keys": True,
            "add_metadata": True
        })
        print(yaml_result.data)

        # Test 2: JSON formatting without metadata
        print("\n2. JSON Formatting without Metadata:")
        json_result = await client.call_tool("format_data_json", {
            "data": sample_data,
            "indent": 2,
            "sort_keys": False,
            "add_metadata": False
        })
        print(json_result.data)

        # Test 3: Data transformation
        print("\n3. Data Transformation (uppercase keys, remove nulls):")
        transform_result = await client.call_tool("transform_data", {
            "data": sample_data,
            "transformations": ["uppercase_keys", "remove_nulls"]
        })
        print(f"Transformed data: {transform_result.data}")

        # Test 4: Structured report
        print("\n4. Structured Report:")
        report_result = await client.call_tool("create_structured_report", {
            "title": "User and Project Data Analysis",
            "data": sample_data,
            "format_type": "yaml",
            "include_summary": True
        })
        print(report_result.data)

        # Test 5: Get server configuration
        print("\n5. Server Configuration:")
        config_result = await client.read_resource("config://server")
        print(f"Server config: {config_result}")

        # Test 6: Get formatting examples
        print("\n6. Formatting Examples:")
        examples_result = await client.read_resource("examples://formatting")
        print(f"Examples: {examples_result}")

        print("\nAll tests completed successfully!")

if __name__ == "__main__":
    asyncio.run(test_enhanced_server())