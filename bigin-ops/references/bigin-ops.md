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
    Note_Title="Call summary", Note_Content="Discussed Q2 renewal...")
```

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
