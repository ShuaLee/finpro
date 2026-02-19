# Admin Workflows - Portfolio & Account Management

This document describes the admin-only workflows for managing portfolios, accounts, and holdings in the Django Admin interface.

## User Creation

**Workflow:**
1. Navigate to Users → Users → Add User in Django Admin
2. Enter email and password
3. Save

**What Happens Automatically:**
- `ProfileService.bootstrap()` is called via `UserManager.create_user()`
- Profile is created and linked to User
- Free plan is assigned
- USD currency is set as default
- US country is set as default
- **Main Portfolio is created automatically**

**Result:**
User is fully bootstrapped and ready for account creation.

---

## Portfolio Management

**Key Points:**
- Main portfolio is created automatically when user is created
- Additional portfolios can be created manually if needed
- Each portfolio belongs to one Profile/User
- Portfolios contain multiple Accounts

**Model:**
```
User → Profile → Portfolio (Main) → Accounts → Holdings
```

**Admin Location:**
- Navigate to: Portfolios → Portfolios

---

## Account Creation Workflow

**Steps:**
1. Navigate to: Accounts → Accounts → Add Account
2. Fill in required fields:
   - **Portfolio**: Select user's portfolio (usually "Main Portfolio")
   - **Account Type**: Choose type (Brokerage, Crypto Wallet, etc.)
   - **Account Name**: Give it a descriptive name
   - **Broker**: (Optional) Broker name if applicable
   - **Classification Definition**: Select tax classification (TFSA, RRSP, 401k, etc.)
3. Click Save

**What Happens Automatically:**
- `AccountAdmin.save_model()` calls `AccountService.initialize_account()`
- **AccountClassification** is created/linked (profile + definition)
- **Schema** is created or reused for (portfolio, account_type) pair
- **SchemaColumns** are generated from SchemaTemplate
- Account is ready to receive holdings

**Important Notes:**
- One Schema is shared by all accounts of the same type within a portfolio
- Schema defines what columns (quantity, price, value, etc.) are tracked
- Classification is user-specific (each user has their own TFSA classification instance)

---

## Holding Management

**Steps:**
1. Navigate to: Accounts → Holdings → Add Holding
2. Select the **Account** (must have active schema)
3. Choose **Source**:
   - **Asset**: Market-backed holding (stocks, crypto, etc.)
   - **Custom**: User-defined or market-unavailable asset
4. If Asset source:
   - Select **Asset** from catalog
   - System validates asset type compatibility
5. Enter **Quantity**
6. Enter **Average Purchase Price** (optional)
7. Click Save

**What Happens Automatically:**
- `HoldingAdmin.save_model()` triggers `SCVRefreshService.holding_changed()`
- **SchemaColumnValues** are created for all schema columns
- Formula-based columns are computed (e.g., current_value = quantity * price)
- Original ticker is derived from asset
- Holding data is now available for analytics

**Validation:**
- Asset type must be allowed by account type
- Account must have an active schema
- Quantity cannot be negative
- Average purchase price cannot be set if quantity is zero

---

## Schema System

**Overview:**
The Schema system provides flexible, dynamic columns for holdings data.

**Architecture:**
```
Portfolio + AccountType → Schema (one per pair)
    ↓
SchemaColumns (quantity, price, current_value, etc.)
    ↓
SchemaColumnValues (actual data per holding)
```

**Column Types:**
1. **Holding fields**: Direct from Holding model
   - Example: `quantity`, `average_purchase_price`

2. **Asset fields**: Pulled from Asset model
   - Example: `ticker`, `name`, `price`

3. **Formula computed**: Calculated via FormulaDefinitions
   - Example: `current_value = quantity * last_price`

4. **Custom**: User-entered values
   - Example: custom notes, tags, identifiers

**Schema Reuse:**
- Accounts of the same type in the same portfolio share one schema
- Adding a column to schema applies to ALL accounts of that type
- Changing schema affects all associated holdings

---

## Analytics

**How It Works:**
1. Analytics aggregate SchemaColumnValues across holdings
2. Group by dimensions (country, sector, asset class, etc.)
3. Sum by value column (typically `current_value_profile_fx`)
4. Compute percentages and breakdowns

**Example:**
- **Analytic**: "Country Exposure"
- **Value Column**: `current_value_profile_fx`
- **Dimension**: `country`
- **Result**:
  - USA: $40,000 (30%)
  - Canada: $15,000 (12%)
  - Unknown: $80,000 (58%)

---

## Common Admin Tasks

### Creating a Test Account
```python
# In Django shell or script
from users.models import User
from accounts.models import Account, AccountType, ClassificationDefinition
from accounts.services.account_service import AccountService

# Get user
user = User.objects.get(email="user@example.com")
portfolio = user.profile.portfolio

# Get or create account type
account_type = AccountType.objects.get(slug="brokerage")

# Get classification definition
definition = ClassificationDefinition.objects.get(name="TFSA")

# Create account
account = Account.objects.create(
    portfolio=portfolio,
    name="Test Brokerage",
    account_type=account_type,
)

# Initialize (REQUIRED!)
AccountService.initialize_account(
    account=account,
    definition=definition
)
```

### Verifying Schema Creation
```python
from schemas.models import Schema

# Check if schema exists
schema = Schema.objects.filter(
    portfolio=portfolio,
    account_type=account_type
).first()

print(f"Schema: {schema}")
print(f"Columns: {schema.columns.count()}")
```

### Checking Holdings Data
```python
from accounts.models import Holding
from schemas.models import SchemaColumnValue

holding = Holding.objects.last()

# Get all schema values for this holding
scvs = SchemaColumnValue.objects.filter(holding=holding)

for scv in scvs:
    print(f"{scv.column.identifier}: {scv.value}")
```

---

## Troubleshooting

### "Account schema must exist before holdings can be created"
**Cause**: Account wasn't initialized properly
**Solution**: Call `AccountService.initialize_account(account, definition)`

### Schema not appearing for account type
**Cause**: No SchemaTemplate exists for that account type
**Solution**: Create SchemaTemplate via management command or admin

### Holdings not showing analytics data
**Cause**: SchemaColumnValues not computed
**Solution**: Trigger `SCVRefreshService.holding_changed(holding)`

---

## Next Steps

After accounts are set up in admin, you can:
1. Create SchemaTemplates for each AccountType
2. Seed system data (account types, classifications, formulas)
3. Implement formula evaluation
4. Build REST API for frontend integration
5. Add analytics computation
