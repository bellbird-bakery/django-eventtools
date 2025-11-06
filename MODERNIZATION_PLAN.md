# Django-Eventtools Modernization Plan

**Version:** 2.0.0
**Started:** 2025-11-06
**Status:** Phases 1-4 Complete, Ready for Phase 5+

---

## Executive Summary

This document outlines a comprehensive modernization plan for django-eventtools, a Django library for managing recurring and one-off event occurrences. The library was originally developed circa 2015-2017 and needs updating to modern Python/Django standards.

### Current State
- **Version:** 1.0.3 → 2.0.0 (major version bump)
- **Python Support:** 2.7, 3.4-3.8 → 3.9-3.12
- **Django Support:** 1.8+ → 3.2 LTS, 4.2 LTS, 5.0+
- **Package Management:** setup.py → pyproject.toml + uv
- **Type Hints:** None → Comprehensive type hints throughout

---

## Original Analysis

### What the Library Does

django-eventtools is a lightweight library for handling repeating and one-off event occurrences using RFC 5545 recurrence rules (rrule format). It provides:

1. **BaseEvent** - Represents an event (e.g., "Christmas Party")
2. **BaseOccurrence** - Represents when/how often an event occurs
3. On-the-fly occurrence generation via Python generators
4. Django ORM integration with querysets and managers

### Key Findings (Issues Identified)

#### 1. Outdated Dependencies
- Python 2/3 compatibility layer (`six`) no longer needed
- Support for EOL Python versions (2.7, 3.4, 3.5)
- Old Django versions (1.8-2.x)

#### 2. Performance Concerns
- `exact=True` filtering iterates all objects - O(n) complexity
- `sort_by_next()` evaluates every object's next occurrence
- Manual generator merging instead of `heapq.merge()`
- Hard-coded limits (REPEAT_MAX = 200)

#### 3. Missing Modern Features
- No type hints
- No async support
- No modern packaging (still using setup.py)
- Mixed coding styles

#### 4. API Design Issues
- `sort_by_next()` returns list instead of queryset
- Plain tuples `(start, end, instance)` instead of named tuples
- Inconsistent behavior across Event/Occurrence/QuerySet

#### 5. Code Quality
- `as_datetime()` uses `type(d) is date` instead of `isinstance()`
- Some unclear variable names
- Lack of comprehensive docstrings
- Migration helper suggests API changed

---

## Modernization Phases

### ✅ Phase 1: Drop Legacy Python/Django Support (COMPLETED)

**Status:** ✅ Complete
**Time Spent:** ~1 hour

#### Changes Made:
- ✅ Removed `six` dependency completely
- ✅ Removed `@python_2_unicode_compatible` decorators
- ✅ Updated setup.py dependencies:
  - Django: `>=1.8` → `>=3.2`
  - python-dateutil: `>=2.1` → `>=2.8.2`
  - Removed six dependency
  - Added `python_requires='>=3.9'`
- ✅ Updated Python version classifiers (3.9, 3.10, 3.11, 3.12)
- ✅ Added Django framework classifiers (3.2, 4.2, 5.0)
- ✅ Updated tox.ini for Python 3.9-3.12 × Django 3.2/4.2/5.0 matrix
- ✅ Bumped version: 1.0.3 → 2.0.0

#### Files Modified:
```
eventtools/_version.py    |  1 line changed
eventtools/models.py      |  3 lines removed
setup.py                  | 14 lines changed
tests/models.py           |  2 lines removed
tox.ini                   | 44 lines rewritten
```

---

### ✅ Phase 2: Add Type Hints Throughout Codebase (COMPLETED)

**Status:** ✅ Complete
**Time Spent:** ~2 hours

#### Changes Made:
- ✅ Created mypy.ini configuration with strict settings
- ✅ Added eventtools/py.typed marker file (PEP 561 compliance)
- ✅ Updated setup.py to include py.typed in package_data
- ✅ Added `from __future__ import annotations` for forward references
- ✅ Created **OccurrenceTuple NamedTuple** to replace plain tuples:
  ```python
  class OccurrenceTuple(NamedTuple):
      start: datetime
      end: datetime | None
      instance: BaseOccurrence
  ```

#### Type Hints Added:

**Utility Functions (9 functions):**
- `max_future_date() -> datetime`
- `first_item(gen: Generator[OccurrenceTuple, None, None]) -> OccurrenceTuple | None`
- `default_aware(dt: datetime) -> datetime`
- `default_naive(dt: datetime) -> datetime`
- `as_datetime(d: date | datetime, end: bool = False) -> datetime`
- `combine_occurrences(...) -> Generator[OccurrenceTuple, None, None]`
- `filter_invalid(approx_qs: BaseQuerySet, ...) -> BaseQuerySet`
- `filter_from(qs: BaseQuerySet, ...) -> BaseQuerySet`

**Classes (26 methods typed):**
- OccurrenceMixin: `all_occurrences()`, `next_occurrence()`, `first_occurrence()`
- BaseQuerySet: `for_period()`, `sort_by_next()`, `all_occurrences()`
- EventQuerySet: `for_period()` with return type `EventQuerySet`
- BaseEvent: `get_occurrence_relation()`, `occurrence_filter_prefix()`, etc.
- OccurrenceQuerySet: `for_period()` with return type `OccurrenceQuerySet`
- OccurrenceManager: `migrate_integer_repeat() -> int`
- BaseOccurrence: All methods fully typed including `get_repeater() -> rrule.rruleset`

#### Files Modified:
```
eventtools/models.py     | 151 lines changed (type hints, OccurrenceTuple)
eventtools/py.typed      | New file (PEP 561 marker)
mypy.ini                 | New file (type checker config)
setup.py                 | 2 lines changed (include py.typed)
tests/models.py          | 4 lines changed (type hints)
```

#### Benefits:
- ✅ 100% of public API is now type-hinted
- ✅ Better IDE support (autocomplete, type checking)
- ✅ Catches type errors at development time
- ✅ PEP 561 compliant for downstream projects
- ✅ Uses modern Python 3.9+ syntax (`|` union operator)

---

### ✅ UV Project Setup (COMPLETED)

**Status:** ✅ Complete
**Time Spent:** ~1 hour

#### New Files Created:

1. **pyproject.toml** (128 lines)
   - Modern packaging with hatchling backend
   - Project metadata and dependencies
   - Optional dependency groups: `dev`, `test`
   - Tool configurations: pytest, ruff, mypy

2. **.python-version**
   - Set to Python 3.12

3. **.gitignore** (145 lines)
   - Python, Django, uv, and IDE patterns

4. **DEVELOPMENT.md** (220 lines)
   - Quick start guide
   - Development workflows
   - Common tasks
   - Troubleshooting

5. **Makefile** (51 lines)
   - Convenient task automation
   - Commands: test, lint, format, typecheck, etc.

#### Environment Setup:
- ✅ uv 0.5.4 installed and working
- ✅ Virtual environment created at `.venv/`
- ✅ 22 packages installed (Django 5.2.8, mypy, pytest, ruff, etc.)
- ✅ Tests running: 16/19 passing (3 timezone-related failures are pre-existing)
- ✅ Linting working: ruff auto-fixed 11 style issues
- ✅ Type checking configured

#### Quick Commands:
```bash
make test        # Run tests
make lint        # Check code style
make lint-fix    # Auto-fix issues
make typecheck   # Run mypy
make all         # Run all checks
```

---

## 🔄 Remaining Phases

### ✅ Phase 3: Performance Optimizations (COMPLETED)

**Status:** ✅ Complete
**Time Spent:** ~2 hours
**Priority:** High
**Breaking Changes:** Minimal (progress_callback parameter added to filter_invalid)

#### Changes Made:

- ✅ **Replaced manual generator merging with heapq.merge()**
  - Simplified combine_occurrences() from ~40 lines to ~15 lines
  - Performance improvement: O(n*m) → O(n log k) where k is number of generators
  - More maintainable using battle-tested stdlib implementation

- ✅ **Added database indexes for BaseOccurrence**
  - Composite index on (start, end) fields
  - Index on repeat_until field
  - Improves query performance for date range filtering

- ✅ **Optimized filter_invalid() function**
  - Added optional progress_callback parameter for tracking
  - Uses .iterator(chunk_size=100) for memory efficiency
  - Enhanced docstring with performance warnings
  - Better handling of large querysets

- ✅ **Made REPEAT_MAX configurable**
  - Now uses EVENTTOOLS_REPEAT_MAX Django setting (default: 200)
  - Per-query override via limit parameter
  - Documented in all_occurrences() docstring

- ✅ **Enhanced get_related_occurrences() method**
  - Added .order_by('start') for efficient processing
  - Added comprehensive docstring with optimization examples
  - Documented select_related/prefetch_related patterns

#### Files Modified:
```
eventtools/models.py     | 80 lines changed (imports, functions, indexes, docs)
MODERNIZATION_PLAN.md    | Phase 3 marked complete
```

#### Testing:
- ✅ 18/19 tests passing (1 pre-existing timezone failure)
- ✅ No tests broken by changes
- ✅ Type hints validated

#### Deferred Items:
- **QuerySet Caching** - Deferred to Phase 7 (Optional Enhancements)
  - Full caching implementation with Django cache framework
  - Cache invalidation and management
  - Better suited for 2.1.0+ as optional feature

---

#### Original Tasks (for reference):

1. **Replace Manual Generator Merging** (eventtools/models.py:89-128)
   - Current: Manual `combine_occurrences()` with list of dicts
   - Replace with: `heapq.merge()` with custom key function
   - Benefit: More efficient, battle-tested stdlib implementation

   ```python
   import heapq

   def combine_occurrences(
       generators: Iterator[Generator[OccurrenceTuple, None, None]],
       limit: int | None
   ) -> Generator[OccurrenceTuple, None, None]:
       """Merge occurrences using heapq for better performance."""
       # Use heapq.merge with key function for start datetime
       merged = heapq.merge(*generators, key=lambda occ: occ.start)

       if limit is None:
           yield from merged
       else:
           for i, occurrence in enumerate(merged):
               if i >= limit:
                   return
               yield occurrence
   ```

2. **Add Database Indexes**
   - Add composite index on `(start, end)` for BaseOccurrence
   - Add index on `repeat_until` field
   - Document in migration guide

   ```python
   class BaseOccurrence(BaseModel):
       # ... fields ...

       class Meta:
           ordering = ('start', 'end')
           abstract = True
           indexes = [
               models.Index(fields=['start', 'end']),
               models.Index(fields=['repeat_until']),
           ]
   ```

3. **Optimize `filter_invalid()`** (eventtools/models.py:131-146)
   - Current: Iterates through queryset, builds list of PKs to exclude
   - Improvement: Add progress callback, consider caching, use bulk operations
   - Add performance warning in docstring

   ```python
   def filter_invalid(
       approx_qs: BaseQuerySet,
       from_date: date | datetime | None,
       to_date: date | datetime | None,
       progress_callback: Callable[[int, int], None] | None = None
   ) -> BaseQuerySet:
       """Filter out invalid results. WARNING: O(n) operation for large querysets.

       Args:
           approx_qs: Queryset to filter
           from_date: Start date
           to_date: End date
           progress_callback: Optional callback(current, total) for progress tracking
       """
       # Use .values_list('pk', flat=True).iterator() for memory efficiency
       total = approx_qs.count()
       exclude_pks = []

       for i, obj in enumerate(approx_qs.iterator(chunk_size=100)):
           if progress_callback:
               progress_callback(i + 1, total)
           if not obj.next_occurrence(from_date=from_date, to_date=to_date):
               exclude_pks.append(obj.pk)

       return approx_qs.exclude(pk__in=exclude_pks)
   ```

4. **Make REPEAT_MAX Configurable**
   - Allow per-query limit override
   - Add Django setting: `EVENTTOOLS_REPEAT_MAX`
   - Document in README

   ```python
   def all_occurrences(
       self,
       from_date: date | datetime | None = None,
       to_date: date | datetime | None = None,
       limit: int | None = None
   ) -> Generator[OccurrenceTuple, None, None]:
       if limit is None:
           limit = getattr(settings, 'EVENTTOOLS_REPEAT_MAX', REPEAT_MAX)
       # ... rest of implementation
   ```

5. **Add QuerySet Caching**
   - Cache `next_occurrence()` results for repeated calls
   - Use Django's cache framework or simple LRU cache
   - Make optional via setting

   ```python
   from functools import lru_cache

   class BaseOccurrence(BaseModel):
       def _cache_key(self, from_date, to_date):
           return f"occ_{self.pk}_{from_date}_{to_date}"

       def next_occurrence(
           self,
           from_date: date | datetime | None = None,
           to_date: date | datetime | None = None,
           use_cache: bool = True
       ) -> OccurrenceTuple | None:
           if use_cache and getattr(settings, 'EVENTTOOLS_CACHE_OCCURRENCES', False):
               cache_key = self._cache_key(from_date, to_date)
               cached = cache.get(cache_key)
               if cached:
                   return cached

           result = first_item(self.all_occurrences(from_date, to_date))

           if use_cache and result:
               cache.set(cache_key, result, timeout=300)  # 5 min cache

           return result
   ```

6. **Optimize QuerySet Select Operations**
   - Add `select_related()` / `prefetch_related()` hints in documentation
   - Consider adding helper methods for common patterns

   ```python
   # In BaseEvent
   def get_related_occurrences(self) -> OccurrenceQuerySet:
       """Get related occurrences with optimized query."""
       rel = self.get_occurrence_relation()
       return getattr(self, rel.get_accessor_name()).all().order_by('start')
   ```

#### Files to Modify:
- eventtools/models.py:89-128 (combine_occurrences)
- eventtools/models.py:131-146 (filter_invalid)
- eventtools/models.py:27 (REPEAT_MAX)
- eventtools/models.py:432-484 (BaseOccurrence.all_occurrences)
- Add migration for new indexes

#### Testing Plan:
- Benchmark before/after with `pytest-benchmark`
- Test with 1, 10, 100, 1000, 10000 occurrences
- Verify exact=True performance with progress callback
- Memory profiling for large querysets

---

### ✅ Phase 4: Improve API Consistency (COMPLETED)

**Status:** ✅ Complete
**Time Spent:** ~1 hour
**Priority:** Medium
**Breaking Changes:** Minimal (deprecation warnings only)

#### Changes Made:

- ✅ **Added deprecation warning to sort_by_next()**
  - Enhanced docstring with detailed warnings about return type
  - Added PendingDeprecationWarning to inform users
  - Documented performance implications
  - Warning caught in tests showing it works correctly

- ✅ **Enhanced occurrence_data property**
  - Added comprehensive docstring with 30+ lines of documentation
  - Included use cases and examples
  - Showed caching and enrichment patterns
  - Better guidance for subclass overrides

- ✅ **Added __repr__() methods**
  - BaseOccurrence.__repr__(): Shows pk, start, end, repeat
  - BaseEvent.__repr__(): Shows pk and string representation
  - Improved debugging experience in Python shell and logs

- ✅ **Reviewed parameter naming**
  - Verified consistency across all methods
  - Confirmed from_date/to_date pattern used throughout
  - No changes needed - already well-standardized

- ✅ **Improved ValidationError messages**
  - Enhanced clean() method with detailed error messages
  - Added current values to error messages for context
  - Included actionable suggestions for fixing issues
  - Multi-line formatted help for complex errors

#### Files Modified:
```
eventtools/models.py     | 85 lines changed (warnings, docs, repr, validation)
MODERNIZATION_PLAN.md    | Phase 4 marked complete
```

#### Testing:
- ✅ 18/19 tests passing (1 pre-existing timezone failure)
- ✅ Deprecation warnings working correctly (caught in test output)
- ✅ No tests broken by changes

---

#### Original Tasks (for reference):

1. **OccurrenceTuple Already Created** ✅
   - Done in Phase 2
   - Named access: `occ.start`, `occ.end`, `occ.instance`

2. **Fix `sort_by_next()` Return Type**
   - Current: Returns a list (breaks queryset chaining)
   - Option A: Return QuerySet-like object with __iter__
   - Option B: Add `order_by_next()` that returns actual QuerySet
   - Option C: Document clearly and provide alternative

   Recommended: Add new method, deprecate old one
   ```python
   class BaseQuerySet(models.QuerySet, OccurrenceMixin):
       def sort_by_next(self, from_date: date | datetime | None = None):
           """DEPRECATED: Use order_by_next() for queryset-like behavior.

           This method returns a list, not a queryset.
           """
           warnings.warn(
               "sort_by_next() is deprecated. Use order_by_next() or convert "
               "to list explicitly: list(qs.order_by_next())",
               DeprecationWarning,
               stacklevel=2
           )
           return self._sort_by_next_list(from_date)

       def order_by_next(self, from_date: date | datetime | None = None):
           """Return queryset-like iterator ordered by next occurrence.

           Note: This returns an iterator, not a full QuerySet. Some QuerySet
           methods won't be available after calling this.
           """
           return SortedOccurrenceIterator(self, from_date)
   ```

3. **Enhance `occurrence_data` Property**
   - Current: Just returns `self`
   - Make more useful or document override pattern better
   - Add example of custom data in docstring

   ```python
   @property
   def occurrence_data(self) -> BaseOccurrence:
       """Return data for this occurrence.

       Subclasses can override to return modified data or a related object.

       Example:
           class MyOccurrence(BaseOccurrence):
               @property
               def occurrence_data(self):
                   # Return self with cached event data
                   if not hasattr(self, '_cached_event'):
                       self._cached_event = self.event
                   return self
       """
       return self
   ```

4. **Add `__repr__()` Methods**
   - Better debugging experience
   - Show key fields

   ```python
   class BaseOccurrence(BaseModel):
       def __repr__(self) -> str:
           return (
               f"<{self.__class__.__name__}("
               f"start={self.start!r}, "
               f"end={self.end!r}, "
               f"repeat={self.repeat!r})>"
           )
   ```

5. **Standardize Parameter Names**
   - Review all methods for consistency
   - Document naming conventions
   - Use `from_date`/`to_date` consistently (not `from_dt`, etc.)

6. **Better Error Messages**
   - ValidationError messages could be more helpful
   - Add suggestions for fixes

   ```python
   def clean(self) -> None:
       if self.start and self.end and self.start >= self.end:
           raise ValidationError(
               "End time must be after start time. "
               f"Got start={self.start}, end={self.end}. "
               "Did you accidentally swap them?"
           )
   ```

#### Files to Modify:
- eventtools/models.py:205-216 (sort_by_next)
- eventtools/models.py:497-499 (occurrence_data)
- eventtools/models.py (add __repr__ methods)
- eventtools/models.py:415-428 (clean method)

#### Migration Strategy:
- Use deprecation warnings for breaking changes
- Document migration path in MIGRATION.md
- Keep old behavior available for 1-2 minor versions

---

### Phase 5: Modern Testing and CI/CD

**Priority:** High
**Breaking Changes:** No
**Estimated Time:** 1-2 weeks

#### Tasks:

1. **GitHub Actions Workflow**
   - Replace/supplement CircleCI
   - Test matrix: Python 3.9-3.12 × Django 3.2/4.2/5.0
   - Multiple OS: Linux, macOS, Windows
   - Coverage reporting to codecov

   Create `.github/workflows/test.yml`:
   ```yaml
   name: Tests

   on: [push, pull_request]

   jobs:
     test:
       runs-on: ${{ matrix.os }}
       strategy:
         fail-fast: false
         matrix:
           os: [ubuntu-latest, macos-latest, windows-latest]
           python-version: ["3.9", "3.10", "3.11", "3.12"]
           django-version: ["3.2", "4.2", "5.0"]
           exclude:
             # Django 5.0 doesn't support Python 3.9
             - python-version: "3.9"
               django-version: "5.0"

       steps:
         - uses: actions/checkout@v4
         - uses: astral-sh/setup-uv@v1
         - name: Set up Python ${{ matrix.python-version }}
           run: uv python install ${{ matrix.python-version }}
         - name: Install dependencies
           run: |
             uv pip install -e ".[test]"
             uv pip install "Django~=${{ matrix.django-version }}.0"
         - name: Run tests
           run: uv run pytest -v --cov=eventtools
         - name: Upload coverage
           uses: codecov/codecov-action@v3

     lint:
       runs-on: ubuntu-latest
       steps:
         - uses: actions/checkout@v4
         - uses: astral-sh/setup-uv@v1
         - name: Set up Python
           run: uv python install 3.12
         - name: Install dependencies
           run: uv pip install -e ".[dev]"
         - name: Run ruff
           run: uv run ruff check eventtools tests
         - name: Run mypy
           run: uv run mypy eventtools
   ```

2. **Pre-commit Hooks**
   - Auto-format with ruff
   - Type check with mypy
   - Run quick tests

   Create `.pre-commit-config.yaml`:
   ```yaml
   repos:
     - repo: https://github.com/astral-sh/ruff-pre-commit
       rev: v0.1.6
       hooks:
         - id: ruff
           args: [--fix]
         - id: ruff-format

     - repo: https://github.com/pre-commit/mirrors-mypy
       rev: v1.7.0
       hooks:
         - id: mypy
           additional_dependencies: [django-stubs, types-python-dateutil]
   ```

3. **Migrate to pytest (Already Done) ✅**
   - Tests already use pytest via pyproject.toml
   - Consider adding fixtures for common test data
   - Add parametrized tests where appropriate

4. **Add Performance Benchmarks**
   - Use pytest-benchmark
   - Test occurrence generation with various limits
   - Track performance over time

   Create `tests/benchmarks.py`:
   ```python
   import pytest
   from datetime import datetime, date
   from tests.models import MyEvent, MyOccurrence

   @pytest.mark.benchmark
   def test_occurrence_generation_benchmark(benchmark, db):
       event = MyEvent.objects.create(title='Daily Event')
       occ = MyOccurrence.objects.create(
           event=event,
           start=datetime(2024, 1, 1, 9, 0),
           repeat="RRULE:FREQ=DAILY"
       )

       def generate_occurrences():
           return list(occ.all_occurrences(
               from_date=date(2024, 1, 1),
               to_date=date(2024, 12, 31),
               limit=365
           ))

       result = benchmark(generate_occurrences)
       assert len(result) == 365
   ```

5. **Coverage Requirements**
   - Add coverage reporting
   - Set minimum coverage threshold (e.g., 90%)
   - Add coverage badge to README

6. **Add Mutation Testing** (Optional)
   - Use mutmut to verify test quality
   - Catch undertested code paths

#### Files to Create:
- .github/workflows/test.yml
- .github/workflows/publish.yml
- .pre-commit-config.yaml
- tests/benchmarks.py
- tests/conftest.py (pytest fixtures)

#### Files to Modify:
- README.md (add badges)
- pyproject.toml (add pytest-benchmark)

---

### Phase 6: Documentation Improvements

**Priority:** Medium
**Breaking Changes:** No
**Estimated Time:** 1 week

#### Tasks:

1. **Add Comprehensive Docstrings**
   - Use Google style docstrings
   - Document all public methods
   - Include examples in docstrings

   Example:
   ```python
   def all_occurrences(
       self,
       from_date: date | datetime | None = None,
       to_date: date | datetime | None = None,
       limit: int = REPEAT_MAX
   ) -> Generator[OccurrenceTuple, None, None]:
       """Generate all occurrences within the specified date range.

       This method generates occurrence tuples on-the-fly using Python
       generators for memory efficiency. For repeating occurrences, it
       uses python-dateutil's rrule to calculate recurrence.

       Args:
           from_date: Start of date range (inclusive). Defaults to occurrence start.
           to_date: End of date range (inclusive). Defaults to repeat_until or
                   10 years from now.
           limit: Maximum number of occurrences to generate. Prevents infinite
                 loops for repeating events. Defaults to REPEAT_MAX (200).

       Yields:
           OccurrenceTuple: Named tuple with (start, end, instance) for each
                          occurrence in the date range.

       Examples:
           >>> event = MyEvent.objects.create(title='Daily Meeting')
           >>> occ = MyOccurrence.objects.create(
           ...     event=event,
           ...     start=datetime(2024, 1, 1, 9, 0),
           ...     repeat='RRULE:FREQ=DAILY'
           ... )
           >>>
           >>> # Get all occurrences in January 2024
           >>> jan_occs = list(occ.all_occurrences(
           ...     from_date=date(2024, 1, 1),
           ...     to_date=date(2024, 1, 31)
           ... ))
           >>> len(jan_occs)
           31
           >>>
           >>> # Access occurrence data
           >>> first = jan_occs[0]
           >>> print(f"Start: {first.start}, End: {first.end}")
           Start: 2024-01-01 09:00:00, End: None

       Warning:
           For non-repeating occurrences that span multiple days, both
           from_date and to_date will match if they fall within the
           occurrence duration.

       Performance:
           - O(n) where n is the number of occurrences generated
           - For repeating events, each occurrence requires rrule calculation
           - Consider caching results for frequently accessed data
       """
   ```

2. **Document Performance Implications**
   - When to use `exact=True` vs approximate filtering
   - `sort_by_next()` returns list warning
   - REPEAT_MAX limits
   - Memory considerations for large querysets

3. **Create Usage Examples**
   - Basic event creation
   - Repeating events with various frequencies
   - Custom repeater patterns
   - Timezone handling
   - Bulk operations
   - Cancelling specific occurrences

4. **Create CHANGELOG.md**
   - Follow Keep a Changelog format
   - Document all changes from 1.0.3 to 2.0.0
   - Include migration guide

   ```markdown
   # Changelog

   All notable changes to django-eventtools will be documented in this file.

   The format is based on [Keep a Changelog](https://keepachangelog.com/),
   and this project adheres to [Semantic Versioning](https://semver.org/).

   ## [2.0.0] - 2025-XX-XX

   ### Breaking Changes
   - Dropped Python 2.7, 3.4, 3.5, 3.6, 3.7, 3.8 support
   - Dropped Django < 3.2 support
   - Removed `six` dependency

   ### Added
   - Type hints throughout entire codebase (PEP 484, 561)
   - `OccurrenceTuple` NamedTuple for occurrence data
   - Modern packaging with pyproject.toml
   - uv support for fast development
   - Comprehensive development documentation

   ### Changed
   - Minimum Python version is now 3.9
   - Minimum Django version is now 3.2 LTS
   - All occurrence tuples are now `OccurrenceTuple` named tuples

   ### Improved
   - Performance optimizations for large querysets
   - Better error messages in validation
   - Updated tooling (ruff, mypy, pytest)

   ## [1.0.3] - 2017-XX-XX
   ...
   ```

5. **Create CONTRIBUTING.md**
   - How to contribute
   - Code style guidelines
   - Testing requirements
   - Pull request process

6. **Create MIGRATION.md**
   - Guide for migrating from 1.x to 2.x
   - Breaking changes
   - Deprecation timeline
   - Code examples (before/after)

   ```markdown
   # Migration Guide: 1.x → 2.0

   ## Python and Django Requirements

   **Before:**
   - Python 2.7+ or 3.4+
   - Django 1.8+

   **After:**
   - Python 3.9+
   - Django 3.2+

   ## Tuple to NamedTuple

   **Before:**
   ```python
   occ = event.next_occurrence()
   start, end, instance = occ
   print(occ[0])  # start time
   ```

   **After:**
   ```python
   occ = event.next_occurrence()
   # Still works, but named access is better:
   print(occ.start)  # start time
   print(occ.end)    # end time
   print(occ.instance)  # occurrence instance
   ```

   ## Type Hints

   If your code uses django-eventtools and you use type checkers:

   **Install type stubs:**
   ```bash
   pip install django-stubs types-python-dateutil
   ```

   **Your code now gets type checking:**
   ```python
   from eventtools.models import OccurrenceTuple

   def process_occurrence(occ: OccurrenceTuple) -> None:
       # Type checker knows occ.start is datetime
       print(occ.start.year)
   ```
   ```

7. **Update README.md**
   - Add badges (tests, coverage, pypi version)
   - Update installation instructions
   - Add "What's New in 2.0" section
   - Update examples for new features
   - Document performance considerations

8. **Consider Sphinx Documentation** (Optional)
   - Full API documentation
   - Hosted on Read the Docs
   - Auto-generated from docstrings

#### Files to Create:
- CHANGELOG.md
- CONTRIBUTING.md
- MIGRATION.md
- docs/conf.py (if using Sphinx)
- docs/index.md
- docs/usage.md
- docs/api.md
- docs/performance.md

#### Files to Modify:
- README.md (major updates)
- All Python files (add docstrings)

---

### Phase 7: Optional Enhancements

**Priority:** Low
**Breaking Changes:** Varies
**Estimated Time:** 4-8 weeks

These are nice-to-have features that could be added in minor releases (2.1.0+):

#### 1. Async Support (2.1.0)
- Add async versions of key methods
- Requires Django 3.1+
- Use `a` prefix: `aall_occurrences()`, `anext_occurrence()`

```python
class OccurrenceMixin(object):
    async def aall_occurrences(
        self,
        from_date: date | datetime | None = None,
        to_date: date | datetime | None = None
    ) -> AsyncGenerator[OccurrenceTuple, None]:
        """Async generator version of all_occurrences."""
        # Implementation
        pass

    async def anext_occurrence(
        self,
        from_date: date | datetime | None = None,
        to_date: date | datetime | None = None
    ) -> OccurrenceTuple | None:
        """Async version of next_occurrence."""
        async for occ in self.aall_occurrences(from_date, to_date):
            return occ
        return None
```

#### 2. Bulk Operations (2.2.0)
- Create multiple occurrences efficiently
- Update repeating patterns in bulk

```python
class OccurrenceManager(models.Manager):
    def bulk_create_with_repeats(
        self,
        occurrences: list[dict],
        batch_size: int = 100
    ) -> list[BaseOccurrence]:
        """Create multiple occurrences efficiently."""
        pass
```

#### 3. Occurrence Caching Layer (2.3.0)
- Built-in caching for frequently accessed events
- Configurable cache backend
- Auto-invalidation on updates

```python
# In settings.py
EVENTTOOLS_CACHE = {
    'BACKEND': 'django.core.cache.backends.redis.RedisCache',
    'LOCATION': 'redis://127.0.0.1:6379/1',
    'TIMEOUT': 300,  # 5 minutes
}
```

#### 4. iCalendar Export (2.4.0)
- Export events to iCalendar format (RFC 5545)
- Import from .ics files

```python
class BaseEvent(BaseModel):
    def to_ical(self) -> str:
        """Export event and occurrences to iCalendar format."""
        pass

    @classmethod
    def from_ical(cls, ical_string: str) -> BaseEvent:
        """Import event from iCalendar format."""
        pass
```

#### 5. Built-in Occurrence Modifications (2.5.0)
- Make the example in README a first-class feature
- Built-in support for cancellations and modifications

```python
class OccurrenceException(models.Model):
    """Represents a modification or cancellation of a specific occurrence."""
    occurrence = models.ForeignKey(BaseOccurrence, on_delete=models.CASCADE)
    original_start = models.DateTimeField()
    modified_start = models.DateTimeField(null=True, blank=True)  # None = cancelled
    modified_end = models.DateTimeField(null=True, blank=True)
    reason = models.TextField(blank=True)
```

#### 6. Django Admin Improvements (2.6.0)
- Better admin forms for repeat rules
- Visual calendar preview
- Inline occurrence list with date range selector
- Custom admin widgets

```python
class RepeatRuleWidget(forms.Select):
    """Select widget with visual preview of repeat pattern."""
    template_name = 'eventtools/widgets/repeat_rule.html'

class OccurrenceInline(admin.TabularInline):
    """Inline showing generated occurrences."""
    model = BaseOccurrence
    extra = 0
    readonly_fields = ['preview_occurrences']

    def preview_occurrences(self, obj):
        """Show first 10 occurrences."""
        pass
```

#### 7. REST API Serializers (2.7.0)
- Django REST Framework integration
- Serializers for Event and Occurrence
- Custom fields for occurrence lists

```python
from rest_framework import serializers

class OccurrenceSerializer(serializers.ModelSerializer):
    generated_occurrences = OccurrenceListField(
        source='all_occurrences',
        from_date='2024-01-01',
        to_date='2024-12-31'
    )

    class Meta:
        model = BaseOccurrence
        fields = '__all__'
```

#### 8. GraphQL Support (2.8.0)
- Graphene-Django types
- Occurrence field resolvers
- Efficient batching

```python
import graphene
from graphene_django import DjangoObjectType

class OccurrenceType(DjangoObjectType):
    generated_occurrences = graphene.List(
        lambda: GeneratedOccurrenceType,
        from_date=graphene.Date(),
        to_date=graphene.Date()
    )

    class Meta:
        model = BaseOccurrence
```

---

## Testing Strategy

### Current Test Status
- **Total Tests:** 19
- **Passing:** 16
- **Failing:** 3 (timezone-related, pre-existing issues)

### Test Coverage Goals
- Minimum 90% code coverage
- 100% coverage for core functionality
- Edge case testing (timezones, DST boundaries)
- Performance regression tests

### Testing Tools
- pytest for test execution
- pytest-django for Django integration
- pytest-cov for coverage reporting
- pytest-benchmark for performance testing
- tox for multi-environment testing

---

## Breaking Changes Summary

### Version 2.0.0

**Python/Django Requirements:**
- ❌ Python 2.7, 3.4, 3.5, 3.6, 3.7, 3.8 no longer supported
- ✅ Python 3.9+ required
- ❌ Django < 3.2 no longer supported
- ✅ Django 3.2 LTS minimum

**Dependencies:**
- ❌ `six` removed
- ✅ Modern `python-dateutil>=2.8.2`

**API Changes:**
- ✅ Occurrence tuples are now `OccurrenceTuple` NamedTuple
  - Still compatible with tuple unpacking
  - Added named access: `.start`, `.end`, `.instance`
- ⚠️ Return types changed (shouldn't affect most usage)

**Deprecations (future 2.x versions):**
- `sort_by_next()` may be deprecated in favor of `order_by_next()`
- Plain tuple access discouraged (use named access)

---

## Migration Timeline

### Immediate (2.0.0)
- ✅ Drop legacy Python/Django support
- ✅ Add type hints
- ✅ Modern packaging with pyproject.toml

### Short-term (2.1.0 - 2.3.0)
- Performance optimizations
- API consistency improvements
- Documentation overhaul
- CI/CD modernization

### Medium-term (2.4.0 - 2.6.0)
- Optional enhancements
- Admin improvements
- Extended functionality

### Long-term (3.0.0)
- Possible breaking API changes
- Async-first design
- Major new features

---

## Development Commands

```bash
# Setup
uv venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
uv pip install -e ".[dev]"

# Testing
make test           # Run tests
make test-cov       # Run with coverage
pytest -v           # Run tests verbose
pytest -k test_name # Run specific test

# Code Quality
make lint           # Check code style
make lint-fix       # Auto-fix issues
make format         # Format code
make typecheck      # Type checking

# All Checks
make all            # Run lint, typecheck, test

# Cleanup
make clean          # Remove build artifacts
```

---

## Resources

### Documentation
- Python type hints: https://docs.python.org/3/library/typing.html
- Django documentation: https://docs.djangoproject.com/
- python-dateutil: https://dateutil.readthedocs.io/
- uv documentation: https://docs.astral.sh/uv/

### Tools
- uv: https://github.com/astral-sh/uv
- ruff: https://github.com/astral-sh/ruff
- mypy: https://mypy-lang.org/
- pytest: https://docs.pytest.org/

### Related Projects
- django-recurrence: https://github.com/django-recurrence/django-recurrence
- django-scheduler: https://github.com/llazzaro/django-scheduler

---

## Notes

### Design Decisions

1. **Why NamedTuple over dataclass?**
   - Lighter weight, immutable
   - Better for return values
   - Compatible with tuple unpacking (backward compatible)

2. **Why heapq.merge()?**
   - Stdlib, well-tested
   - Efficient for merging sorted iterables
   - Handles edge cases (empty generators, etc.)

3. **Why not async-first?**
   - Not all users are on Django 3.1+
   - Async can be added in minor version
   - Sync API is simpler for most use cases

4. **Why keep setup.py?**
   - Some tools still need it
   - Can coexist with pyproject.toml
   - May remove in 3.0.0

### Known Issues

1. **Timezone Tests Failing**
   - 3 tests fail with Django 5.2.8
   - Related to pytz vs zoneinfo changes
   - Need investigation and fixes

2. **Performance with Large Querysets**
   - `exact=True` is slow for 1000+ objects
   - Need better solution or clearer warnings

3. **API Inconsistency**
   - `sort_by_next()` returns list
   - Should be addressed in Phase 4

---

## Contact & Contribution

- **Original Author:** Greg Brown
- **Modernization:** [Your Name]
- **Repository:** https://github.com/gregplaysguitar/django-eventtools
- **Issues:** https://github.com/gregplaysguitar/django-eventtools/issues

Contributions welcome! See CONTRIBUTING.md for guidelines.
