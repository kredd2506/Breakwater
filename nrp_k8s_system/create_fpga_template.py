#!/usr/bin/env python3
"""
Create FPGA Template
===================

Create a comprehensive FPGA template for the knowledge base using the
information extracted from the correct NRP documentation page.
"""

import os
import sys
import json
import logging
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_fpga_template():
    """Create comprehensive FPGA template from NRP documentation."""
    try:
        from nrp_k8s_system.core.enhanced_knowledge_base import EnhancedKnowledgeBase
        from nrp_k8s_system.agents.deep_extractor_agent import ExtractionTemplate

        kb = EnhancedKnowledgeBase()

        # Create comprehensive FPGA template based on the extracted information
        fpga_template = ExtractionTemplate(
            title="Alveo FPGA and ESnet SmartNIC Workflow on NRP",
            description="Complete administrative workflow for flashing and managing Alveo U55C FPGAs and ESnet SmartNIC on NRP cluster infrastructure",
            resource_type="fpga",
            yaml_content="""# FPGA Device Verification
# Check PCIe hardware connection
lspci | grep -i fpga

# Xilinx Runtime Tools setup
source /opt/xilinx/xrt/setup.sh
xbmgmt examine

# ESnet SmartNIC verification
lspci | grep -i nic

# For flashing operations (admin only):
# Use Vivado software on admin Coder instance
# Access FPGA Flashing template in admin environment""",
            usage_context="Administrative workflow for FPGA management on NRP cluster. Requires cluster administrator privileges and specialized knowledge of FPGA hardware configuration.",
            warnings=[
                "FPGA flashing operations require administrator privileges",
                "Only use Vivado software on designated admin Coder instances",
                "Incorrect flashing can damage FPGA hardware permanently",
                "ESnet SmartNIC has different requirements from standard Alveo workflow"
            ],
            cautions=[
                "This is administrative documentation for cluster operators only",
                "FPGA operations can affect cluster stability and user workloads",
                "Always verify device readiness before attempting operations",
                "Follow AMD/Xilinx official flashing guides for detailed procedures"
            ],
            notes=[
                "32 U55C FPGAs available on PNRP Nodes at SDSC",
                "ESnet SmartNIC only requires lspci visibility",
                "Detailed inventory tracked in FPGA Inventory spreadsheet",
                "XRT tools required for device verification"
            ],
            dangers=[
                "Improper FPGA flashing can permanently brick devices",
                "Administrative access required - unauthorized users cannot perform these operations",
                "Hardware modifications can affect entire cluster performance"
            ],
            examples=[
                "lspci verification: Check PCIe device enumeration",
                "XRT examination: Use xbmgmt examine for device status",
                "Vivado flashing: Access through admin Coder FPGA template",
                "SmartNIC check: Verify ESnet device visibility"
            ],
            best_practices=[
                "Always verify device readiness with XRT tools before operations",
                "Use designated admin Coder instances for FPGA flashing",
                "Follow official AMD/Xilinx documentation for flashing procedures",
                "Maintain updated FPGA inventory tracking",
                "Test device functionality after any configuration changes",
                "Coordinate with cluster administrators before hardware operations"
            ],
            common_mistakes=[
                "Attempting FPGA operations without administrator privileges",
                "Using wrong flashing procedures for ESnet SmartNIC",
                "Not verifying XRT tool setup before device operations",
                "Confusing Alveo U55C workflow with SmartNIC requirements",
                "Skipping device readiness verification steps"
            ],
            source_url="https://nrp.ai/documentation/admindocs/cluster/fpga/",
            api_version="N/A",
            namespace_requirements=["admin"],
            resource_requirements={
                "admin_access": "required",
                "vivado_software": "required",
                "xrt_tools": "required",
                "fpga_hardware": "Alveo U55C or ESnet SmartNIC"
            },
            dependencies=[
                "Xilinx Runtime Tools (XRT)",
                "Vivado software suite",
                "Administrator Coder instance access",
                "PCIe hardware enumeration tools"
            ],
            confidence_score=0.98,
            extraction_method="manual_from_correct_documentation",
            validation_status="verified_from_official_nrp_docs"
        )

        # Add template to knowledge base
        template_id = kb.add_template(fpga_template)
        kb.save()

        print(f"✅ Created FPGA template: {template_id}")
        print(f"📄 Title: {fpga_template.title}")
        print(f"🔗 Source: {fpga_template.source_url}")
        print(f"⚠️  Warnings: {len(fpga_template.warnings)}")
        print(f"🔧 Best Practices: {len(fpga_template.best_practices)}")

        # Test search for FPGA query
        print(f"\n🔍 Testing search for FPGA query...")
        results = kb.search_templates("How do users flash an Alveo FPGA via the ESnet SmartNIC workflow", limit=3)
        print(f"📊 Search results: {len(results)} templates found")

        for i, result in enumerate(results, 1):
            template = result.template.template
            print(f"  {i}. {template.title}")
            print(f"     Relevance: {result.relevance_score:.3f}")
            print(f"     Source: {template.source_url}")

        return True

    except Exception as e:
        print(f"❌ Failed to create FPGA template: {e}")
        import traceback
        traceback.print_exc()
        return False

def create_fpga_yaml_examples():
    """Create FPGA-specific YAML examples storage."""
    try:
        # Create FPGA examples directory
        fpga_examples_dir = Path("nrp_k8s_system/cache/yaml_examples/fpga")
        fpga_examples_dir.mkdir(parents=True, exist_ok=True)

        # FPGA verification scripts
        fpga_scripts = {
            "fpga_verification.sh": """#!/bin/bash
# FPGA Device Verification Script
# For NRP cluster administrators only

echo "=== FPGA Device Verification ==="

# Check PCIe hardware connection
echo "1. Checking PCIe FPGA devices..."
lspci | grep -i fpga
if [ $? -eq 0 ]; then
    echo "✅ FPGA devices found in PCIe enumeration"
else
    echo "❌ No FPGA devices found"
    exit 1
fi

# Setup Xilinx Runtime Tools
echo "2. Setting up Xilinx Runtime Tools..."
if [ -f "/opt/xilinx/xrt/setup.sh" ]; then
    source /opt/xilinx/xrt/setup.sh
    echo "✅ XRT environment loaded"
else
    echo "❌ XRT tools not found"
    exit 1
fi

# Examine devices with XRT
echo "3. Examining FPGA devices with XRT..."
xbmgmt examine
if [ $? -eq 0 ]; then
    echo "✅ XRT device examination completed"
else
    echo "⚠️  Device examination failed - may need flashing"
fi

echo "=== Verification Complete ==="
""",

            "esnet_smartnic_check.sh": """#!/bin/bash
# ESnet SmartNIC Verification Script
# For NRP cluster administrators only

echo "=== ESnet SmartNIC Verification ==="

# Check for ESnet SmartNIC devices
echo "1. Checking for ESnet SmartNIC devices..."
lspci | grep -i nic | grep -i esnet
if [ $? -eq 0 ]; then
    echo "✅ ESnet SmartNIC devices found"
else
    echo "❌ No ESnet SmartNIC devices found"
    lspci | grep -i nic
fi

echo "=== SmartNIC Check Complete ==="
"""
        }

        # Save scripts
        for filename, content in fpga_scripts.items():
            script_file = fpga_examples_dir / filename
            with open(script_file, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"📄 Created: {script_file}")

        # Create metadata
        metadata = {
            "fpga_examples": {
                "fpga_verification": {
                    "file": "fpga/fpga_verification.sh",
                    "title": "FPGA Device Verification Script",
                    "description": "Complete verification workflow for Alveo U55C FPGAs",
                    "requirements": ["admin_access", "xrt_tools"],
                    "warnings": ["Administrator privileges required"]
                },
                "esnet_smartnic_check": {
                    "file": "fpga/esnet_smartnic_check.sh",
                    "title": "ESnet SmartNIC Verification",
                    "description": "Verification script for ESnet SmartNIC devices",
                    "requirements": ["admin_access"],
                    "warnings": ["Cluster administrator access only"]
                }
            },
            "topics": {
                "fpga_management": ["fpga_verification", "esnet_smartnic_check"],
                "admin_operations": ["fpga_verification", "esnet_smartnic_check"]
            },
            "source_documentation": "https://nrp.ai/documentation/admindocs/cluster/fpga/",
            "created": "2025-01-15",
            "last_updated": "2025-01-15"
        }

        metadata_file = Path("nrp_k8s_system/cache/yaml_examples") / "fpga_examples_metadata.json"
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2)

        print(f"📋 Created metadata: {metadata_file}")
        return True

    except Exception as e:
        print(f"❌ Failed to create FPGA examples: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Create comprehensive FPGA knowledge base entries."""
    print("Creating FPGA Knowledge Base Entries")
    print("="*50)

    try:
        # Create FPGA template
        template_success = create_fpga_template()

        # Create FPGA examples
        examples_success = create_fpga_yaml_examples()

        print("\n" + "="*50)
        print("RESULTS SUMMARY")
        print("="*50)
        print(f"FPGA Template: {'✅ SUCCESS' if template_success else '❌ FAILED'}")
        print(f"FPGA Examples: {'✅ SUCCESS' if examples_success else '❌ FAILED'}")

        if template_success and examples_success:
            print(f"\n🎉 FPGA knowledge base entries created successfully!")
            print(f"📚 The system will now provide comprehensive answers for:")
            print(f"   - Alveo FPGA flashing workflows")
            print(f"   - ESnet SmartNIC management")
            print(f"   - FPGA device verification procedures")
            print(f"   - Administrative requirements and warnings")
            print(f"\n🔗 All information sourced from: https://nrp.ai/documentation/admindocs/cluster/fpga/")
        else:
            print(f"\n⚠️  Some entries failed to create - check errors above")

    except Exception as e:
        print(f"❌ Main execution failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()