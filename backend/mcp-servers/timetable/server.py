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
import logging
from typing import Optional

from fastmcp import FastMCP

# Disable FastMCP's stdout logger banner
logging.getLogger("fastmcp").setLevel(logging.CRITICAL)

# Enable pandas to read our CSV files easily
import pandas as pd

# ==================== CONFIG ====================
TIMETABLE_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data", "timetable")
TIMETABLE_CSV  = os.path.join(TIMETABLE_DIR, "timetable.csv")   # shared / fallback
DEADLINES_CSV  = os.path.join(TIMETABLE_DIR, "deadlines.csv")

mcp = FastMCP("Timetable Server")


# ==================== HELPERS ====================
def _read_csv(filepath: str) -> list[dict]:
    """Read a CSV file and return a list of dicts."""
    if not os.path.exists(filepath):
        return []
    with open(filepath, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return list(reader)


def _group_csv_path(student_group: str) -> str:
    """Return path for a group-specific timetable CSV (e.g. timetable_CS-A.csv)."""
    safe_name = student_group.strip().upper().replace(" ", "-")
    return os.path.join(TIMETABLE_DIR, f"timetable_{safe_name}.csv")


# ==================== TOOLS ====================
@mcp.tool
def get_timetable(day: str, student_group: Optional[str] = None) -> list[dict]:
    """
    Get class schedule for a given day.

    When student_group is provided the server first looks for a group-specific
    file (timetable_CS-A.csv). If that exists, it returns all rows in that file
    matching the day (no further group column filtering needed).
    If the group-specific file does not exist it falls back to the shared
    timetable.csv and filters by the student_group column.

    Args:
        day: Day of the week (e.g., 'Monday', 'Tuesday').
        student_group: Optional student group filter (e.g., 'CS-A', 'CS-B').

    Returns:
        List of classes with time, course_id, course_name, faculty, room, student_group.
    """
    day_lower = day.strip().lower()

    if student_group:
        group_csv = _group_csv_path(student_group)
        if os.path.exists(group_csv):
            # Group-specific file: filter only by day
            rows = _read_csv(group_csv)
            results = [r for r in rows if r.get("day", "").strip().lower() == day_lower]
            if not results:
                return [{"message": f"No classes found for {day} in group {student_group.upper()}"}]
            return results
        # Fall through to shared file with group column filter

    rows = _read_csv(TIMETABLE_CSV)
    if not rows:
        return [{"error": "Timetable data not found. Please ask an admin to upload a timetable."}]

    results = [r for r in rows if r.get("day", "").strip().lower() == day_lower]

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
    # Collect all group-specific files + the shared file
    group_files = []
    if os.path.exists(TIMETABLE_DIR):
        for fname in os.listdir(TIMETABLE_DIR):
            if fname.startswith("timetable_") and fname.endswith(".csv"):
                group_files.append(fname)

    all_rows = []
    for fname in group_files:
        all_rows += _read_csv(os.path.join(TIMETABLE_DIR, fname))
    # Also include shared file if no group files or it has extra data
    shared_rows = _read_csv(TIMETABLE_CSV)
    all_rows += shared_rows

    deadline_rows = _read_csv(DEADLINES_CSV)

    days = sorted(set(r.get("day", "") for r in all_rows if r.get("day")))
    groups = sorted(set(r.get("student_group", "") for r in all_rows if r.get("student_group")))
    # Infer groups from group-specific filenames too
    for fname in group_files:
        g = fname.replace("timetable_", "").replace(".csv", "")
        if g not in groups:
            groups.append(g)
    groups = sorted(groups)
    courses = sorted(set(r.get("course_id", "") for r in all_rows if r.get("course_id")))

    metadata = {
        "available_days": days,
        "student_groups": groups,
        "group_files": group_files,
        "courses": courses,
        "total_timetable_entries": len(all_rows),
        "total_deadlines": len(deadline_rows),
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
