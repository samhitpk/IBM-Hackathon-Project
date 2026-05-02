# Connecting IBM Bob to DataContractIQ MCP Server

## 🎉 Your MCP Server is Running!

You successfully started the DataContractIQ MCP server. Now let's connect Bob to it.

---

## 📋 Configuration Steps

### Step 1: Locate Bob's MCP Configuration File

Bob's MCP configuration is typically stored in one of these locations:

**For Claude Desktop (if using Claude with MCP):**
- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
- **Linux**: `~/.config/Claude/claude_desktop_config.json`

**For Cline/Roo-Cline (VS Code Extension):**
- Look for MCP settings in VS Code settings or `.vscode/settings.json`

### Step 2: Add DataContractIQ MCP Server Configuration

Add this configuration to your MCP config file:

```json
{
  "mcpServers": {
    "datacontractiq": {
      "command": "python",
      "args": [
        "/mnt/c/Users/sam20/Documents/IBM Hackathon Project/backend/mcp_server.py"
      ],
      "env": {
        "PYTHONPATH": "/mnt/c/Users/sam20/Documents/IBM Hackathon Project/backend",
        "DATABASE_URL": "postgresql://postgres:password@localhost:5432/pagila"
      }
    }
  }
}
```

**Important Notes:**
- Use the **full absolute path** to `mcp_server.py`
- Make sure the path uses forward slashes `/` even on Windows
- The `env` section passes environment variables to the server
- Adjust the `DATABASE_URL` if your PostgreSQL credentials are different

### Step 3: Alternative Configuration (Using Virtual Environment)

If you want to use the virtual environment's Python explicitly:

```json
{
  "mcpServers": {
    "datacontractiq": {
      "command": "/mnt/c/Users/sam20/Documents/IBM Hackathon Project/backend/venv/bin/python",
      "args": [
        "/mnt/c/Users/sam20/Documents/IBM Hackathon Project/backend/mcp_server.py"
      ],
      "env": {
        "DATABASE_URL": "postgresql://postgres:password@localhost:5432/pagila"
      }
    }
  }
}
```

### Step 4: Restart Bob/Claude

After adding the configuration:
1. **Save the config file**
2. **Restart Claude Desktop** or **Reload VS Code window**
3. Bob should now have access to the 7 DataContractIQ tools

---

## 🛠️ The 7 Tools Bob Can Now Use

Once connected, Bob can use these tools through natural conversation:

### 1. **introspect_schema**
```
"Bob, introspect the Pagila database"
"Bob, read the schema from the SQL file"
```

### 2. **analyze_table**
```
"Bob, analyze the film table"
"Bob, give me details about the customer table"
```

### 3. **generate_contract**
```
"Bob, generate a data contract for the film table"
"Bob, create a contract for the rental table in markdown format"
```

### 4. **save_contract**
```
"Bob, save this contract and mark it as approved by me"
```

### 5. **list_contracts**
```
"Bob, show me all approved contracts"
"Bob, list contracts for the film table"
```

### 6. **detect_drift**
```
"Bob, check if the film table has drifted from its contract"
"Bob, detect any schema changes in the customer table"
```

### 7. **compare_schemas**
```
"Bob, compare the current schema with snapshot ABC123"
```

---

## 🧪 Testing the Connection

### Test 1: Check if Bob Can See the Tools

Ask Bob:
```
"What MCP tools do you have access to?"
```

Bob should list the 7 DataContractIQ tools.

### Test 2: Introspect the Database

Ask Bob:
```
"Introspect the Pagila database and tell me how many tables you found"
```

Expected response: Bob should report finding 21 tables.

### Test 3: Generate a Contract

Ask Bob:
```
"Generate a data contract for the film table in the Pagila database"
```

Bob should:
1. Call `introspect_schema` to get the schema
2. Call `generate_contract` for the film table
3. Present a plain English contract with columns, relationships, and business rules

### Test 4: Detect Drift

First, generate and save a contract:
```
"Generate and save a contract for the actor table"
```

Then test drift detection:
```
"Check if the actor table has any schema drift"
```

---

## 🐛 Troubleshooting

### Issue: Bob Can't Find the MCP Server

**Solution 1: Check the Path**
- Make sure the path to `mcp_server.py` is absolute and correct
- Use forward slashes `/` even on Windows
- Test the path in terminal: `python /full/path/to/mcp_server.py`

**Solution 2: Check Python Path**
- Verify Python is in your PATH: `which python` or `where python`
- Or use the full path to Python in the config

**Solution 3: Check Environment Variables**
- Make sure `DATABASE_URL` is correct
- Test database connection: `psql postgresql://postgres:password@localhost:5432/pagila`

### Issue: MCP Server Starts But Tools Don't Work

**Check the Logs:**
The MCP server logs to stdout. Look for error messages when Bob calls a tool.

**Common Issues:**
1. **Database connection failed** - Check PostgreSQL is running
2. **Import errors** - Make sure all dependencies are installed in venv
3. **Permission errors** - Check file permissions on data/contracts and data/snapshots

### Issue: Bob Says "Tool Not Found"

This means Bob can't see the MCP server. Check:
1. MCP config file is in the correct location
2. Config JSON is valid (no syntax errors)
3. You restarted Claude/VS Code after adding the config

---

## 📊 Example Workflow

Here's a complete workflow to test all features:

```
You: "Bob, introspect the Pagila database"
Bob: [Calls introspect_schema, reports 21 tables found]

You: "Bob, analyze the film table in detail"
Bob: [Calls analyze_table, shows columns, relationships, constraints]

You: "Bob, generate a data contract for the film table"
Bob: [Calls generate_contract, presents plain English contract]

You: "Bob, save this contract as approved by Sam"
Bob: [Calls save_contract, confirms saved]

You: "Bob, list all approved contracts"
Bob: [Calls list_contracts, shows the film contract]

You: "Bob, check if the film table has drifted"
Bob: [Calls detect_drift, reports no drift detected]
```

---

## 🎯 Next Steps

1. **Test the connection** using the examples above
2. **Generate contracts** for key tables (film, customer, rental, payment)
3. **Simulate drift** by modifying a table and detecting changes
4. **Explore Bob's intelligence** - ask follow-up questions about the contracts

---

## 📝 Notes

- The MCP server must be running for Bob to use the tools
- Bob can call multiple tools in sequence to accomplish complex tasks
- Bob understands the full context of your database through the tools
- All contracts are saved in `data/contracts/` as JSON files
- All schema snapshots are saved in `data/snapshots/` as JSON files

---

## 🆘 Need Help?

If you encounter issues:
1. Check the MCP server logs (stdout when running `python mcp_server.py`)
2. Verify database connection works
3. Test tools individually using the test examples above
4. Check file permissions on data directories

---

**Made with Bob** 🤖