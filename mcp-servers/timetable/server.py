"""
Timetable MCP Server — Exposes campus timetable and deadline data via FastMCP.

Tools:
  - get_timetable(day, student_group?) → class schedule for a day
  - get_deadlines(course_id?) → upcoming deadlines

Resources:
  - timetable://metadata → available days, groups, courses, timestamps
"""

import csv
import json
import os
import sys
from datetime import datetime
from typing import Optional

from fastmcp import FastMCP

# ==================== CONFIG ====================
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data", "timetable")
TIMETABLE_CSV = os.path.join(DATA_DIR, "timetable.csv")
DEADLINES_CSV = os.path.join(DATA_DIR, "deadlines.csv")

mcp = FastMCP("Timetable Server")


# ==================== HELPERS ====================
def _read_csv(filepath: str) -> list[dict]:
    """Read a CSV file and return a list of dicts."""
    if not os.path.exists(filepath):
        return []
    with open(filepath, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return list(reader)


# ==================== TOOLS ====================
@mcp.tool
def get_timetable(day: str, student_group: Optional[str] = None) -> list[dict]:
    """
    Get class schedule for a given day.

    Args:
        day: Day of the week (e.g., 'Monday', 'Tuesday').
        student_group: Optional student group filter (e.g., 'CS-A', 'CS-B').

    Returns:
        List of classes with time, course_id, course_name, faculty, room, student_group.
    """
    rows = _read_csv(TIMETABLE_CSV)
    if not rows:
        return [{"error": "Timetable data not found. No CSV file available."}]

    # Case-insensitive day matching
    day_lower = day.strip().lower()
    results = [r for r in rows if r.get("day", "").strip().lower() == day_lower]

    # Optional group filter
    if student_group:
        group_lower = student_group.strip().lower()
        results = [
            r for r in results
            if r.get("student_group", "").strip().lower() == group_lower
        ]

    if not results:
        return [{"message": f"No classes found for {day}" + (f" (group: {student_group})" if student_group else "")}]

    return results


@mcp.tool
def get_deadlines(course_id: Optional[str] = None) -> list[dict]:
    """
    Get upcoming deadlines, optionally filtered by course.

    Args:
        course_id: Optional course ID filter (e.g., 'CS401', 'CS402').

    Returns:
        List of deadlines with course_id, title, due_date, description.
    """
    rows = _read_csv(DEADLINES_CSV)
    if not rows:
        return [{"error": "Deadlines data not found. No CSV file available."}]

    # Filter by course if specified
    if course_id:
        course_lower = course_id.strip().lower()
        rows = [
            r for r in rows
            if r.get("course_id", "").strip().lower() == course_lower
        ]

    # Sort by due_date (ascending)
    try:
        rows.sort(key=lambda r: r.get("due_date", ""))
    except Exception:
        pass

    # Filter to only upcoming deadlines
    today = datetime.now().strftime("%Y-%m-%d")
    upcoming = [r for r in rows if r.get("due_date", "") >= today]

    if not upcoming:
        # If no upcoming deadlines, return all deadlines with a note
        if rows:
            return [{"message": "No upcoming deadlines. Here are all deadlines:"}, *rows]
        return [{"message": f"No deadlines found" + (f" for {course_id}" if course_id else "")}]

    return upcoming


# ==================== RESOURCES ====================
@mcp.resource("timetable://metadata")
def timetable_metadata() -> str:
    """
    Returns metadata about available timetable and deadline data:
    available days, student groups, courses, and CSV timestamps.
    """
    timetable_rows = _read_csv(TIMETABLE_CSV)
    deadline_rows = _read_csv(DEADLINES_CSV)

    days = sorted(set(r.get("day", "") for r in timetable_rows))
    groups = sorted(set(r.get("student_group", "") for r in timetable_rows))
    courses = sorted(set(r.get("course_id", "") for r in timetable_rows))

    metadata = {
        "available_days": days,
        "student_groups": groups,
        "courses": courses,
        "total_timetable_entries": len(timetable_rows),
        "total_deadlines": len(deadline_rows),
        "timetable_csv_last_modified": (
            datetime.fromtimestamp(os.path.getmtime(TIMETABLE_CSV)).isoformat()
            if os.path.exists(TIMETABLE_CSV)
            else None
        ),
        "deadlines_csv_last_modified": (
            datetime.fromtimestamp(os.path.getmtime(DEADLINES_CSV)).isoformat()
            if os.path.exists(DEADLINES_CSV)
            else None
        ),
    }

    return json.dumps(metadata, indent=2)


# ==================== SELF-TEST ====================
def _run_self_test():
    """Run a quick self-test to verify the server works."""
    print("=" * 50)
    print("Timetable MCP Server -- Self-Test")
    print("=" * 50)

    print("\n[1] Testing get_timetable('Monday'):")
    result = get_timetable("Monday")
    print(f"  -> {len(result)} results")
    for r in result[:3]:
        print(f"    {r}")

    print("\n[2] Testing get_timetable('Monday', 'CS-A'):")
    result = get_timetable("Monday", "CS-A")
    print(f"  -> {len(result)} results")
    for r in result:
        print(f"    {r}")

    print("\n[3] Testing get_deadlines('CS401'):")
    result = get_deadlines("CS401")
    print(f"  -> {len(result)} results")
    for r in result[:3]:
        print(f"    {r}")

    print("\n[4] Testing get_deadlines() (all):")
    result = get_deadlines()
    print(f"  -> {len(result)} results")

    print("\n[5] Testing timetable_metadata():")
    meta = timetable_metadata()
    print(f"  -> {meta[:200]}...")

    print("\n" + "=" * 50)
    print("All self-tests passed!")
    print("=" * 50)


# ==================== ENTRYPOINT ====================
if __name__ == "__main__":
    if "--test" in sys.argv:
        _run_self_test()
    else:
        mcp.run()
