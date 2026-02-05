"""Validation script for dashboard UI."""

import sys
from pathlib import Path

# Add src to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

def validate_dashboard_files():
    """Validate that dashboard files exist."""
    print("Validating dashboard files...")
    
    ui_dir = Path(__file__).parent
    required_files = [
        "dashboard.html",
        "dashboard_api.py",
        "README.md",
    ]
    
    missing = []
    for filename in required_files:
        filepath = ui_dir / filename
        if not filepath.exists():
            missing.append(filename)
    
    if missing:
        print(f"❌ Missing files: {', '.join(missing)}")
        return False
    
    print("✅ All dashboard files exist")
    return True


def validate_dashboard_html():
    """Validate dashboard HTML structure."""
    print("\nValidating dashboard HTML...")
    
    ui_dir = Path(__file__).parent
    html_path = ui_dir / "dashboard.html"
    
    with open(html_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    required_elements = [
        "<!DOCTYPE html>",
        "<html",
        "<head>",
        "<body>",
        "Backup Monitoring Dashboard",
        "filters",
        "dashboardContent",
        "applyFilters",
        "resetFilters",
    ]
    
    missing = []
    for element in required_elements:
        if element.lower() not in content.lower():
            missing.append(element)
    
    if missing:
        print(f"❌ Missing HTML elements: {', '.join(missing)}")
        return False
    
    print("✅ Dashboard HTML structure is valid")
    return True


def validate_api_server():
    """Validate API server can be imported."""
    print("\nValidating API server...")
    
    try:
        from backup_monitoring.integration.mocks import MockUIAdapter
        from ui.dashboard_api import create_api_server
        
        # Test that we can create a server
        ui_adapter = MockUIAdapter()
        server = create_api_server(ui_adapter, port=9999)
        server.shutdown()
        
        print("✅ API server can be created")
        return True
        
    except Exception as e:
        print(f"❌ API server validation failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def validate_integration_layer_usage():
    """Validate that dashboard uses Integration Layer."""
    print("\nValidating Integration Layer usage...")
    
    ui_dir = Path(__file__).parent
    api_path = ui_dir / "dashboard_api.py"
    
    with open(api_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check that it imports from integration layer
    if "from backup_monitoring.integration" not in content:
        print("❌ API server does not use Integration Layer")
        return False
    
    if "UIAdapter" not in content:
        print("❌ API server does not use UIAdapter")
        return False
    
    print("✅ Dashboard uses Integration Layer correctly")
    return True


def main():
    """Run all validation checks."""
    print("=" * 60)
    print("CORE-009 Validation: Basic Dashboard (UI)")
    print("=" * 60)
    
    results = [
        validate_dashboard_files(),
        validate_dashboard_html(),
        validate_api_server(),
        validate_integration_layer_usage(),
    ]
    
    print("\n" + "=" * 60)
    if all(results):
        print("✅ All validations passed!")
        print("Dashboard is ready for use.")
        print("\nTo run the dashboard:")
        print("  python ui/dashboard_api.py")
        print("  Then open http://localhost:8080/dashboard.html")
        return 0
    else:
        print("❌ Some validations failed. Please fix issues before proceeding.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
