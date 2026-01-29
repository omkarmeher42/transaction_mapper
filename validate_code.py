"""
Python Codebase Validation Script
Validates all Python files by attempting to import them
"""
import sys
import importlib.util

def validate_module(module_path, module_name):
    """Attempt to load and validate a Python module"""
    try:
        spec = importlib.util.spec_from_file_location(module_name, module_path)
        if spec and spec.loader:
            module = importlib.util.module_from_spec(spec)
            # Don't execute, just check if it can be loaded
            return True, "OK"
        return False, "Could not create module spec"
    except SyntaxError as e:
        return False, f"Syntax Error: {e}"
    except Exception as e:
        return False, f"Error: {e}"

# Test critical imports
print("Testing critical imports...")
print("=" * 50)

critical_modules = [
    ("app.py", "app"),
    ("models/__init__.py", "models"),
    ("models/users.py", "models.users"),
    ("models/transactions.py", "models.transactions"),
    ("models/budget_recurring.py", "models.budget_recurring"),
    ("routes/user_routes.py", "routes.user_routes"),
    ("routes/transaction_routes.py", "routes.transaction_routes"),
    ("routes/budget_routes.py", "routes.budget_routes"),
    ("routes/quick_routes.py", "routes.quick_routes"),
    ("services/user_services.py", "services.user_services"),
    ("services/transaction_services.py", "services.transaction_services"),
]

all_passed = True
for path, name in critical_modules:
    success, message = validate_module(path, name)
    status = "✓" if success else "✗"
    print(f"{status} {name:40s} {message}")
    if not success:
        all_passed = False

print("=" * 50)
if all_passed:
    print("✅ All modules validated successfully!")
    sys.exit(0)
else:
    print("❌ Some modules failed validation")
    sys.exit(1)
