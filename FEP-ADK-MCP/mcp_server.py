from fastmcp import FastMCP
from typing import Optional, Dict, Any, List, Tuple
import requests
import json
import sys
import io
import base64
import matplotlib.pyplot as plt
import pandas as pd
from langchain_experimental.utilities import PythonREPL
import os
from contextlib import redirect_stdout
import pyodbc
import time


mcp = FastMCP("FEP-MCP")

# Pre-import heavy libraries once at server start to avoid per-call overhead
try:
    import pandas as _pd  # type: ignore
except Exception:  # pragma: no cover
    _pd = None  # type: ignore
try:
    import matplotlib as _mpl  # type: ignore
    _mpl.use("Agg")
    import matplotlib.pyplot as _plt  # type: ignore
except Exception:  # pragma: no cover
    _plt = None  # type: ignore

CSV_REMOTE_URL = "https://genaipoddatademo.blob.core.windows.net/csvdata/claims_history(in)_new.csv?sp=r&st=2025-03-10T10:41:01Z&se=2026-03-10T18:41:01Z&spr=https&sv=2022-11-02&sr=b&sig=e3yQB2OaZcT1Lbp8tapOkLf5GSFVWE%2F8sak5UQ0od6A%3D"
CSV_URL = CSV_REMOTE_URL


def _init_csv_cache() -> None:
    """Set CSV_URL to a local file if available; otherwise fall back to remote.

    Avoid performing any network download at import time to prevent startup delays
    that can cause MCP tool calls to time out.
    """
    global CSV_URL
    try:
        local_path = os.path.join(
            os.path.dirname(__file__),
            "agents",
            "claim_agent",
            "data",
            "claims_history(in).csv",
        )
        if os.path.exists(local_path) and os.path.getsize(local_path) > 0:
            CSV_URL = local_path
            return
    except Exception:
        pass
    # Fallback remains the remote URL
    CSV_URL = CSV_REMOTE_URL


# Initialize at import time (fast, no network)
_init_csv_cache()


def python_repl_tool(python_code: str) -> str:
    # Inject commonly used globals to speed up user code and avoid repeated imports
    initial_globals = {"csv_url": CSV_URL}
    if _pd is not None:
        initial_globals["pd"] = _pd
    python_repl = PythonREPL(_globals=initial_globals)
    # Ensure matplotlib doesn't try to open GUI windows; auto-export on show
    try:
        # Prefer pre-imported pyplot if available
        if _plt is None:
            import matplotlib  # type: ignore
            matplotlib.use("Agg")
            import matplotlib.pyplot as plt  # type: ignore
        else:
            plt = _plt  # type: ignore
        import base64 as _b64
        from io import BytesIO as _BytesIO

        def _auto_export_show(*args, **kwargs):
            try:
                buf = _BytesIO()
                try:
                    plt.tight_layout()
                except Exception:
                    pass
                plt.savefig(buf, format="png")
                plt.close()
                buf.seek(0)
                print(_b64.b64encode(buf.read()).decode("utf-8"))
            except Exception:
                # If export fails, just suppress to avoid blocking
                try:
                    plt.close()
                except Exception:
                    pass

        # Expose plt to the REPL and monkey-patch show
        python_repl.globals["plt"] = plt
        try:
            plt.show = _auto_export_show  # type: ignore
        except Exception:
            pass
    except Exception:
        pass
    try:
        f = io.StringIO()
        with redirect_stdout(f):
            try:
                execution_result = python_repl.run(python_code)
            except Exception as e:
                execution_result = f"[Execution Error] {e}"
        output = f.getvalue().strip()
        if not output:
            output = execution_result or "[No output]"
    except Exception as e:
        output = f"[Execution Error] {e}"
    return output


@mcp.tool()
def run_claims_analysis(python_code: str) -> str:
    """Execute Python code against claims CSV file."""
    return python_repl_tool(python_code)


# --- DB Config from environment (assumes load_dotenv() called elsewhere) ---
sql_driver = os.getenv("SQL_DRIVER", "ODBC Driver 18 for SQL Server")
sql_server_name = os.getenv("SQL_SERVER_NAME")
sql_database_name = os.getenv("SQL_DATABASE_NAME")
sql_db_username = os.getenv("SQL_DB_USERNAME")
sql_db_password = os.getenv("SQL_DB_PASSWORD")

DB_AVAILABLE = all([sql_server_name, sql_database_name,
                   sql_db_username, sql_db_password])


def _build_connection_string(driver: str) -> str:
    return (
        f"DRIVER={{{driver}}};"
        f"SERVER={sql_server_name};"
        f"DATABASE={sql_database_name};"
        f"UID={sql_db_username};"
        f"PWD={sql_db_password};"
        f"Encrypt=yes;"
        f"TrustServerCertificate=no;"
        f"Connection Timeout=30;"
    )


connection_string = _build_connection_string(
    sql_driver) if DB_AVAILABLE else None


def get_db_connection(retries=1, delay=1):
    if not DB_AVAILABLE:
        raise RuntimeError("Database configuration not available")
    for attempt in range(retries):
        try:
            return pyodbc.connect(connection_string, timeout=2)
        except pyodbc.Error as e:
            print(
                f"Attempt {attempt + 1} - Error connecting to database: {e}", file=sys.stderr)
            if attempt == retries - 1:
                try:
                    alt_driver = "ODBC Driver 17 for SQL Server" if "18" in sql_driver else "ODBC Driver 18 for SQL Server"
                    alt_conn_str = _build_connection_string(alt_driver)
                    print(
                        f"Trying alternate SQL Server driver: {alt_driver}", file=sys.stderr)
                    return pyodbc.connect(alt_conn_str, timeout=2)
                except Exception:
                    pass
            if attempt < retries - 1:
                time.sleep(delay)
            else:
                raise


def get_schema() -> List[Dict[str, Any]]:
    if not DB_AVAILABLE:
        return [{"error": "Database not configured. Set SQL_* env vars."}]
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT
                t.name AS table_name,
                c.name AS column_name,
                typ.name AS data_type
            FROM sys.tables AS t
            JOIN sys.columns AS c ON t.object_id = c.object_id
            JOIN sys.types AS typ ON c.user_type_id = typ.user_type_id
            WHERE t.is_ms_shipped = 0
            ORDER BY t.name, c.column_id;
        """)
        schema_data = cursor.fetchall()
        formatted_schema = {}
        for table, column, data_type in schema_data:
            if table not in formatted_schema:
                formatted_schema[table] = []
            formatted_schema[table].append(
                {"column": column, "type": data_type})
        return [{"table_name": table, "columns": cols} for table, cols in formatted_schema.items()]
    except pyodbc.Error as ex:
        return [{"error": f"Database schema retrieval failed: {ex}"}]
    finally:
        if conn:
            conn.close()


def execute_read_query(query: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    if not DB_AVAILABLE:
        return [{"error": "Database not configured. Set SQL_* env vars."}]
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        if params:
            cursor.execute(query, list(params.values()))
        else:
            cursor.execute(query)
        columns = [column[0] for column in cursor.description]
        results = [dict(zip(columns, row)) for row in cursor.fetchall()]
        return results
    except pyodbc.Error as ex:
        return [{"error": f"Database query failed: {ex}"}]
    finally:
        if conn:
            conn.close()


def execute_write_query(query: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    if not DB_AVAILABLE:
        return {"error": "Database not configured. Set SQL_* env vars."}
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        if params:
            cursor.execute(query, list(params.values()))
        else:
            cursor.execute(query)
        conn.commit()
        return {"rows_affected": cursor.rowcount}
    except pyodbc.Error as ex:
        if conn:
            conn.rollback()
        return {"error": f"Database write failed: {ex}"}
    finally:
        if conn:
            conn.close()


# --- FastMCP Tools ---

@mcp.tool()
def get_db_schema() -> List[Dict[str, Any]]:
    """Retrieve database schema (tables and columns)."""
    return get_schema()


@mcp.tool()
def run_read_query(query: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    """Execute a read-only SQL query."""
    return execute_read_query(query, params)


@mcp.tool()
def run_write_query(query: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Execute a write (INSERT/UPDATE/DELETE) SQL query."""
    return execute_write_query(query, params)


@mcp.tool()
def get_member_info(member_id: str, search_key: Optional[str] = None) -> Dict[str, Any]:
    """
    Retrieve a member's information by ID, with optional keyword-based field search.
    """
    file_url = "https://genaipoddatademo.blob.core.windows.net/csvdata/dummy_patient_data_new.json?sp=r&st=2025-03-24T12:44:37Z&se=2026-03-24T20:44:37Z&spr=https&sv=2024-11-04&sr=b&sig=vtt19xTWblJaIFdxByvdNRM6j5C8CoZxeTqAaRccI90%3D"
    print(f"Searching for member_id: {member_id}, search_key: {search_key}")

    try:
        response = requests.get(file_url)
        response.raise_for_status()
        data = response.json()
    except (requests.RequestException, json.JSONDecodeError) as e:
        print(f"Error fetching JSON: {e}", file=sys.stderr)
        return {"status": "error", "message": "Failed to fetch member data."}

    member = next((record for record in data if record.get(
        "member_id") == member_id), None)

    if not member:
        return {"status": "not_found", "message": f"No member found with ID: {member_id}"}

    if not search_key:
        return {"status": "success", "member_data": member}

    results: List[Tuple[str, Any]] = []

    def recursive_search(obj: Any, key_fragment: str):
        if isinstance(obj, dict):
            for key, value in obj.items():
                if key_fragment.lower() in key.lower():
                    results.append((key, value))
                if isinstance(value, (dict, list)):
                    recursive_search(value, key_fragment)
        elif isinstance(obj, list):
            for item in obj:
                recursive_search(item, key_fragment)

    recursive_search(member, search_key)

    return {
        "status": "success",
        "member_id": member_id,
        "search_key": search_key,
        "matches": results or [],
        "match_count": len(results)
    }


@mcp.tool()
def generate_graph_from_code(code: str) -> Dict[str, Any]:
    """
    Execute Python code that generates a matplotlib plot, and return the image.

    The code must generate a plot using matplotlib and should call plt.plot(), plt.bar(), etc.
    """
    try:
        # Redirect output buffer (if needed)
        old_stdout = sys.stdout
        sys.stdout = io.StringIO()

        # Clean up previous figures
        plt.close('all')

        # Restricted globals (you can add more libs if needed)
        safe_globals = {
            "__builtins__": __builtins__,
            "plt": plt,
        }

        # Execute the code
        exec(code, safe_globals)

        # Save the figure to a buffer
        buf = io.BytesIO()
        plt.savefig(buf, format='png')
        buf.seek(0)
        image_base64 = base64.b64encode(buf.read()).decode('utf-8')
        buf.close()

        # Get stdout output
        output = sys.stdout.getvalue()
        sys.stdout = old_stdout

        return {
            "status": "success",
            "output": output.strip(),
            "image_base64": image_base64
        }

    except Exception as e:
        sys.stdout = old_stdout
        return {
            "status": "error",
            "message": f"Execution failed: {str(e)}"
        }


# ---- Run server ----
if __name__ == "__main__":
    mcp.run()
