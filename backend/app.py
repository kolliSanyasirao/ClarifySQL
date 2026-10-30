
import json
import os
import re
import sqlite3
import subprocess
import sys
import uuid

from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from litellm import completion
from pydantic import BaseModel, Field


app = FastAPI(title="ClarifySQL API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
          "https://clarify-sql-nine.vercel.app"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
VSCODE = ROOT / ".vscode"

load_dotenv(VSCODE / ".env")

SPIDER_ROOT = VSCODE / "combined_data_all" / "spider"
TABLES_FILE = SPIDER_ROOT / "tables.json"
DATABASE_ROOT = SPIDER_ROOT / "database"


# ---------------------------------------------------------
# Category to Python script mapping
# ---------------------------------------------------------

CATEGORY_SCRIPTS = {
    "Ambiguous SELECT Column":
        SRC / "ambiguous" / "ambiguous_SELECT_column" /
        "ambiguous_select_column_main.py",

    "Ambiguous VALUES Across Columns":
        SRC / "ambiguous" / "ambiguous_VALUES_across_columns" /
        "ambiguous_values_across_columns_main.py",

    "Ambiguous VALUES Within Column":
        SRC / "ambiguous" / "ambiguous_VALUES_within_column" /
        "ambiguous_values_within_column_main.py",

    "Vague Filter Term":
        SRC / "ambiguous" / "vague_filter_term" /
        "vague_filter_term_main.py",

    "Nonexistent SELECT Column":
        SRC / "unanswerable" / "nonexistent_select_column" /
        "nonexistent_select_column_main.py",

    "Nonexistent Value":
        SRC / "unanswerable" / "nonexistent_value" /
        "nonexistent_value_main.py",

    "Nonexistent WHERE Column":
        SRC / "unanswerable" / "nonexistent_where_column" /
        "nonexistent_where_column_main.py",

    "Unsupported Joins":
        SRC / "unanswerable" / "unsupported_joins" /
        "unsupported_join_generation_main.py",
}


# ---------------------------------------------------------
# Running jobs
# ---------------------------------------------------------

JOBS = {}
LATEST_OUTPUTS = {}


class RunRequest(BaseModel):
    category: str = "Ambiguous SELECT Column"
    split: str = "dev"
    n2sample: int = Field(default=1, ge=1, le=100)


class ChatRequest(BaseModel):
    message: str
    history: list = Field(default_factory=list)
    database: str | None = None


# ---------------------------------------------------------
# JSONL reader
# ---------------------------------------------------------

def read_jsonl(path: Path):
    if not path.exists():
        return []

    results = []

    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()

            if not line:
                continue

            try:
                results.append(json.loads(line))
            except json.JSONDecodeError:
                continue

    return results


# ---------------------------------------------------------
# Load SPIDER databases
# ---------------------------------------------------------

def load_spider_tables():
    if not TABLES_FILE.exists():
        return []

    try:
        with TABLES_FILE.open("r", encoding="utf-8") as f:
            return json.load(f)

    except Exception as exc:
        print(f"Could not load tables.json: {exc}")
        return []


# ---------------------------------------------------------
# Normalize tokens
# ---------------------------------------------------------

def normalize_tokens(text: str):

    stop_words = {
        "a", "an", "the", "me", "my",
        "you", "your", "is", "are",
        "was", "were", "what", "which",
        "who", "where", "when", "how",
        "can", "could", "would", "should",
        "do", "does", "did", "show",
        "give", "list", "find", "tell",
        "get", "all", "of", "for",
        "from", "to", "in", "on",
        "with", "and", "or", "about"
    }

    tokens = re.findall(
        r"[a-zA-Z_][a-zA-Z0-9_]*",
        text.lower()
    )

    return {
        token
        for token in tokens
        if token not in stop_words
    }


# ---------------------------------------------------------
# Extract database schema
# ---------------------------------------------------------

def get_schema_for_db(db):
    """
    Return both original SQLite identifiers and readable
    SPIDER display names.

    SQL generation must always use original identifiers.
    """

    display_tables = db.get("table_names", []) or []

    original_tables = (
        db.get("table_names_original")
        or display_tables
    )

    display_columns = db.get("column_names", []) or []

    original_columns = (
        db.get("column_names_original")
        or display_columns
    )

    types = db.get("column_types", []) or []

    schema_columns = []

    for index, column in enumerate(original_columns):

        if (
            not isinstance(column, (list, tuple))
            or len(column) != 2
        ):
            continue

        table_id, original_name = column

        if table_id < 0:
            continue

        display_name = original_name

        if index < len(display_columns):

            display_entry = display_columns[index]

            if (
                isinstance(display_entry, (list, tuple))
                and len(display_entry) == 2
            ):
                display_name = display_entry[1]

        column_type = (
            types[index]
            if index < len(types)
            else "unknown"
        )

        schema_columns.append({
            "index": index,
            "table_id": table_id,
            "column": original_name,
            "display_column": display_name,
            "type": column_type,
        })

    # Resolve primary and foreign keys using
    # the original SQLite identifiers.

    column_by_index = {
        column["index"]: column
        for column in schema_columns
    }

    primary_keys = []

    for column_index in db.get("primary_keys", []) or []:

        column_info = column_by_index.get(column_index)

        if (
            column_info
            and column_info["table_id"] < len(original_tables)
        ):
            primary_keys.append({
                "table": original_tables[
                    column_info["table_id"]
                ],
                "column": column_info["column"],
            })

    foreign_keys = []

    for pair in db.get("foreign_keys", []) or []:

        if (
            not isinstance(pair, (list, tuple))
            or len(pair) != 2
        ):
            continue

        source = column_by_index.get(pair[0])
        target = column_by_index.get(pair[1])

        if not source or not target:
            continue

        if (
            source["table_id"] >= len(original_tables)
            or target["table_id"] >= len(original_tables)
        ):
            continue

        foreign_keys.append({
            "from_table": original_tables[
                source["table_id"]
            ],
            "from_column": source["column"],
            "to_table": original_tables[
                target["table_id"]
            ],
            "to_column": target["column"],
        })

    return {
        "db_id": db.get("db_id"),
        "tables": original_tables,
        "display_tables": display_tables,
        "columns": schema_columns,
        "primary_keys": primary_keys,
        "foreign_keys": foreign_keys,
    }


# ---------------------------------------------------------
# Build schema text for Gemini
# ---------------------------------------------------------

def build_schema_text(schema):
    """
    Original SQLite identifiers are provided separately
    from human-readable display labels.
    """

    tables = schema["tables"]

    display_tables = schema.get(
        "display_tables",
        tables
    )

    columns = schema["columns"]

    def quote_identifier(name):
        return (
            '"'
            + str(name).replace('"', '""')
            + '"'
        )

    grouped = {}

    for column in columns:

        table_id = column["table_id"]

        if table_id < 0 or table_id >= len(tables):
            continue

        table_name = tables[table_id]

        display_column = column.get(
            "display_column",
            column["column"]
        )

        grouped.setdefault(
            table_name,
            []
        ).append(
            f'{quote_identifier(column["column"])} '
            f'(display label: {display_column}; '
            f'type: {column["type"]})'
        )

    lines = []

    for table_index, table_name in enumerate(tables):

        display_name = (
            display_tables[table_index]
            if table_index < len(display_tables)
            else table_name
        )

        lines.append(
            f'TABLE SQL_NAME {quote_identifier(table_name)} '
            f'(display label: {display_name})'
        )

        for column_description in grouped.get(
            table_name,
            []
        ):
            lines.append(
                f"  COLUMN {column_description}"
            )

    # Primary keys

    primary_keys = schema.get("primary_keys", [])

    if primary_keys:

        lines.append("PRIMARY KEYS:")

        for key in primary_keys:

            lines.append(
                f'  {quote_identifier(key["table"])}.'
                f'{quote_identifier(key["column"])}'
            )

    # Foreign keys

    foreign_keys = schema.get("foreign_keys", [])

    if foreign_keys:

        lines.append(
            "FOREIGN KEY RELATIONSHIPS (use these for joins):"
        )

        for key in foreign_keys:

            lines.append(
                f'  {quote_identifier(key["from_table"])}.'
                f'{quote_identifier(key["from_column"])} = '
                f'{quote_identifier(key["to_table"])}.'
                f'{quote_identifier(key["to_column"])}'
            )

    return "\n".join(lines)


# ---------------------------------------------------------
# Find database using ID
# ---------------------------------------------------------

def get_database_by_id(db_id: str):

    databases = load_spider_tables()

    for db in databases:

        if db.get("db_id") == db_id:
            return db

    return None


# ---------------------------------------------------------
# Normalize database names
# ---------------------------------------------------------

def normalize_db_phrase(text: str):

    return re.sub(
        r"[^a-z0-9]+",
        " ",
        text.lower()
    ).strip()


# ---------------------------------------------------------
# Automatic database search
# ---------------------------------------------------------

def find_candidate_databases(
    question: str,
    limit: int = 5
):

    databases = load_spider_tables()

    question_tokens = normalize_tokens(question)

    normalized_question = (
        f" {normalize_db_phrase(question)} "
    )

    candidates = []

    for db in databases:

        schema = get_schema_for_db(db)

        db_id = db.get("db_id", "")

        searchable_names = [db_id]

        searchable_names.extend(schema["tables"])

        searchable_names.extend(
            schema.get("display_tables", [])
        )

        searchable_names.extend(
            column["column"]
            for column in schema["columns"]
        )

        searchable_names.extend(
            column.get("display_column", "")
            for column in schema["columns"]
        )

        schema_tokens = normalize_tokens(
            " ".join(searchable_names)
        )

        overlap = question_tokens.intersection(
            schema_tokens
        )

        normalized_db_id = normalize_db_phrase(
            db_id
        )

        explicitly_requested = (
            bool(normalized_db_id)
            and f" {normalized_db_id} " in normalized_question
        )

        score = len(overlap)

        if explicitly_requested:
            score += 10000

        candidates.append({
            "db_id": db_id,
            "score": score,
            "overlap": sorted(overlap),
            "explicitly_requested": explicitly_requested,
            "schema": schema,
        })

    candidates.sort(
        key=lambda item: item["score"],
        reverse=True
    )

    return candidates[:limit]


# ---------------------------------------------------------
# Extract JSON returned by Gemini
# ---------------------------------------------------------

def extract_json_response(text: str):

    text = text.strip()

    if text.startswith("```"):

        text = re.sub(
            r"^```(?:json)?\s*",
            "",
            text,
            flags=re.IGNORECASE
        )

        text = re.sub(
            r"\s*```$",
            "",
            text
        )

    start = text.find("{")
    end = text.rfind("}")

    if start == -1 or end == -1:

        raise ValueError(
            "Gemini did not return a valid JSON object."
        )

    json_text = text[start:end + 1]

    return json.loads(json_text)


# ---------------------------------------------------------
# Execute SQL safely against selected SQLite database
# ---------------------------------------------------------

def execute_select(
    db_id: str,
    sql: str
):

    if not sql:

        return None, "No SQL query was generated."

    normalized_sql = sql.strip().rstrip(";").lstrip()

    if not re.match(
        r"^SELECT\b",
        normalized_sql,
        re.IGNORECASE
    ):
        return None, "Only SELECT queries are allowed."

    db_path = (
        DATABASE_ROOT
        / db_id
        / f"{db_id}.sqlite"
    )

    if not db_path.exists():

        return (
            None,
            f"Database not found: {db_path}"
        )

    try:

        with sqlite3.connect(
            str(db_path)
        ) as connection:

            # Enforce read-only SQL execution.
            connection.execute("PRAGMA query_only = ON")

            cursor = connection.cursor()

            cursor.execute(sql)

            rows = cursor.fetchall()

            column_names = [
                description[0]
                for description in cursor.description
            ]

        results = [
            dict(zip(column_names, row))
            for row in rows
        ]

        return results, None

    except Exception as exc:

        return None, str(exc)


# ---------------------------------------------------------
# Main ClarifySQL Chat API
# ---------------------------------------------------------

@app.post("/api/chat")
def chat(request: ChatRequest):

    user_message = request.message.strip()

    if not user_message:

        raise HTTPException(
            status_code=400,
            detail="Message cannot be empty."
        )

    # -----------------------------------------------------
    # 1. Greeting detection
    # -----------------------------------------------------

    normalized_message = re.sub(
        r"[^\w\s]",
        "",
        user_message.lower()
    ).strip()

    normalized_message = re.sub(
        r"\s+",
        " ",
        normalized_message
    )

    greetings = {
        "hi",
        "hello",
        "hey",
        "hello there",
        "hey there",
        "good morning",
        "good afternoon",
        "good evening",
        "how are you",
        "thanks",
        "thank you",
        "thank you so much"
    }

    if normalized_message in greetings:

        return {
            "stage": "WELCOME",
            "state": "greeting",
            "database": request.database,
            "message": (
                "Hello! Welcome to ClarifySQL. "
                "Ask me a question about your database. "
                "I will inspect the available schema, "
                "identify ambiguity, ask for clarification "
                "when needed, and generate validated SQL."
            ),
            "reason": None,
            "clarification": None,
            "sql": None,
            "rows": None,
            "candidate_databases": []
        }

    # -----------------------------------------------------
    # 2. Explicit dataset selection and switching
    # -----------------------------------------------------

    normalized_phrase = normalize_db_phrase(
        user_message
    )

    message_words = set(
        normalized_phrase.split()
    )

    selection_words = {
        "select",
        "choose",
        "use",
        "switch",
        "change",
        "load",
        "open"
    }

    dataset_words = {
        "dataset",
        "database",
        "db"
    }

    is_dataset_selection = bool(
        message_words.intersection(selection_words)
        and message_words.intersection(dataset_words)
    )

    if is_dataset_selection:

        for db in load_spider_tables():

            db_id = db.get("db_id", "")

            normalized_db_id = normalize_db_phrase(
                db_id
            )

            if normalized_db_id and (
                f" {normalized_db_id} "
                in f" {normalized_phrase} "
            ):

                return {
                    "stage": "SCHEMA",
                    "state": "database_selected",
                    "database": db_id,
                    "message": (
                        f"The {db_id} dataset has been "
                        "selected successfully. "
                        "You can now ask a question "
                        "about this database."
                    ),
                    "reason": "Explicit dataset selection.",
                    "clarification": None,
                    "sql": None,
                    "rows": None,
                    "candidate_databases": [db_id]
                }

        return {
            "stage": "SCHEMA",
            "state": "database_not_found",
            "database": request.database,
            "message": (
                "I couldn't find that dataset in the "
                "loaded SPIDER collection. Please check "
                "the dataset ID or choose one from the "
                "available list."
            ),
            "reason": (
                f"No database ID matched: {normalized_phrase}"
            ),
            "clarification": None,
            "sql": None,
            "rows": None,
            "candidate_databases": []
        }

    # -----------------------------------------------------
    # 3. Database selection
    # -----------------------------------------------------
    # Preserve the selected database during follow-up turns.

    if request.database:

        previous_db = get_database_by_id(
            request.database
        )

        if previous_db:

            selected = {
                "db_id": previous_db["db_id"],
                "score": 999,
                "overlap": [],
                "schema": get_schema_for_db(previous_db)
            }

            candidates = [selected]

        else:

            candidates = find_candidate_databases(
                user_message,
                limit=5
            )

    else:

        candidates = find_candidate_databases(
            user_message,
            limit=5
        )

    if not candidates:

        return {
            "stage": "SCG",
            "state": "unanswerable",
            "database": None,
            "message": (
                "I could not find a relevant database "
                "schema for your question."
            ),
            "clarification": None,
            "sql": None,
            "rows": None,
            "candidate_databases": []
        }

    selected = candidates[0]

    # -----------------------------------------------------
    # 4. Build schema information
    # -----------------------------------------------------

    schema_text = build_schema_text(
        selected["schema"]
    )

    candidate_text = "\n".join(
        [
            f"{item['db_id']} | matched: "
            f"{', '.join(item['overlap']) or 'none'}"
            for item in candidates
        ]
    )

    # -----------------------------------------------------
    # 5. Conversation history
    # -----------------------------------------------------

    history_items = request.history[-10:]

    # Prevent duplicate current user message.

    if (
        history_items
        and isinstance(history_items[-1], dict)
    ):

        last_history_message = str(
            history_items[-1].get("content", "")
        ).strip()

        if last_history_message == user_message:

            history_items = history_items[:-1]

    history_text = "\n".join(
        [
            f"{item.get('role', 'user')}: "
            f"{item.get('content', '')}"
            for item in history_items
            if isinstance(item, dict)
        ]
    )

    # -----------------------------------------------------
    # 6. ClarifySQL reasoning prompt
    # -----------------------------------------------------

    prompt = f"""
You are ClarifySQL, an adaptive schema-grounded
conversational Text-to-SQL system.

Your task is to understand the user's request and
never invent database tables or columns.

Follow this reasoning process:

1. JID — INTENT DETECTION

First determine whether the user's request is:

ANSWERABLE:
The requested information is specific enough to
generate SQL directly.

AMBIGUOUS:
The request could refer to multiple columns, tables,
attributes, filters, aggregations, or meanings.

UNANSWERABLE:
The requested information does not exist in the
provided schema.

IMPORTANT:

Do NOT mark a broad request as answerable simply
because some table exists.

For example:

"Show me the student information"

is AMBIGUOUS when the relevant schema contains
multiple reasonable pieces of student information.

Ask which information the user wants.

If the user sends a short follow-up such as:
"I want their names"
"Only the IDs"
"I mean the department"
"Yes, that one"

interpret it as a clarification of the previous
conversation, not as a new standalone query.

2. SCG — SCHEMA GAP ANALYSIS

Compare the user's wording against the exact schema.

Identify:
- possible matching tables
- possible matching columns
- missing columns
- multiple possible interpretations

Never assume that a broad natural-language term
refers to a particular column when more than one
reasonable schema interpretation exists.

3. CLARIFICATION POLICY

If the request is ambiguous, ask ONE precise
clarification question.

4. BRT — BELIEF REVISION / DIALOGUE CONTEXT

Use previous conversation turns to understand the
user's clarification.

Preserve the selected database and interpret the
latest message together with the prior user request
and the assistant's clarification question.

5. QUERY REFINEMENT

Combine the original request with the clarification
and produce the refined intent.

6. SQL GENERATION

Generate only valid SQLite SELECT SQL using the
supplied schema.

CRITICAL SPIDER IDENTIFIER RULES:

The schema below contains BOTH:
- original SQLite identifiers, shown after SQL_NAME or COLUMN;
- human-readable labels, shown after "display label".

ONLY use the original SQL_NAME table identifiers and the original
COLUMN identifiers as SQL identifiers. Display labels are for
understanding the user's wording only. NEVER use a display label
as a table or column name in SQL.

- Use table and column names EXACTLY as quoted in the schema.
- Do not replace underscores with spaces or spaces with underscores.
- Do not translate, rename, pluralize, or invent identifiers.
- Quote every table and column identifier with SQLite double quotes.
- Use the FOREIGN KEY RELATIONSHIPS in the schema when joins are needed.
- Do not invent joins or join keys that are not supported by the schema.
- Generate one read-only SELECT statement only.

Example mapping:
Display label: singer in concert
SQL_NAME: "singer_in_concert"

Correct:
SELECT * FROM "singer_in_concert";

Incorrect:
SELECT * FROM "singer in concert";

The original SQLite identifiers in the supplied schema are the ONLY
valid source of table and column names.

DATABASE CANDIDATES:
{candidate_text}

SELECTED DATABASE:
{selected["db_id"]}

SCHEMA — USE THESE IDENTIFIERS EXACTLY:
{schema_text}

CONVERSATION:
{history_text}

CURRENT USER MESSAGE:
{user_message}

Return ONLY valid JSON in exactly this format:

{{
  "state": "answerable",
  "reason": "short explanation",
  "clarification": null,
  "sql": "SELECT ..."
}}

For ambiguous requests:

{{
  "state": "ambiguous",
  "reason": "short explanation",
  "clarification": "one precise clarification question",
  "sql": null
}}

For unanswerable requests:

{{
  "state": "unanswerable",
  "reason": "explain what is missing from the schema",
  "clarification": null,
  "sql": null
}}
"""

    # -----------------------------------------------------
    # 7. Call Gemini
    # -----------------------------------------------------

    try:

        response = completion(
            model="gemini/gemini-3.5-flash-lite",
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            api_key=os.environ["GEMINI_API_KEY"]
        )

        content = response.choices[0].message.content

        result = extract_json_response(content)

    except Exception as exc:

        return {
            "stage": "JID",
            "state": "error",
            "database": selected["db_id"],
            "message": f"Gemini error: {exc}",
            "clarification": None,
            "sql": None,
            "rows": None
        }

    state = result.get(
        "state",
        "ambiguous"
    )

    reason = result.get(
        "reason",
        ""
    )

    clarification = result.get(
        "clarification"
    )

    sql = result.get("sql")

    # -----------------------------------------------------
    # 8. Execute SQL
    # -----------------------------------------------------

    rows = None
    sql_error = None

    if state == "answerable" and sql:

        rows, sql_error = execute_select(
            selected["db_id"],
            sql
        )

        if sql_error:

            state = "unanswerable"

            reason = (
                "The generated SQL could not be executed "
                f"against the selected database: {sql_error}"
            )

            sql = None

    # -----------------------------------------------------
    # 9. Decide UI stage and response
    # -----------------------------------------------------

    if state == "ambiguous":

        stage = "CLARIFY"

        message = (
            clarification
            or
            "I need one clarification before generating SQL."
        )

    elif state == "unanswerable":

        stage = "SCG"

        message = reason or (
            "This request cannot be answered from "
            "the available schema."
        )

    elif state == "answerable":

        stage = "SQL"

        if rows is None:

            message = (
                "I understood the request, but no database "
                "result was produced."
            )

        elif len(rows) == 0:

            message = (
                "The SQL was successfully validated and "
                "executed, but no matching rows were found."
            )

        else:

            message = (
                f"The request was understood and the validated "
                f"SQL was executed against {selected['db_id']}."
            )

    else:

        stage = "JID"

        message = (
            reason
            or
            "I could not confidently determine the intent."
        )

    return {
        "stage": stage,
        "state": state,
        "database": selected["db_id"],
        "message": message,
        "reason": reason,
        "clarification": clarification,
        "sql": sql,
        "rows": rows,
        "candidate_databases": [
            item["db_id"]
            for item in candidates
        ]
    }


# ---------------------------------------------------------
# Health
# ---------------------------------------------------------

@app.get("/api/status")
def status():

    return {
        "system": "ClarifySQL",
        "dataset": "SPIDER",
        "llm": "Gemini",
        "status": "Ready"
    }


# ---------------------------------------------------------
# Categories
# ---------------------------------------------------------

@app.get("/api/categories")
def categories():

    output = []

    for name in CATEGORY_SCRIPTS:

        path = LATEST_OUTPUTS.get(name)

        if path is None:

            output.append({
                "name": name,
                "generated": False,
                "count": 0
            })

            continue

        data = read_jsonl(path)

        output.append({
            "name": name,
            "generated": path.exists(),
            "count": len(data)
        })

    return output


# ---------------------------------------------------------
# Results
# ---------------------------------------------------------

@app.get("/api/results")
def results(
    category: str = "Ambiguous SELECT Column"
):

    candidates = []

    # Find web-generated results.

    web_runs = VSCODE / "web-runs"

    if web_runs.exists():

        for job_dir in web_runs.iterdir():

            if not job_dir.is_dir():
                continue

            split_dir = job_dir / "dev"

            if not split_dir.exists():
                continue

            for jsonl_file in split_dir.glob("*.jsonl"):

                data = read_jsonl(jsonl_file)

                if len(data) > 0:

                    candidates.append(
                        (
                            jsonl_file.stat().st_mtime,
                            jsonl_file,
                            data
                        )
                    )

    # Existing manually generated results.

    fallback_paths = {

        "Ambiguous SELECT Column":
            VSCODE / "output-test3" / "dev" /
            "Ambiguous_SELECT_Column.jsonl",

        "Ambiguous VALUES Across Columns":
            VSCODE / "output-values-across" / "dev" /
            "Ambiguous_VALUES_across_Columns.jsonl"
    }

    fallback = fallback_paths.get(category)

    if fallback and fallback.exists():

        data = read_jsonl(fallback)

        if len(data) > 0:

            candidates.append(
                (
                    fallback.stat().st_mtime,
                    fallback,
                    data
                )
            )

    if not candidates:

        return {
            "category": category,
            "count": 0,
            "results": [],
            "source": None
        }

    candidates.sort(
        key=lambda x: x[0],
        reverse=True
    )

    _, selected_path, selected_data = candidates[0]

    return {
        "category": category,
        "count": len(selected_data),
        "results": selected_data,
        "source": str(selected_path)
    }


# ---------------------------------------------------------
# Start experiment
# ---------------------------------------------------------

@app.post("/api/run")
def run_experiment(request: RunRequest):

    if request.category not in CATEGORY_SCRIPTS:

        raise HTTPException(
            status_code=400,
            detail=f"Unknown category: {request.category}"
        )

    script = CATEGORY_SCRIPTS[request.category]

    if not script.exists():

        raise HTTPException(
            status_code=404,
            detail=f"Python script not found: {script}"
        )

    job_id = uuid.uuid4().hex[:10]

    output_dir = VSCODE / "web-runs" / job_id

    output_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    log_file = output_dir / "run.log"

    env = os.environ.copy()

    env["PYTHONPATH"] = (
        str(SRC)
        + os.pathsep
        + env.get("PYTHONPATH", "")
    )

    command = [
        sys.executable,
        str(script),
        "--spider-data-root-dir",
        str(VSCODE / "combined_data_all" / "spider"),
        "--output-dir",
        str(output_dir),
        "--split",
        request.split,
        "--n2sample",
        str(request.n2sample)
    ]

    log_handle = open(
        log_file,
        "w",
        encoding="utf-8"
    )

    process = subprocess.Popen(
        command,
        cwd=str(ROOT),
        env=env,
        stdout=log_handle,
        stderr=subprocess.STDOUT
    )

    JOBS[job_id] = {
        "process": process,
        "category": request.category,
        "split": request.split,
        "output_dir": output_dir,
        "log_file": log_file,
        "log_handle": log_handle
    }

    return {
        "job_id": job_id,
        "status": "running",
        "category": request.category,
        "message": "Experiment started"
    }


# ---------------------------------------------------------
# Job status
# ---------------------------------------------------------

@app.get("/api/run/{job_id}")
def run_status(job_id: str):

    job = JOBS.get(job_id)

    if job is None:

        raise HTTPException(
            status_code=404,
            detail="Job not found"
        )

    process = job["process"]

    return_code = process.poll()

    status_value = "running"

    if return_code is not None:

        status_value = (
            "completed"
            if return_code == 0
            else "failed"
        )

        try:
            job["log_handle"].close()

        except Exception:
            pass

        if status_value == "completed":

            output_file = (
                job["output_dir"]
                / job["split"]
                / f"{job['category'].replace(' ', '_')}.jsonl"
            )

            if not output_file.exists():

                candidates = list(
                    (
                        job["output_dir"] / job["split"]
                    ).glob("*.jsonl")
                )

                if candidates:
                    output_file = candidates[0]

            if output_file.exists():

                LATEST_OUTPUTS[
                    job["category"]
                ] = output_file

    # Read recent log content.

    log_text = ""

    if job["log_file"].exists():

        try:

            log_text = job["log_file"].read_text(
                encoding="utf-8",
                errors="replace"
            )

        except Exception:

            log_text = ""

    # Detect tqdm progress.

    progress_current = None
    progress_total = None

    matches = re.findall(
        r"(\d+)/(\d+)",
        log_text
    )

    if matches:

        progress_current = int(matches[-1][0])
        progress_total = int(matches[-1][1])

    return {
        "job_id": job_id,
        "status": status_value,
        "category": job["category"],
        "return_code": return_code,
        "progress_current": progress_current,
        "progress_total": progress_total,
        "log_tail": log_text[-2000:]
    }
