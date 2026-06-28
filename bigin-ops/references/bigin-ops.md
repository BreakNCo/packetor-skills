# Bigin CRM Operations — Reference

Field names, module details, pipeline stages, and tool call patterns for Zoho Bigin.

## Modules & API Names

| Module | `module_api_name` | Purpose |
|--------|------------------|---------|
| Accounts | `Accounts` | Companies / organisations |
| Contacts | `Contacts` | Individual people |
| Pipelines | `Pipelines` | Deals / opportunities |
| Tasks | `Tasks` | Follow-up tasks |
| Meetings | `Meetings` | Calls and meetings |

---

## Accounts Fields

| Field | API Name | Type |
|-------|----------|------|
| Company Name | `Account_Name` | String |
| Website | `Website` | URL |
| Industry | `Industry` | Picklist |
| Employees | `Employees` | Integer |
| Phone | `Phone` | String |
| Description | `Description` | Text |
| City | `Billing_City` | String |
| State | `Billing_State` | String |
| Country | `Billing_Country` | String |
| LinkedIn | `Company_Linkedin_Url` | URL |
| Twitter | `Twitter` | String |

---

## Contacts Fields

| Field | API Name | Type |
|-------|----------|------|
| First Name | `First_Name` | String |
| Last Name | `Last_Name` | String (required) |
| Email | `Email` | Email |
| Phone | `Phone` | String |
| Mobile | `Mobile` | String |
| Title | `Title` | String |
| Department | `Department` | String |
| Account | `Account_Name` | Lookup → Accounts |
| LinkedIn | `LinkedIn__c` | URL |

---

## Pipelines (Deals) Fields

| Field | API Name | Type |
|-------|----------|------|
| Deal Name | `Deal_Name` | String (required) |
| Stage | `Stage` | Picklist |
| Amount | `Amount` | Currency |
| Closing Date | `Closing_Date` | Date |
| Account | `Account_Name` | Lookup → Accounts |
| Contact | `Contact_Name` | Lookup → Contacts |
| Owner | `Owner` | Lookup → Users |
| Description | `Description` | Text |
| Probability | `Probability` | Percentage |

### Default Pipeline Stages (in order)

1. `Qualification`
2. `Needs Analysis`
3. `Value Proposition`
4. `Identify Decision Makers`
5. `Proposal/Price Quote`
6. `Negotiation/Review`
7. `Closed Won`
8. `Closed Lost`

> Stage names are case-sensitive. Use exact values above.

---

## Tasks Fields

| Field | API Name | Type |
|-------|----------|------|
| Subject | `Subject` | String (required) |
| Status | `Status` | Picklist |
| Due Date | `Due_Date` | Date (YYYY-MM-DD) |
| Priority | `Priority` | Picklist |
| Owner | `Owner` | Lookup → Users |
| Related To | `What_Id` | `{"id": "<record_id>"}` |
| Description | `Description` | Text |

**Status values:** `Not Started`, `Deferred`, `In Progress`, `Completed`, `Waiting for Input`
**Priority values:** `High`, `Medium`, `Low`

---

## Meetings Fields

| Field | API Name | Type |
|-------|----------|------|
| Title | `Event_Title` | String (required) |
| Start | `Start_DateTime` | ISO 8601 datetime |
| End | `End_DateTime` | ISO 8601 datetime |
| Location | `Venue` | String |
| Description | `Description` | Text |
| Related To | `What_Id` | `{"id": "<record_id>"}` |
| Participants | `Participants` | Array of `{"id": ...}` |

---

## Notes Fields

| Field | API Name | Type |
|-------|----------|------|
| Title | `Note_Title` | String |
| Content | `Note_Content` | Text |
| Parent module | `Parent_Id` | Lookup |

---

## Common Tool Call Patterns

### Search a contact
```python
mcporter_call("ZohoMCP", "Bigin_searchRecords",
    module_api_name="Contacts", word="John Smith")
```

### Get a specific record
```python
mcporter_call("ZohoMCP", "Bigin_getSpecificRecord",
    module_api_name="Contacts", record_id="<id>")
```

### Create a contact
```python
mcporter_call("ZohoMCP", "Bigin_addRecords",
    module_api_name="Contacts",
    data=[{"Last_Name": "Smith", "Email": "john@example.com", "Phone": "+91..."}])
```

### Update a record
```python
mcporter_call("ZohoMCP", "Bigin_updateSpecificRecord",
    module_api_name="Contacts", record_id="<id>",
    data={"Title": "VP of Engineering"})
```

### Move deal stage
```python
mcporter_call("ZohoMCP", "Bigin_updateSpecificRecord",
    module_api_name="Pipelines", record_id="<id>",
    data={"Stage": "Proposal/Price Quote"})
```

### Add a note
```python
mcporter_call("ZohoMCP", "Bigin_addNotesToSpecificRecord",
    module_api_name="Contacts", record_id="<id>",
    data=[{"Note_Title": "Call summary", "Note_Content": "Discussed Q2 renewal..."}])
```

### Add a note to a Pipeline record reliably
```python
mcporter_call("ZohoMCP", "Bigin_addNotes",
    data=[{
        "Note_Title": "Call summary",
        "Note_Content": "Discussed next steps...",
        "Parent_Id": "<pipeline_id>",
        "se_module": "Pipelines"
    }])
```

Note: in this environment, `Bigin_addNotesToSpecificRecord` expects a `body.data` array rather than a flat note body. Pipeline notes are confirmed working when sent either through `Bigin_addNotes` with `Parent_Id + se_module`, or through `Bigin_addNotesToSpecificRecord` with `data=[...]`.

Important: do not trust a stale pipeline id copied from an older message or another workspace. Before writing a Pipeline note or Pipeline-linked task, re-search the deal by company/deal name and use the current returned `id`, unless the id was just fetched in the same execution flow.

### Exact pipeline id extraction command

In this environment, if the pretty-printed search output obscures the top-level deal id, use this exact command to extract the current Pipeline/Deal `id` directly:

```bash
mcporter --config /data/workspace-discord-ops/config/mcporter.json call zoho-bigin.Bigin_searchRecords \
  'path_variables={"module_api_name":"Pipelines"}' \
  'query_params={"word":"<company or deal name>"}' \
| python3 -c 'import sys,json; obj=json.load(sys.stdin); print(obj["data"]["data"][0]["id"])'
```

Example:

```bash
mcporter --config /data/workspace-discord-ops/config/mcporter.json call zoho-bigin.Bigin_searchRecords \
  'path_variables={"module_api_name":"Pipelines"}' \
  'query_params={"word":"Orivios Technologies Private Limited"}' \
| python3 -c 'import sys,json; obj=json.load(sys.stdin); print(obj["data"]["data"][0]["id"])'
```

This returned:

```text
1188539000000665129
```

### Create a Pipeline-linked task (exact working pattern)
```python
mcporter_call("ZohoMCP", "Bigin_addRecords",
    module_api_name="Tasks",
    data=[{
        "Subject": "Follow up",
        "What_Id": {"id": "<pipeline_id>"},
        "$se_module": "Deals",
        "Priority": "High",
        "Status": "Not Started",
        "Due_Date": "2026-04-05",
        "Description": "Concrete next step from the call"
    }])
```

Important:
- Before creating a Pipeline-linked task, re-search the current deal/pipeline record and use the returned `id`.
- Prefer the exact pipeline-id extraction command above when the visible pretty output does not show the top-level `id` clearly.
- In this setup, the reliable linkage pattern is:
  - `What_Id: { id }`
  - `$se_module: "Deals"`
- Do not rely on stale ids copied from old notes/messages.
- Always set a `Due_Date`.

### Due date rule
Use the earliest sensible due date based on what the call clearly implies:

- **Explicit date/day mentioned** → convert that into the actual due date and use it.
- **Email / send details / send deck / send proposal** with no explicit date → set due date to **next day**.
- **Tomorrow / next day callback** → set due date to **next day**.
- **This week meeting / schedule this week** → set due date to the **next business day**, or the explicit day if one is named.
- **Next week follow-up / next Tuesday / Wednesday to Friday plan** → set due date to the earliest day that fits the instruction.
- **No timing signal but still a concrete task** → default to **next business day**.

If the exact date cannot be resolved perfectly, prefer a practical near-term due date rather than leaving it blank.

### Fetch related tasks
```python
mcporter_call("ZohoMCP", "Bigin_getRelatedListRecords",
    module_api_name="Contacts", record_id="<id>",
    related_list_api_name="Tasks")
```

### List deals by stage
```python
mcporter_call("ZohoMCP", "Bigin_getRecords",
    module_api_name="Pipelines",
    criteria="(Stage:equals:Qualification)",
    per_page=20)
```
