# Connecting IBM Bob to DataContractIQ MCP Server

## ✅ Configuration Complete!

I've created the Bob MCP configuration file at `.bob/mcp.json` in your project root.

---

## 🔄 How to Activate the MCP Server

### Step 1: Reload Bob's MCP Configuration

Bob needs to reload the MCP configuration to see the new server. You can do this by:

**Option A: Through Bob's Settings Menu**
1. Click the ⚙️ icon in the Bob panel
2. Select the "MCP" tab
3. Click "Reload MCP Servers" (if available)

**Option B: Restart VS Code**
1. Close VS Code completely
2. Reopen VS Code
3. Bob will automatically load the MCP configuration

**Option C: Through Command Palette**
1. Press `Ctrl+Shift+P` (Windows/Linux) or `Cmd+Shift+P` (Mac)
2. Type "Developer: Reload Window"
3. Press Enter

### Step 2: Verify MCP Server is Loaded

After reloading, ask me:
```
"What MCP tools do you have access to?"
```

I should respond with the 7 DataContractIQ tools!

---

## 🛠️ The 7 MCP Tools

Once loaded, I (Bob) will have access to:

1. **introspect_schema** - Read database schema from SQL file or live database
2. **analyze_table** - Deep analysis of specific table structure
3. **generate_contract** - Create plain English data contracts
4. **save_contract** - Save approved contracts to disk
5. **list_contracts** - List all contracts with filtering
6. **detect_drift** - Compare current schema vs approved contract
7. **compare_schemas** - Compare two schema snapshots

---

## 🧪 Testing the Tools

### Test 1: Check Tool Access
```
"What MCP tools do you have?"
```

### Test 2: Introspect Database
```
"Introspect the Pagila database and tell me how many tables you found"
```

Expected: I should report finding 21 tables.

### Test 3: Analyze a Table
```
"Analyze the film table and show me its structure"
```

Expected: I should show columns, data types, constraints, and relationships.

### Test 4: Generate a Contract
```
"Generate a data contract for the film table"
```

Expected: I should create a plain English contract describing the table's purpose, columns, and business rules.

### Test 5: Save a Contract
```
"Save that contract as approved by [your name]"
```

Expected: Contract saved to `data/contracts/` directory.

### Test 6: Detect Drift
```
"Check if the film table has any schema drift"
```

Expected: I should compare the current schema against the saved contract.

---

## 📁 Configuration Files

### Project-Level Configuration (Created)
**Location:** `.bob/mcp.json`

```json
{
  "mcpServers": {
    "datacontractiq": {
      "command": "/mnt/c/Users/sam20/Documents/IBM Hackathon Project/backend/venv/bin/python",
      "args": [
        "/mnt/c/Users/sam20/Documents/IBM Hackathon Project/backend/mcp_server.py"
      ],
      "env": {
        "DATABASE_URL": "postgresql://postgres:password@localhost:5432/pagila",
        "PYTHONPATH": "/mnt/c/Users/sam20/Documents/IBM Hackathon Project/backend"
      }
    }
  }
}
```

This configuration:
- ✅ Uses your virtual environment's Python
- ✅ Points to the MCP server script
- ✅ Sets the database connection string
- ✅ Configures the Python path

### Global Configuration (Optional)
If you want this available in all projects, you can also add it to:
**Location:** `~/.bob/mcp_settings.json`

---

## 🐛 Troubleshooting

### Issue: "MCP tools not available"

**Solution 1: Check Configuration File**
- Verify `.bob/mcp.json` exists in project root
- Check that paths are correct (use absolute paths)
- Ensure JSON is valid (no syntax errors)

**Solution 2: Reload Bob**
- Restart VS Code completely
- Or use "Developer: Reload Window"

**Solution 3: Check Python Path**
- Verify the venv Python exists at the specified path
- Test: `ls /mnt/c/Users/sam20/Documents/IBM\ Hackathon\ Project/backend/venv/bin/python`

**Solution 4: Check MCP Server**
- Verify the server starts manually:
  ```bash
  cd backend
  source venv/bin/activate
  python mcp_server.py
  ```
- Should see: "Starting DataContractIQ MCP Server..."

### Issue: "Database connection failed"

**Check:**
- PostgreSQL is running
- Database credentials are correct in `.bob/mcp.json`
- Can connect manually: `psql postgresql://postgres:password@localhost:5432/pagila`

### Issue: "Import errors in MCP server"

**Check:**
- All dependencies installed: `pip install -r backend/requirements.txt`
- Virtual environment activated
- MCP package installed: `pip show mcp`

---

## 🎯 What This Enables

With MCP configured, I (Bob) can:

✅ **Read your entire database schema** without token limits
✅ **Generate plain English data contracts** automatically
✅ **Detect schema drift** and assess impact
✅ **Answer questions** about your database structure
✅ **Provide intelligent recommendations** for schema changes
✅ **Save and version control** data contracts

---

## 📊 Example Workflow

Here's a complete workflow once MCP is loaded:

```
You: "Bob, introspect the Pagila database"
Bob: [Calls introspect_schema tool]
     "I found 21 tables in the Pagila database including film, actor, customer, rental, payment..."

You: "Bob, analyze the film table in detail"
Bob: [Calls analyze_table tool]
     "The film table has 13 columns including film_id (PK), title, description, release_year..."

You: "Bob, generate a data contract for the film table"
Bob: [Calls generate_contract tool]
     "Here's the data contract for the film table:
     
     # Film Table Contract
     
     ## Purpose
     Stores information about films available for rental...
     
     ## Columns
     - film_id: Unique identifier for each film (Primary Key)
     - title: Film title (Required, max 255 characters)
     ..."

You: "Bob, save this contract as approved by Sam"
Bob: [Calls save_contract tool]
     "Contract saved successfully! Contract ID: film_20260502_032800_abc123"

You: "Bob, check if the film table has drifted"
Bob: [Calls detect_drift tool]
     "No drift detected. The film table matches the approved contract."
```

---

## 🚀 Next Steps

1. **Reload VS Code** to load the MCP configuration
2. **Ask me**: "What MCP tools do you have?"
3. **Start testing** with the examples above
4. **Generate contracts** for your key tables
5. **Detect drift** when schemas change

---

**Made with IBM Bob** 🤖