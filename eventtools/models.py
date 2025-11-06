from __future__ import annotations

import heapq
import warnings
from collections.abc import Callable, Generator, Iterator
from datetime import date, datetime, timedelta
from typing import TYPE_CHECKING, NamedTuple

from dateutil import rrule
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Case, Q, Value, When
from django.utils.timezone import is_aware, is_naive, make_aware, make_naive
from django.utils.translation import gettext_lazy as _

if TYPE_CHECKING:
    from django.db.models import ManyToOneRel


# set EVENTTOOLS_REPEAT_CHOICES = None to make this a plain textfield
REPEAT_CHOICES = getattr(settings, 'EVENTTOOLS_REPEAT_CHOICES', (
    ("RRULE:FREQ=DAILY", 'Daily'),
    ("RRULE:FREQ=WEEKLY", 'Weekly'),
    ("RRULE:FREQ=MONTHLY", 'Monthly'),
    ("RRULE:FREQ=YEARLY", 'Yearly'),
))
# set EVENTTOOLS_REPEAT_MAX to override the default maximum number of occurrences
REPEAT_MAX = getattr(settings, 'EVENTTOOLS_REPEAT_MAX', 200)


class OccurrenceTuple(NamedTuple):
    """Type representing a single occurrence as (start, end, instance)."""
    start: datetime
    end: datetime | None
    instance: BaseOccurrence


def max_future_date() -> datetime:
    return datetime(date.today().year + 10, 1, 1, 0, 0)


def first_item(gen: Generator[OccurrenceTuple, None, None]) -> OccurrenceTuple | None:
    """Return the first item from a generator, or None if empty."""
    try:
        return next(gen)
    except StopIteration:
        return None


def default_aware(dt: datetime) -> datetime:
    """Convert a naive datetime argument to a tz-aware datetime, if tz support
       is enabled. """

    if settings.USE_TZ and is_naive(dt):
        return make_aware(dt)

    # if timezone support disabled, assume only naive datetimes are used
    return dt


def default_naive(dt: datetime) -> datetime:
    """Convert an aware datetime argument to naive, if tz support
       is enabled. """

    if settings.USE_TZ and is_aware(dt):
        return make_naive(dt)

    # if timezone support disabled, assume only naive datetimes are used
    return dt


def as_datetime(d: date | datetime, end: bool = False) -> datetime:
    """Normalise a date/datetime argument to a datetime for use in filters

    If a date is passed, it will be converted to a datetime with the time set
    to 0:00, or 23:59:59 if end is True."""

    if type(d) is date:
        date_args = tuple(d.timetuple())[:3]
        if end:
            time_args = (23, 59, 59)
        else:
            time_args = (0, 0, 0)
        new_value = datetime(*(date_args + time_args))
        return default_aware(new_value)
    # otherwise assume it's a datetime
    return default_aware(d)


def combine_occurrences(
    generators: Iterator[Generator[OccurrenceTuple, None, None]],
    limit: int | None
) -> Generator[OccurrenceTuple, None, None]:
    """Merge the occurrences in two or more generators, in date order.

    Uses heapq.merge for efficient merging of sorted generators.
    Returns a generator yielding OccurrenceTuple objects sorted by start datetime.

    Args:
        generators: Iterator of generators that yield OccurrenceTuple objects
        limit: Maximum number of occurrences to yield, or None for unlimited

    Yields:
        OccurrenceTuple: Occurrences in chronological order by start datetime
    """
    # Use heapq.merge with key function for start datetime
    # This is more efficient than manual merging (O(n log k) where k is number of generators)
    merged = heapq.merge(*generators, key=lambda occ: occ.start)

    if limit is None:
        yield from merged
    else:
        for i, occurrence in enumerate(merged):
            if i >= limit:
                return
            yield occurrence


def filter_invalid(
    approx_qs: BaseQuerySet,
    from_date: date | datetime | None,
    to_date: date | datetime | None,
    progress_callback: Callable[[int, int], None] | None = None
) -> BaseQuerySet:
    """Filter out any results from the queryset which do not have an occurrence
       within the given range.

    WARNING: This is an O(n) operation for large querysets as it must evaluate
    each object's occurrences individually. Use approximate filtering with
    for_period() when possible, and only use this when exact results are required.

    Args:
        approx_qs: Queryset to filter
        from_date: Start date for occurrence range
        to_date: End date for occurrence range
        progress_callback: Optional callback(current, total) for progress tracking

    Returns:
        Filtered queryset with invalid results excluded

    Performance:
        - Uses .iterator(chunk_size=100) for memory efficiency
        - Processes objects in batches to reduce memory usage
        - For large querysets (1000+ objects), consider caching or pre-filtering
    """
    # work out what to exclude based on occurrences
    # Use .iterator() with chunk_size for better memory efficiency
    total = approx_qs.count()
    exclude_pks = []

    for i, obj in enumerate(approx_qs.iterator(chunk_size=100), start=1):
        if progress_callback:
            progress_callback(i, total)
        if not obj.next_occurrence(from_date=from_date, to_date=to_date):
            exclude_pks.append(obj.pk)

    # and then apply the filtering to the queryset itself
    return approx_qs.exclude(pk__in=exclude_pks)


def filter_from(
    qs: BaseQuerySet,
    from_date: date | datetime,
    q_func: type[Q] = Q
) -> BaseQuerySet:
    """Filter a queryset by from_date. May still contain false positives due to
       uncertainty with repetitions. """

    from_date = as_datetime(from_date)
    return qs.filter(
        q_func(end__isnull=False, end__gte=from_date) |
        q_func(start__gte=from_date) |
        (~q_func(repeat='') & (q_func(repeat_until__gte=from_date) |
         q_func(repeat_until__isnull=True)))).distinct()


class OccurrenceMixin:
    """Class mixin providing common occurrence-related functionality. """

    def all_occurrences(
        self,
        from_date: date | datetime | None = None,
        to_date: date | datetime | None = None
    ) -> Generator[OccurrenceTuple, None, None]:
        raise NotImplementedError()

    def next_occurrence(
        self,
        from_date: date | datetime | None = None,
        to_date: date | datetime | None = None
    ) -> OccurrenceTuple | None:
        """Return next occurrence as a (start, end) tuple for this instance,
           between from_date and to_date, taking repetition into account. """
        if not from_date:
            from_date = datetime.now()
        return first_item(
            self.all_occurrences(from_date=from_date, to_date=to_date))

    def first_occurrence(self) -> OccurrenceTuple | None:
        """Return first occurrence as a (start, end) tuple for this instance.
        """
        return first_item(self.all_occurrences())


class BaseQuerySet(models.QuerySet, OccurrenceMixin):
    """Base QuerySet for models which have occurrences. """

    def for_period(
        self,
        from_date: date | datetime | None = None,
        to_date: date | datetime | None = None,
        exact: bool = False
    ) -> BaseQuerySet:
        # subclasses should implement this
        raise NotImplementedError()

    def sort_by_next(
        self,
        from_date: date | datetime | None = None
    ) -> list[BaseEvent | BaseOccurrence]:
        """Sort the queryset by next_occurrence.

        .. deprecated:: 2.0.0
            This method returns a list instead of a queryset, which breaks queryset
            chaining. While this method is not scheduled for removal, users should be
            aware that it does not return a queryset and cannot be chained with other
            queryset methods.

        Note:
            This method necessarily returns a list, not a queryset. For large querysets,
            this can be memory-intensive as all objects must be loaded and sorted in memory.

        Args:
            from_date: Optional start date for finding next occurrence

        Returns:
            list: Sorted list of objects by their next occurrence date. Objects without
                  a next occurrence are excluded.

        Warning:
            Performance degrades with large querysets as this is an O(n log n) operation
            that must evaluate each object's next occurrence.
        """
        warnings.warn(
            "sort_by_next() returns a list, not a queryset, which breaks queryset "
            "chaining. Consider converting to list explicitly: list(qs) if you need "
            "a list, or be aware this does not return a queryset.",
            PendingDeprecationWarning,
            stacklevel=2
        )

        def sort_key(obj: BaseEvent | BaseOccurrence) -> datetime | None:
            occ = obj.next_occurrence(from_date=from_date)
            return occ[0] if occ else None
        return sorted([e for e in self if sort_key(e)], key=sort_key)

    def all_occurrences(
        self,
        from_date: date | datetime | None = None,
        to_date: date | datetime | None = None,
        limit: int | None = None
    ) -> Generator[OccurrenceTuple, None, None]:
        """Return a generator yielding a (start, end) tuple for all occurrence
           dates in the queryset, taking repetition into account, up to a
           maximum limit if specified. """

        # winnow out events which are definitely invalid
        qs = self.for_period(from_date, to_date)

        return combine_occurrences(
            (obj.all_occurrences(from_date, to_date) for obj in qs), limit)


class BaseModel(models.Model, OccurrenceMixin):
    """Abstract model providing common occurrence-related functionality. """

    class Meta:
        abstract = True


class EventQuerySet(BaseQuerySet):
    """QuerySet for BaseEvent subclasses. """

    def for_period(
        self,
        from_date: date | datetime | None = None,
        to_date: date | datetime | None = None,
        exact: bool = False
    ) -> EventQuerySet:
        """Filter by the given dates, returning a queryset of Occurrence
           instances with occurrences falling within the range.

           Due to uncertainty with repetitions, from_date filtering is only an
           approximation. If exact results are needed, pass exact=True - this
           will use occurrences to exclude invalid results, but may be very
           slow, especially for large querysets. """

        filtered_qs: EventQuerySet = self
        prefix = self.model.occurrence_filter_prefix()

        def wrap_q(**kwargs: date | datetime) -> Q:
            """Prepend the related model name to the filter keys. """

            return Q(**{f'{prefix}__{k}': v for k, v in kwargs.items()})

        # to_date filtering is accurate
        if to_date:
            to_date = as_datetime(to_date, True)
            filtered_qs = filtered_qs.filter(
                wrap_q(start__lte=to_date)).distinct()

        if from_date:
            # but from_date isn't, due to uncertainty with repetitions, so
            # just winnow down as much as possible via queryset filtering
            filtered_qs = filter_from(filtered_qs, from_date, wrap_q)

            # filter out invalid results if requested
            if exact:
                filtered_qs = filter_invalid(filtered_qs, from_date, to_date)  # type: ignore[assignment]

        return filtered_qs


class EventManager(models.Manager.from_queryset(EventQuerySet)):
    use_for_related_fields = True


class BaseEvent(BaseModel):
    """Abstract model providing occurrence-related methods for events.

       Subclasses should have a related BaseOccurrence subclass. """

    objects = EventManager()

    @classmethod
    def get_occurrence_relation(cls) -> ManyToOneRel:
        """Get the occurrence relation for this class - use the first if
           there's more than one. """

        # get all related occurrence fields
        relations = [rel for rel in cls._meta.get_fields()
                     if isinstance(rel, models.ManyToOneRel) and
                     issubclass(rel.related_model, BaseOccurrence)]

        # assume there's only one
        return relations[0]  # type: ignore[return-value]

    @classmethod
    def occurrence_filter_prefix(cls) -> str:
        rel = cls.get_occurrence_relation()
        return rel.name

    def get_related_occurrences(self) -> OccurrenceQuerySet:
        """Get related occurrences with optimized query.

        Returns occurrences ordered by start date for efficient processing.
        For best performance, consider using select_related() or prefetch_related()
        on the event queryset before calling this method.

        Example:
            # Efficient: prefetch occurrences for multiple events
            events = MyEvent.objects.prefetch_related('occurrence_set')
            for event in events:
                occurrences = event.get_related_occurrences()

        Returns:
            OccurrenceQuerySet: Occurrences ordered by start date
        """
        rel = self.get_occurrence_relation()
        return getattr(self, rel.get_accessor_name()).all().order_by('start')

    def all_occurrences(
        self,
        from_date: date | datetime | None = None,
        to_date: date | datetime | None = None,
        limit: int | None = None
    ) -> Generator[OccurrenceTuple, None, None]:
        """Return a generator yielding a (start, end) tuple for all dates
           for this event, taking repetition into account. """

        return self.get_related_occurrences().all_occurrences(
            from_date, to_date, limit=limit)

    def __repr__(self) -> str:
        """Return detailed representation for debugging."""
        class_name = self.__class__.__name__
        pk_str = f"pk={self.pk}" if self.pk else "unsaved"
        # Try to include a title or string representation if available
        try:
            str_repr = str(self)[:50]  # Limit to 50 chars
            return f"<{class_name}({pk_str}, {str_repr!r})>"
        except Exception:
            return f"<{class_name}({pk_str})>"

    class Meta:
        abstract = True


class OccurrenceQuerySet(BaseQuerySet):
    """QuerySet for BaseOccurrence subclasses. """

    def for_period(
        self,
        from_date: date | datetime | None = None,
        to_date: date | datetime | None = None,
        exact: bool = False
    ) -> OccurrenceQuerySet:
        """Filter by the given dates, returning a queryset of Occurrence
           instances with occurrences falling within the range.

           Due to uncertainty with repetitions, from_date filtering is only an
           approximation. If exact results are needed, pass exact=True - this
           will use occurrences to exclude invalid results, but may be very
           slow, especially for large querysets. """

        filtered_qs: OccurrenceQuerySet = self

        # to_date filtering is accurate
        if to_date:
            to_date = as_datetime(to_date, True)
            filtered_qs = filtered_qs.filter(Q(start__lte=to_date)).distinct()

        if from_date:
            # but from_date isn't, due to uncertainty with repetitions, so
            # just winnow down as much as possible via queryset filtering
            filtered_qs = filter_from(filtered_qs, from_date)  # type: ignore[assignment]

            # filter out invalid results if requested
            if exact:
                filtered_qs = filter_invalid(filtered_qs, from_date, to_date)  # type: ignore[assignment]

        return filtered_qs


class OccurrenceManager(models.Manager.from_queryset(OccurrenceQuerySet)):
    use_for_related_fields = True

    def migrate_integer_repeat(self) -> int:
        """Migrate old integer-based repeat values to rrule strings."""
        return self.update(repeat=Case(
            When(repeat=rrule.YEARLY,
                 then=Value("RRULE:FREQ=YEARLY")),
            When(repeat=rrule.MONTHLY,
                 then=Value("RRULE:FREQ=MONTHLY")),
            When(repeat=rrule.WEEKLY,
                 then=Value("RRULE:FREQ=WEEKLY")),
            When(repeat=rrule.DAILY,
                 then=Value("RRULE:FREQ=DAILY")),
            default=Value(""),
        ))


class ChoiceTextField(models.TextField):
    """Textfield which uses a Select widget if it has choices specified. """

    def formfield(self, **kwargs):  # type: ignore[no-untyped-def]
        if self.choices:
            # this overrides the TextField's preference for a Textarea widget,
            # allowing the ModelForm to decide which field to use
            kwargs['widget'] = None
        return super().formfield(**kwargs)


class BaseOccurrence(BaseModel):
    """Abstract model providing occurrence-related methods for occurrences.

       Subclasses will usually have a ForeignKey pointing to a BaseEvent
       subclass. """

    start = models.DateTimeField(db_index=True, verbose_name=_('start'))
    end = models.DateTimeField(
        db_index=True, null=True, blank=True, verbose_name=_('end'))

    repeat = ChoiceTextField(
        choices=REPEAT_CHOICES, default='', blank=True,
        verbose_name=_('repeat'))
    repeat_until = models.DateField(
        null=True, blank=True, verbose_name=_('repeat_until'))

    def clean(self) -> None:
        """Validate occurrence data with helpful error messages."""
        if self.start and self.end and self.start >= self.end:
            raise ValidationError(
                f"End time must be after start time. "
                f"Got start={self.start}, end={self.end}. "
                f"Did you accidentally swap them?"
            )

        if self.repeat_until and not self.repeat:
            raise ValidationError(
                "A 'repeat until' date was specified without a repeat pattern. "
                "Please either:\n"
                "  1. Select a repeat interval (Daily, Weekly, Monthly, or Yearly), OR\n"
                "  2. Remove the 'repeat until' date if this is a one-time occurrence."
            )

        if self.start and self.repeat_until and \
           self.repeat_until < self.start.date():
            raise ValidationError(
                f"'Repeat until' date ({self.repeat_until}) cannot be before "
                f"the first occurrence ({self.start.date()}). "
                f"The repeat pattern would have no occurrences. "
                f"Please set 'repeat until' to a date on or after {self.start.date()}."
            )

    objects = OccurrenceManager()

    def all_occurrences(
        self,
        from_date: date | datetime | None = None,
        to_date: date | datetime | None = None,
        limit: int = REPEAT_MAX
    ) -> Generator[OccurrenceTuple, None, None]:
        """Return a generator yielding a (start, end) tuple for all dates
           for this occurrence, taking repetition into account.

        Args:
            from_date: Start of date range (inclusive)
            to_date: End of date range (inclusive)
            limit: Maximum number of occurrences to generate. Defaults to REPEAT_MAX
                   which can be configured via EVENTTOOLS_REPEAT_MAX setting (default: 200).
                   Set to a higher value if you need more occurrences, or pass explicitly
                   per query for fine-grained control.

        Yields:
            OccurrenceTuple: Named tuple with (start, end, instance) for each occurrence
        """

        if not self.start:
            return

        from_date = from_date and as_datetime(from_date)
        to_date = to_date and as_datetime(to_date, True)

        if not self.repeat:
            if (not from_date or self.start >= from_date or
                (self.end and self.end >= from_date)) and \
               (not to_date or self.start <= to_date):
                yield OccurrenceTuple(self.start, self.end, self.occurrence_data)
        else:
            delta = (self.end - self.start) if self.end else timedelta(0)
            repeater = self.get_repeater()

            # start from the first occurrence at the earliest
            if not from_date or from_date < self.start:
                from_date = self.start

            # look until the last occurrence, up to an arbitrary maximum date
            if self.repeat_until and (
                    not to_date or
                    as_datetime(self.repeat_until, True) < to_date):
                to_date = as_datetime(self.repeat_until, True)
            elif not to_date:
                to_date = default_aware(max_future_date())

            # start is used for the filter, so modify from_date to take the
            # occurrence length into account
            from_date -= delta

            # always send naive datetimes to the repeater
            repeater = repeater.between(default_naive(from_date),
                                        default_naive(to_date), inc=True)

            count = 0
            for occ_start in repeater:
                count += 1
                if count > limit:
                    return

                # make naive results aware
                occ_start = default_aware(occ_start)
                yield OccurrenceTuple(occ_start, occ_start + delta, self.occurrence_data)

    def get_repeater(self) -> rrule.rruleset:
        """Get rruleset instance representing this occurrence's repetitions.

        Subclasses may override this method for custom repeat behaviour.
        """

        ruleset = rrule.rruleset()
        rule = rrule.rrulestr(self.repeat, dtstart=default_naive(self.start))
        ruleset.rrule(rule)
        return ruleset

    @property
    def occurrence_data(self) -> BaseOccurrence:
        """Return data for this occurrence.

        This property is used internally when generating occurrence tuples. By default,
        it returns self, but subclasses can override to return modified data or a
        related object.

        Common use cases for overriding:
            - Pre-load or cache related event data
            - Return a custom data object with computed properties
            - Transform or enrich occurrence data for API responses

        Returns:
            BaseOccurrence: The occurrence data (self by default)

        Examples:
            Override to cache related event data::

                class MyOccurrence(BaseOccurrence):
                    @property
                    def occurrence_data(self):
                        # Cache event data to avoid repeated queries
                        if not hasattr(self, '_cached_event'):
                            self._cached_event = self.event
                        return self

            Override to return enriched data::

                class MyOccurrence(BaseOccurrence):
                    @property
                    def occurrence_data(self):
                        # Add computed properties
                        self._duration = (self.end - self.start) if self.end else None
                        return self
        """
        return self

    class Meta:
        ordering = ('start', 'end')
        abstract = True
        indexes = [
            models.Index(fields=['start', 'end'], name='%(app_label)s_%(class)s_start_end_idx'),
            models.Index(fields=['repeat_until'], name='%(app_label)s_%(class)s_repeat_until_idx'),
        ]

    def __str__(self) -> str:
        return f"{self.start}"

    def __repr__(self) -> str:
        """Return detailed representation for debugging."""
        class_name = self.__class__.__name__
        pk_str = f"pk={self.pk}" if self.pk else "unsaved"
        start_str = f"start={self.start!r}"
        end_str = f"end={self.end!r}" if self.end else "end=None"
        repeat_str = f"repeat={self.repeat!r}" if self.repeat else "repeat=''"
        return f"<{class_name}({pk_str}, {start_str}, {end_str}, {repeat_str})>"
